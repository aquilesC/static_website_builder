import codecs
from pathlib import Path, PurePath

import frontmatter
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from aqui_brain_dump import content_path, creation_dates, md, modification_dates, number_of_edits, output_path, \
    template_path
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
        rel_path = Path(file_path).relative_to(content_path)
        self.rel_path = rel_path
        self.content = None
        self.backlinks = []
        self.links = []
        self.title = ''
        self.metadata = {}
        self.tags = []
        self.parse_file()
        self.url = path_to_url(file_path, content_path)
        self.notes[self.url] = self


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
                self.title = ' '.join(str(self.rel_path).split('_')).strip('/').strip('.md')

            self.metadata = post.metadata
            self.last_mod = modification_dates.get(str(self.rel_path), None)
            self.creation_date = creation_dates.get(str(self.rel_path), None)
            self.number_edits = number_of_edits.get(str(self.rel_path), None)
            self.links = md.links
            self.tags = md.tags

    def render(self):
        out_path = output_path / self.url[1:]
        print(out_path)
        out_path.mkdir(parents=True, exist_ok=True)
        context = {'note': self}
        if 'index' in str(self.rel_path):
            template = template_index
        else:
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
                if link.lower() + '.md' in cls.notes:
                    link_to = cls.notes[link.lower() + '.md']
                    link_to.backlinks.append(note)
                else:
                    Note.create_from_path(content_path / (link + '.md'))

    def __str__(self):
        return self.title or str(self.rel_path)

    def __repr__(self):
        return f'<Note {self.file_path or self.rel_path}>'