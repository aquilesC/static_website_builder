import codecs
import logging
import time
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path

import frontmatter
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from aqui_brain_dump import base_url, content_path, get_creation_date, get_last_modification_date, get_number_commits, \
    md, \
    output_path, static_url, template_path
from aqui_brain_dump.main import datetimeformat
from aqui_brain_dump.util import path_to_url

env = Environment(loader=FileSystemLoader(template_path))
env.filters['datetime'] = datetimeformat
template_article = env.get_template('article.html')
template_index = env.get_template('index.html')


logger = logging.getLogger(__name__)


class Note:
    notes = {}
    note_executor = ThreadPoolExecutor(max_workers=10)
    futures_executor = []
    tags_dict = {}

    def __init__(self, file_path):
        self.file_path = file_path
        self.path = Path(file_path).relative_to(content_path)
        self.content = None
        self.backlinks = []
        self.links = []
        self.title = ''
        self.meta = {}
        self.tags = []
        self.url = ''
        self.last_mod = None
        self.number_edits = 1
        self.creation_date = None

    @classmethod
    def create_from_path(cls, file_path):
        logger.debug(f'Creating note from file: {file_path}')
        rel_path = Path(file_path).relative_to(content_path)
        note = cls.notes.get(path_to_url(rel_path), False)
        if note:
            return note
        note = cls(file_path)
        note.parse_file()
        return note

    @classmethod
    def create_from_url(cls, url: str):
        """ Creates a note without content, normally product of links to non existing notes
        """
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
            logger.info(f'{self.file_path} does not exist, creating empty note')
            self.title = ' '.join(str(self.path).split('_')).strip('/').strip('.md')
            self.url = path_to_url(self.path)
            if not all(ord(c) < 128 for c in self.url):
                logger.warning(f'{self.url} has non-ascii characters')
            self.notes[str(self.path.absolute()).lower()] = self
            return

        with codecs.open(self.file_path, 'r', encoding='utf-8') as f:
            md.reset()
            md.links = []
            post = frontmatter.load(f)
            self.content = md.convert(post.content)
            bs = BeautifulSoup(self.content, 'html.parser')
            h1 = bs.find('h1')
            h1_title = None
            if h1 is not None and h1.get_text() != '':
                h1_title = h1.get_text()
                h1.decompose()
                self.content = bs.prettify()
            if 'title' in post.metadata:
                self.title = post.metadata['title']
            elif h1_title is not None:
                self.title = h1_title
            else:
                self.title = ' '.join(str(self.path).split('_')).strip('/').strip('.md')

            self.url = path_to_url(self.path)
            if 'slug' in post.metadata:
                self.url = post.metadata.get('url')
            self.meta = post.metadata

            self.links = md.links
            self.tags = md.tags
            for tag in self.tags:
                tag = tag.lower()
                if tag not in self.tags_dict:
                    self.tags_dict[tag] =[self, ]
                else:
                    self.tags_dict[tag].append(self)
            self.futures_executor.append(self.note_executor.submit(self.update_git_information))

        logger.debug(f'Added {self} with url {self.url}')
        self.notes[self.url] = self

    def update_git_information(self):
        self.last_mod = get_last_modification_date(self.file_path)
        self.creation_date = get_creation_date(self.file_path)
        self.number_edits = get_number_commits(self.file_path)

    def render(self):
        logger.debug(f'Preparing to render {self}')
        context = {
            'note': self,
            'static': static_url,
            'base_url': base_url,
            }
        out_path = output_path / self.url[1:]
        out_path.mkdir(parents=True, exist_ok=True)
        if 'index.md' == self.file_path.name:
            template = template_index
        else:
            template = template_article
        with open(out_path / 'index.html', 'w', encoding='utf-8') as out:
            logger.debug(f'Writing {template} with {self} information, to {out_path}')
            out.write(template.render(context))

    @classmethod
    def build_backlinks(cls):
        for note in list(cls.notes.values()):
            for link in note.links:
                logger.debug(f'{note.url} links to {link}')
                link_to = cls.notes.get(link, False)
                if link_to:
                    link_to.backlinks.append(note)
                    logger.debug(f'Appending {note} to backlinks of {link_to}')
                else:
                    new_note = Note.create_from_url(link)
                    while len([f for f in Note.futures_executor if f.running()]):
                        time.sleep(.01)
                    new_note.backlinks.append(note)
                    logger.debug(f'Creating {new_note} and appending {note} to its backlinks')


    def __str__(self):
        return self.title or str(self.path)

    def __repr__(self):
        return f'<Note {self.file_path or self.path}>'