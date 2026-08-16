from asyncio import base_futures
import os
import sys
import time
from datetime import datetime, timezone

import logging
from pathlib import Path
from shutil import copyfile, copytree
from collections import OrderedDict
import math

from jinja2 import Environment, FileSystemLoader, select_autoescape

from aqui_brain_dump import bibliography, content_path, datetimeformat, output_path, static_path, static_url
from aqui_brain_dump.note import Note
from aqui_brain_dump.util import is_private_path


logger = logging.getLogger(__name__)


class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()
        if hasattr(self.stream, 'flush'):
            self.stream.flush()


def setup_logging():
    root_logger = logging.getLogger()
    if not any(isinstance(h, FlushStreamHandler) for h in root_logger.handlers):
        # Remove any default handlers to avoid duplicate output or unbuffered conflicts
        for h in list(root_logger.handlers):
            root_logger.removeHandler(h)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        root_logger.setLevel(logging.DEBUG)

        ch = FlushStreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)

        fh = logging.FileHandler('logger.log', mode='w')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)

        root_logger.addHandler(ch)
        root_logger.addHandler(fh)


def main(base_url='https://notes.aquiles.me', parse_git=True):
    setup_logging()
    start_time = time.time()
    logger.info('Starting to compile the notes')
    logger.info(f'Got base_url={base_url}')
    logger.info(f'Got parse_git={parse_git}')
    if len(sys.argv) > 1:
        logger.info(f'Setting base url to {sys.argv[1]}')
        base_url = sys.argv[1]

    parse_git = parse_git
    if len(sys.argv) > 2:
        logger.info('Setting parse git to False')
        parse_git = False

    out_static_dir = output_path / static_url
    logger.info(f'Copying static directory to {out_static_dir}...')
    t0 = time.time()
    if out_static_dir.exists():
        import shutil
        shutil.rmtree(out_static_dir)
    copytree(str(static_path.absolute()), str(out_static_dir.absolute()))
    logger.info(f'Copied static directory in {time.time() - t0:.2f}s')

    Note.notes = {}
    Note.futures_executor = []
    Note.bibliography = bibliography

    if parse_git:
        logger.info(f'Preloading git information from {content_path.parent}...')
        t0 = time.time()
        Note.preload_git_info(content_path.parent)
        logger.info(f'Preloaded git info for {len(Note.git_info_cache)} files in {time.time() - t0:.2f}s')

    logger.info(f'Scanning content directory: {content_path}...')
    t0 = time.time()
    md_files = []
    non_md_count = 0
    f_walk = list(os.walk(content_path))
    for root, dirs, files in f_walk:
        dirs[:] = [d for d in dirs if d != '_private' and d != 'templates' and not d.startswith('.')]
        if is_private_path(root):
            continue
        cur_dir = root
        sub_dir = Path(os.path.abspath(cur_dir))
        if sub_dir == content_path:
            out_subdir = output_path
        else:
            out_subdir = output_path / sub_dir.relative_to(content_path)
        out_subdir.mkdir(exist_ok=True, parents=True)
        for file in files:
            filepath = sub_dir / file
            if is_private_path(filepath):
                continue
            if not file.endswith('.md'):
                logger.debug(f'Copying {file} to {out_subdir / file}')
                copyfile(os.path.join(cur_dir, file), out_subdir / file)
                non_md_count += 1
                continue
            md_files.append(filepath)

    if non_md_count > 0:
        logger.info(f'Copied {non_md_count} non-markdown asset files.')

    md_files = sorted(md_files)
    total_md = len(md_files)
    logger.info(f'Found {total_md} markdown notes. Parsing notes...')
    parse_start = time.time()
    last_log_time = parse_start

    for idx, filepath in enumerate(md_files, 1):
        now = time.time()
        if idx == 1 or idx == total_md or (now - last_log_time) >= 2.0:
            last_log_time = now
            pct = (idx / total_md) * 100
            logger.info(f'Parsing notes: [{idx}/{total_md}] ({pct:.0f}%) - {filepath.name}')
        logger.debug(f'Creating note for {filepath}')
        Note.create_from_path(filepath, parse_git=parse_git)
    
    logger.info(f'Parsed and queued {total_md} notes in {time.time() - parse_start:.2f}s')

    logger.info('Waiting for background note parser tasks to complete...')
    wait_start = time.time()
    while len([f for f in Note.futures_executor if f.running()]):
        time.sleep(.01)
    logger.info(f'Background note parser tasks completed in {time.time() - wait_start:.2f}s')

    logger.info(f'Creating Tag pages for {len(Note.tags_dict)} unique tags...')
    for tag, backlinks in Note.tags_dict.items():
        t = tag.strip('#')
        tag_page = Note.create_from_url(f'/tags/{t}')
        tag_page.backlinks = backlinks

    logger.info(f'Creating Literature note pages for {len(Note.lit_notes)} citations...')
    for cite, backlinks in Note.lit_notes.items():
        cite_page = Note.create_from_lit(cite)
        cite_page.backlinks = backlinks

    logger.info('Building backlinks across all notes...')
    t0 = time.time()
    Note.build_backlinks()
    logger.info(f'Backlinks structure built in {time.time() - t0:.2f}s')

    logger.info('Waiting for backlinks executor to finish...')
    t0 = time.time()
    while len([f for f in Note.futures_executor if f.running()]):
        time.sleep(.01)
    Note.note_executor.shutdown(wait=True)
    logger.info(f'Backlinks executor finished in {time.time() - t0:.2f}s')

    total_notes = len(Note.notes)
    logger.info(f'Rendering {total_notes} notes to HTML...')
    t0 = time.time()
    last_render_log = t0
    from concurrent.futures import ThreadPoolExecutor, as_completed
    rendered_count = 0
    with ThreadPoolExecutor(max_workers=10) as render_executor:
        render_futures = [render_executor.submit(note.render, base_url=base_url) for note in Note.notes.values()]
        for f in as_completed(render_futures):
            f.result()
            rendered_count += 1
            now = time.time()
            if rendered_count == 1 or rendered_count == total_notes or (now - last_render_log) >= 2.0:
                last_render_log = now
                pct = (rendered_count / total_notes) * 100
                logger.info(f'Rendering HTML: [{rendered_count}/{total_notes}] ({pct:.0f}%)')

    logger.info(f'Finished rendering {total_notes} notes in {time.time() - t0:.2f}s')

    logger.info('Building sitemap...')

    num_edits = [n.number_edits for n in Note.notes.values()]
    min_number_edits = min(num_edits)
    max_number_edits = max(num_edits)

    logger.debug(f'Min num edits: {min_number_edits}, Max num edits: {max_number_edits}')
    today = datetime.now(tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')
    env = Environment(
        loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))),
        autoescape=select_autoescape(['xml', 'html', 'rss']),
    )
    env.filters['datetime'] = datetimeformat
    sitemap = env.get_template('sitemap.xml')
    # Compute network-based priorities using incoming (backlinks) and outgoing (links)
    # Use log1p to dampen large degrees; weight incoming higher than outgoing
    network_scores = {}
    for url, n in Note.notes.items():
        in_deg = len(getattr(n, 'backlinks', []) or [])
        out_deg = len(getattr(n, 'links', []) or [])
        score = 2.0 * math.log1p(in_deg) + 1.0 * math.log1p(out_deg)
        network_scores[url] = score
    max_network_score = max(network_scores.values()) if network_scores else 0.0
    network_priorities = {}
    for url, s in network_scores.items():
        if max_network_score > 0:
            pr = s / max_network_score
            pr = pr if pr >= 0.1 else 0.1
        else:
            pr = 0.1
        network_priorities[url] = round(pr, 3)
    xml_base_url = 'https://notes.aquiles.me' if base_url in ('.', '', 'relative') or (isinstance(base_url, str) and base_url.startswith('.')) else base_url
    with open(output_path / 'sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap.render(
            {'notes': Note.notes,
             'min_edits': min_number_edits,
             'max_edits': max_number_edits,
             'network_priorities': network_priorities,
             'today': today,
             'base_url': xml_base_url,
                }))

    logger.info('Building RSS Feed')
    rss_feed = env.get_template('feed.rss')
    # Filter notes modified/created in the last week
    def _note_last_mod_timestamp(item):
        # item is (key, note)
        _, n = item
        import datetime as dt
        value = getattr(n, 'last_mod', None) or getattr(n, 'creation_date', None)
        if isinstance(value, dt.datetime):
            vdt = value
        elif isinstance(value, dt.date):
            vdt = dt.datetime.combine(value, dt.time.min, tzinfo=dt.timezone.utc)
        else:
            return 0
        try:
            return vdt.timestamp()
        except Exception:
            return 0

    # Filter notes to only include those with content (actual notes, not auto-generated pages)
    # and modified/created in the last 7 days
    import datetime as dt
    one_week_ago = dt.datetime.now(tz=dt.timezone.utc) - dt.timedelta(days=7)
    
    filtered_items = []
    for key, note in Note.notes.items():
        # Skip notes without content (auto-generated tag pages, etc.)
        if note.content is None or note.content == '':
            continue
        
        # Get the last modification or creation date
        value = getattr(note, 'last_mod', None) or getattr(note, 'creation_date', None)
        if isinstance(value, dt.datetime):
            note_date = value
            # Make timezone-aware if it's naive
            if note_date.tzinfo is None:
                note_date = note_date.replace(tzinfo=dt.timezone.utc)
        elif isinstance(value, dt.date):
            note_date = dt.datetime.combine(value, dt.time.min, tzinfo=dt.timezone.utc)
        else:
            continue
        
        # Include if modified/created in the last week
        if note_date >= one_week_ago:
            filtered_items.append((key, note))
    
    # Sort by most recent first
    sorted_items = sorted(filtered_items, key=_note_last_mod_timestamp, reverse=True)
    limited_notes = OrderedDict(sorted_items)
    
    logger.info(f'Found {len(limited_notes)} notes modified/created in the last week for RSS feed')
    with open(output_path / 'feed.rss', 'w', encoding='utf-8') as f:
        f.write(rss_feed.render(
            {'notes': limited_notes,
             'min_edits': min_number_edits,
             'max_edits': max_number_edits,
             'today': today,
             'base_url': xml_base_url
             }))

    logger.info('Copying stats files to output directory')
    import shutil
    out_stats_dir = output_path / 'stats'
    out_stats_dir.mkdir(parents=True, exist_ok=True)
    stats_dir = Path('stats')
    if stats_dir.exists():
        for f in ['garden_stats.json', 'garden_graph.json']:
            src = stats_dir / f
            if src.exists():
                logger.debug(f'Copying {src} to {out_stats_dir / f}')
                shutil.copyfile(src, out_stats_dir / f)

    elapsed = time.time() - start_time
    logger.info(f'Site build completed successfully in {elapsed:.2f} seconds!')


if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    class FlushStreamHandler(logging.StreamHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()

    log = logging.getLogger()
    log.setLevel(logging.INFO)
    ch = FlushStreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    fh = logging.FileHandler('logger.log', mode='w')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    log.addHandler(ch)
    log.addHandler(fh)

    main(parse_git=False)