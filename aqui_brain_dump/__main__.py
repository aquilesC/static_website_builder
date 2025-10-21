import os
import sys
import time
from datetime import datetime, timezone
import logging
from pathlib import Path
from shutil import copyfile, copytree
from collections import OrderedDict
import math

from jinja2 import Environment, FileSystemLoader

from aqui_brain_dump import bibliography, content_path, datetimeformat, output_path, static_path, static_url
from aqui_brain_dump.note import Note


logger = logging.getLogger(__name__)


def main(base_url='https://notes.aquiles.me', parse_git=True):
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
    if out_static_dir.exists():
        import shutil
        shutil.rmtree(out_static_dir)
    copytree(str(static_path.absolute()), str(out_static_dir.absolute()))

    Note.bibliography = bibliography

    f_walk = os.walk(content_path)
    for dirs in f_walk:
        if 'templates' in dirs[0]:
            continue
        if 'templates' in dirs[0]:
            continue
        logger.info(f'Entering to {dirs[0]}')
        cur_dir = dirs[0]
        sub_dir = os.path.abspath(cur_dir)
        if sub_dir == '.':
            sub_dir = ''

        if sub_dir.startswith('.') or sub_dir.startswith('templates'):
            continue

        sub_dir = Path(sub_dir).absolute()
        out_subdir = output_path / sub_dir.relative_to(content_path)
        out_subdir.mkdir(exist_ok=True, parents=True)
        for file in dirs[2]:
            if not file.endswith('.md'):
                logger.debug(f'Copying {file} to {output_path / sub_dir.relative_to(content_path) / file}')
                copyfile(os.path.join(cur_dir, file), output_path / sub_dir.relative_to(content_path) / file)
                continue
            filepath = content_path / sub_dir / file
            logger.debug(f'Creating note for {filepath}')
            Note.create_from_path(filepath, parse_git=parse_git)

    logger.info('Waiting for note parser executor to finish')
    while len([f for f in Note.futures_executor if f.running()]):
        time.sleep(.01)

    logger.info('Creating Tags')
    for tag, backlinks in Note.tags_dict.items():
        t = tag.strip('#')
        tag_page = Note.create_from_url(f'/tags/{t}')
        tag_page.backlinks = backlinks

    for cite, backlinks in Note.lit_notes.items():
        cite_page = Note.create_from_lit(cite)
        cite_page.backlinks = backlinks

    logger.info('Building backlinks')
    Note.build_backlinks()
    logger.info('Waiting for backlinks executor to finish')

    while len([f for f in Note.futures_executor if f.running()]):
        time.sleep(.01)
    Note.note_executor.shutdown(wait=True)

    logger.info('Rendering notes')
    for rel_path, note in Note.notes.items():
        logger.debug(f'Rendering {note}')
        note.render(base_url=base_url)

    logger.info('Finished building notes')

    logger.info('Building sitemap')

    num_edits = [n.number_edits for n in Note.notes.values()]
    min_number_edits = min(num_edits)
    max_number_edits = max(num_edits)

    logger.debug(f'Min num edits: {min_number_edits}, Max num edits: {max_number_edits}')
    today = datetime.now(tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')
    env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
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
    with open(output_path / 'sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap.render(
            {'notes': Note.notes,
             'min_edits': min_number_edits,
             'max_edits': max_number_edits,
             'network_priorities': network_priorities,
             'today': today,
             'base_url': base_url,
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
             'base_url': base_url
             }))


if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    fh = logging.FileHandler('logger.log', mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(ch)
    log.addHandler(fh)

    main(parse_git=False)