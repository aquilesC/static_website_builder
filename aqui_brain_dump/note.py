import datetime
import logging
import time
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
import json
import re

import frontmatter
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape

from aqui_brain_dump import content_path, get_creation_date, get_last_modification_date, get_number_commits, \
    get_md, md, \
    output_path, static_url, template_path
from aqui_brain_dump import datetimeformat
from aqui_brain_dump.util import path_to_url, has_invalid_filename_chars, is_private_path

env = Environment(
    loader=FileSystemLoader(template_path),
    autoescape=select_autoescape(['html', 'xml', 'htm']),
    cache_size=400,
)
env.filters['datetime'] = datetimeformat
try:
    template_article = env.get_template('note.html')
    template_index = env.get_template('index.html')
except Exception:
    template_article = None
    template_index = None



logger = logging.getLogger(__name__)

LIST_ITEM_RE = re.compile(r'^\s*([-*]|\d+[\.\)])\s+')


def fix_markdown_lists(text):
    if not text:
        return text
    lines = text.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        if i > 0:
            prev = lines[i - 1].strip()
            if LIST_ITEM_RE.match(line) and prev and not LIST_ITEM_RE.match(lines[i - 1]) and not prev.startswith('#') and not prev.startswith('>'):
                new_lines.append('')
        new_lines.append(line)
    return '\n'.join(new_lines)



