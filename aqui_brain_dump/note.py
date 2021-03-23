import codecs
from pathlib import Path

import frontmatter
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from aqui_brain_dump import content_path, get_creation_date, get_last_modification_date, get_number_commits, md, \
    output_path, static_url, template_path
from aqui_brain_dump.main import datetimeformat
from aqui_brain_dump.util import path_to_url

env = Environment(loader=FileSystemLoader(template_path))
env.filters['datetime'] = datetimeformat
template_article = env.get_template('article.html')
template_index = env.get_template('index.html')


class Note:
    notes = {}

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
        self.parse_file()
        self.notes[str(self.path.absolute()).lower()] = self

    @classmethod
    def create_from_path(cls, file_path):
        rel_path = Path(file_path).relative_to(content_path)
        if note := cls.notes.get(rel_path, False):
            return note
        return cls(file_path)

    def parse_file(self):
        if not Path(self.file_path).is_file():
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
            self.last_mod = get_last_modification_date(self.file_path)
            self.creation_date = get_creation_date(self.file_path)
            self.number_edits = get_number_commits(self.file_path)
            self.links = md.links
            self.tags = md.tags

    def render(self):
        context = {
            'note': self,
            'static': static_url,
            }
        if 'index' in str(self.path):
            out_path = output_path
            out_path.mkdir(parents=True, exist_ok=True)
            template = template_index
            print(self.path)
        else:
            out_path = output_path / self.url[1:]
            out_path.mkdir(parents=True, exist_ok=True)
            template = template_article
        with open(out_path / 'index.html', 'w', encoding='utf-8') as out:
            print(self.title)
            out.write(template.render(context))

    @classmethod
    def build_backlinks(cls):
        for note in list(cls.notes.values()):
            for link in note.links:
                if link.startswith('/'):
                    link = link[1:]
                link = content_path / (str(link) + '.md')
                if str(link.absolute()).lower() in cls.notes:
                    link_to = cls.notes[str(link.absolute()).lower()]
                    link_to.backlinks.append(note)
                else:
                    new_note = Note.create_from_path(content_path / (str(link) + '.md'))
                    new_note.backlinks.append(note)

    def __str__(self):
        return self.title or str(self.path)

    def __repr__(self):
        return f'<Note {self.file_path or self.path}>'