class Note:
    notes = {}
    note_executor = ThreadPoolExecutor(max_workers=10)
    futures_executor = []
    tags_dict = {}
    lit_notes = {}
    bibliography = {}
    git_info_cache = {}

    @classmethod
    def preload_git_info(cls, repo_path):
        from aqui_brain_dump.git_process import get_all_git_info
        cls.git_info_cache = get_all_git_info(repo_path)

    def __init__(self, file_path, parse_git = True):
        self.file_path = Path(file_path).absolute()
        self.path = self.file_path.relative_to(content_path.absolute())
        self.parse_git = parse_git
        self.content = None
        self.backlinks = set()
        self.links = set()
        self.cites = set()
        self.title = ''
        self.meta = {}
        self.tags = set()
        self.url = ''
        self.last_mod = datetime.datetime.now()
        self.number_edits = 1
        self.creation_date = datetime.datetime.now()

    def _generate_connections_data(self):
        """Generate connections data for this note including incoming and outgoing links"""
        connections = {
            'note': {
                'url': self.url,
                'title': self.title,
            },
            'incoming': [],
            'outgoing': []
        }
        
        # Process incoming links (backlinks)
        for backlink in self.backlinks:
            link_data = {
                'url': backlink.url,
                'title': backlink.title,
                'exists': backlink.content is not None,
                'is_tag': backlink.url.startswith('/tags/'),
                'is_external': False
            }
            connections['incoming'].append(link_data)
        
        # Process outgoing links
        for link in self.links:
            linked_note = self.notes.get(link)
            if linked_note:
                link_data = {
                    'url': linked_note.url,
                    'title': linked_note.title,
                    'exists': linked_note.content is not None,
                    'is_tag': linked_note.url.startswith('/tags/'),
                    'is_external': False
                }
            else:
                # External or non-existent link
                is_external = link.startswith('http://') or link.startswith('https://')
                link_data = {
                    'url': link,
                    'title': link,
                    'exists': False,
                    'is_tag': False,
                    'is_external': is_external
                }
            connections['outgoing'].append(link_data)
        
        return connections



    @classmethod
    def create_from_path(cls, file_path, parse_git=False):
        if is_private_path(file_path):
            logger.debug(f'Skipping private file: {file_path}')
            return None
        logger.debug(f'Creating note from file: {file_path}')
        rel_path = Path(file_path).absolute().relative_to(content_path.absolute())
        note = cls.notes.get(path_to_url(rel_path), False)
        if note:
            return note
        note = cls(file_path, parse_git=parse_git)
        note.parse_file()
        return note

    @classmethod
    def create_from_url(cls, url: str):
        """ Creates a note without content, normally product of links to non existing notes
        """
        if is_private_path(url):
            logger.debug(f'Skipping creation of note for private url: {url}')
            return None
        if not all(ord(c) < 128 for c in url):
            logger.warning(f'{url} has non-ascii characters')

        logger.debug(f'Creating note from url {url}')
        if url.startswith('/'):
            url = url[1:]
        logger.debug(f'New Url: {url}')
        file_path = content_path / (url + '.md')
        note = cls(file_path)
        note.title = url.replace('_', ' ').capitalize()
        note.url = '/' + url.replace(' ', '_').lower()
        note.meta['epistemic'] = 'This note is auto generated'
        note.notes[note.url] = note
        logger.debug(f'Added {note} to notes with url {url}')
        return note

    def parse_file(self):
        logger.debug(f'Parsing contents of {self}')
        if not Path(self.file_path).is_file():
            logger.debug(f'{self.file_path} does not exist, creating empty note')
            self.title = ' '.join(str(self.path).split('_')).strip('/')
            if self.title.endswith('.md'):
                self.title = self.title[:-3]
            self.url = path_to_url(self.path)
            if not all(ord(c) < 128 for c in self.url):
                logger.warning(f'{self.url} has non-ascii characters')
            # Check for invalid filename characters in the note path
            has_invalid, chars = has_invalid_filename_chars(str(self.path))
            if has_invalid:
                logger.warning(f'Invalid filename characters {chars} in note path: {self.path}')
            self.notes[str(self.file_path.absolute()).lower()] = self
            return

        with open(self.file_path, 'r', encoding='utf-8') as f:
            local_md = get_md(self.bibliography)
            local_md.reset()
            local_md.links = set()

            post = None
            try:
                post = frontmatter.load(f)
                content_text = fix_markdown_lists(post.content)
                self.content = local_md.convert(content_text)
            except Exception as e:
                logger.error(f'Error parsing {self.file_path}: {e}')
                self.content = ''

            logger.debug(f'Converted {self.file_path}')
            bs = BeautifulSoup(self.content, 'html.parser')
            h1 = bs.find('h1')
            h1_title = None
            if h1 is not None and h1.get_text() != '':
                logger.debug(f'Found title: {h1.get_text()}')
                h1_title = h1.get_text()
                h1.decompose()
                self.content = str(bs)
            if post is not None and 'title' in post.metadata:
                self.title = post.metadata['title']
            elif h1_title is not None:
                self.title = h1_title
            else:
                self.title = ' '.join(str(self.path).split('_')).strip('/').capitalize()
                if self.title.endswith('.md'):
                    self.title = self.title[:-3]

            self.url = path_to_url(self.path)
            if post is not None and 'slug' in post.metadata:
                self.url = post.metadata.get('slug')
            self.meta = post.metadata if post is not None else {}
            self.links = getattr(local_md, 'links', set())
            logger.debug(f'{self.title} links: {self.links}')
            self.tags = getattr(local_md, 'tags', set())
            self.cites = getattr(local_md, 'cites', set())
            for tag in self.tags:
                tag = tag.lower()
                # Check for invalid filename characters in tag
                has_invalid, chars = has_invalid_filename_chars(tag)
                if has_invalid:
                    logger.warning(f'Invalid filename characters {chars} in tag: {tag} (file: {self.file_path})')
                if tag not in self.tags_dict:
                    self.tags_dict[tag] =[self, ]
                else:
                    self.tags_dict[tag].append(self)

            for cite in self.cites:
                if cite not in self.lit_notes:
                    self.lit_notes[cite] = [self, ]
                else:
                    self.lit_notes[cite].append(self)

            self.futures_executor.append(self.note_executor.submit(self.update_git_information))

        logger.debug(f'Added {self} with url {self.url}')
        self.notes[self.url] = self
        self.notes[str(self.file_path.absolute()).lower()] = self

    def update_git_information(self):
        if self.parse_git:
            abs_path = self.file_path.absolute()
            if self.git_info_cache:
                info = self.git_info_cache.get(abs_path)
                if info:
                    self.last_mod = info['last_mod']
                    self.creation_date = info['creation_date']
                    self.number_edits = info['number_edits']
                else:
                    self.last_mod = datetime.date.today()
                    self.creation_date = datetime.date.today()
                    self.number_edits = 1
            else:
                self.last_mod = get_last_modification_date(self.file_path)
                self.creation_date = get_creation_date(self.file_path)
                self.number_edits = get_number_commits(self.file_path)
        else:
            self.last_mod = datetime.date.today()
            self.creation_date = datetime.date.today()
            self.number_edits = 1

    def render(self, base_url):
        logger.debug(f'Preparing to render {self}')
        effective_base_url = base_url
        if base_url in ('.', '', 'relative') or (isinstance(base_url, str) and base_url.startswith('.')):
            clean_url = self.url.strip('/')
            if not clean_url:
                effective_base_url = '.'
            else:
                depth = len(clean_url.split('/'))
                effective_base_url = '/'.join(['..'] * depth)

        context = {
            'note': self,
            'static': static_url,
            'base_url': effective_base_url,
            }
        out_path = output_path / self.url[1:]
        # Check for invalid filename characters in the output path
        # has_invalid, chars = has_invalid_filename_chars(str(out_path))
        # if has_invalid:
        #     logger.warning(f'Invalid filename characters {chars} in output path: {out_path} (source: {self.file_path})')
        try:
            out_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f'Error creating output path {out_path}: {e}')
            return

        template_name = self.meta.get('template', 'note.html')
        try:
            template = env.get_template(template_name)
        except Exception as e:
            logger.error(f'Error loading template {template_name}: {e}')
            return

        html = template.render(context)
        
        # Write the HTML file
        with open(out_path / 'index.html', 'w', encoding='utf-8') as out:
            logger.debug(f'Writing {template} with {self} information, to {out_path}')
            out.write(html)
        
        # Generate and write connections JSON file
        connections_data = self._generate_connections_data()
        with open(out_path / 'connections.json', 'w', encoding='utf-8') as json_file:
            json.dump(connections_data, json_file, indent=2, ensure_ascii=False)
            logger.debug(f'Writing connections.json for {self} to {out_path}')

    @classmethod
    def build_backlinks(cls):
        for note in list(cls.notes.values()):
            if is_private_path(getattr(note, 'file_path', None)) or is_private_path(getattr(note, 'path', None)):
                continue
            for link in note.links:
                if is_private_path(link):
                    continue
                logger.debug(f'{note.url} links to {link}')
                link_to = cls.notes.get(link, False)
                if link_to:
                    if not (is_private_path(getattr(link_to, 'file_path', None)) or is_private_path(getattr(link_to, 'path', None))):
                        link_to.backlinks.add(note)
                        logger.debug(f'Adding {note} to backlinks of {link_to}')
                else:
                    new_note = Note.create_from_url(link)
                    if new_note:
                        while len([f for f in Note.futures_executor if f.running()]):
                            time.sleep(.01)
                        new_note.backlinks.add(note)
                        logger.debug(f'Creating {new_note} and appending {note} to its backlinks')


    @classmethod
    def create_from_lit(cls, cite_key):
        logger.debug(f'Building note from lit cite {cite_key}')
        if cite_key not in cls.bibliography:
            logger.warning(f'{cite_key} not in bibliography')
        # Check for invalid filename characters in citation key
        has_invalid, chars = has_invalid_filename_chars(cite_key)
        if has_invalid:
            logger.warning(f'Invalid filename characters {chars} in citation key: {cite_key}')
        file_path = content_path / (cite_key + '.md')
        note = cls(file_path)
        biblio = note.bibliography.get(cite_key, None)
        if biblio:
            note.title = cls.bibliography[cite_key]['title']
        else:
            note.title = cite_key
        note.meta['template'] = "lit_note.html"
        note.url = f"/lit_note/@{cite_key}/"
        note.notes[note.url] = note
        note.content = biblio
        logger.debug(f'Added {note} to notes with url {note.url}')
        return note

    def __str__(self):
        return self.title or str(self.path)

    def __repr__(self):
        return f'<Note {self.file_path or self.path}>'