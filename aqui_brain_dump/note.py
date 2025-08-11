import datetime
import logging
import time
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
import json

import networkx as nx

import frontmatter
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from aqui_brain_dump import content_path, get_creation_date, get_last_modification_date, get_number_commits, \
    md, \
    output_path, static_url, template_path
from aqui_brain_dump import datetimeformat
from aqui_brain_dump.util import path_to_url, has_invalid_filename_chars

env = Environment(loader=FileSystemLoader(template_path))
env.filters['datetime'] = datetimeformat
template_article = env.get_template('note.html')
template_index = env.get_template('index.html')


logger = logging.getLogger(__name__)


class Note:
    notes = {}
    note_executor = ThreadPoolExecutor(max_workers=20)
    futures_executor = []
    tags_dict = {}
    lit_notes = {}
    bibliography = {}

    def __init__(self, file_path, parse_git = True):
        self.file_path = file_path
        self.path = Path(file_path).relative_to(content_path)
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

    def _local_network(self):
        """Return nodes and edges for local network graph"""
        nodes = {self.url: self}
        for b in self.backlinks:
            nodes[b.url] = b
        for link in self.links:
            n = self.notes.get(link)
            if n:
                nodes[n.url] = n

        G = nx.DiGraph()
        for u in nodes:
            G.add_node(u)
        edges = []
        for link in self.links:
            tgt = self.notes.get(link)
            if tgt:
                edges.append({'source': self.url, 'target': tgt.url})
                G.add_edge(self.url, tgt.url)
        for b in self.backlinks:
            edges.append({'source': b.url, 'target': self.url})
            G.add_edge(b.url, self.url)

        pos = nx.spring_layout(G, seed=1)
        node_data = []
        for u, n in nodes.items():
            x, y = pos[u]
            node_data.append({
                'id': u,
                'title': n.title,
                'size': len(n.backlinks),
                'x': float(x),
                'y': float(y),
            })
        return {'nodes': node_data, 'edges': edges}

    def _inject_network_graph(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        body = soup.body
        if body is None:
            return html
        button = soup.new_tag('button', id='show-network')
        button.string = 'Show Connections'
        body.append(button)

        popup = soup.new_tag('div', id='network-popup')
        popup['style'] = (
            'display:none; position:fixed; top:0; left:0; width:100%; height:100%; '
            'background-color:rgba(0,0,0,0.6); z-index:1000;')
        inner = soup.new_tag('div', id='network-container')
        inner['style'] = (
            'position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); '
            'background:white; padding:1em;')
        close_b = soup.new_tag('button', id='close-network')
        close_b.string = 'Close'
        inner.append(close_b)
        graph_div = soup.new_tag('div', id='network-graph')
        inner.append(graph_div)
        popup.append(inner)
        body.append(popup)

        script = soup.new_tag('script')
        data = json.dumps(self._local_network())
        script.string = f"const networkData = {data};\n" + """
function drawNetwork(data){
  const w=600,h=400;
  const svgNS='http://www.w3.org/2000/svg';
  const container=document.getElementById('network-graph');
  container.innerHTML='';
  const svg=document.createElementNS(svgNS,'svg');
  svg.setAttribute('width',w);
  svg.setAttribute('height',h);
  function sx(x){return (x+1)/2*w;}
  function sy(y){return (y+1)/2*h;}
  data.edges.forEach(e=>{
    const s=data.nodes.find(n=>n.id===e.source);
    const t=data.nodes.find(n=>n.id===e.target);
    if(!s||!t) return;
    const l=document.createElementNS(svgNS,'line');
    l.setAttribute('x1',sx(s.x));
    l.setAttribute('y1',sy(s.y));
    l.setAttribute('x2',sx(t.x));
    l.setAttribute('y2',sy(t.y));
    l.setAttribute('stroke','#999');
    svg.appendChild(l);
  });
  data.nodes.forEach(n=>{
    const c=document.createElementNS(svgNS,'circle');
    c.setAttribute('cx',sx(n.x));
    c.setAttribute('cy',sy(n.y));
    c.setAttribute('r',5+2*n.size);
    c.setAttribute('fill','#1f77b4');
    svg.appendChild(c);
    const text=document.createElementNS(svgNS,'text');
    text.setAttribute('x',sx(n.x)+8);
    text.setAttribute('y',sy(n.y)+4);
    text.textContent=n.title;
    text.setAttribute('font-size','10');
    svg.appendChild(text);
  });
  container.appendChild(svg);
}
document.getElementById('show-network').addEventListener('click',()=>{
  document.getElementById('network-popup').style.display='block';
  drawNetwork(networkData);
});
document.getElementById('close-network').addEventListener('click',()=>{
  document.getElementById('network-popup').style.display='none';
});
"""
        body.append(script)
        return str(soup)

    @classmethod
    def create_from_path(cls, file_path, parse_git=False):
        logger.info(f'Creating note from file: {file_path}')
        rel_path = Path(file_path).relative_to(content_path)
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
        logger.info(f'Parsing contents of {self}')
        if not Path(self.file_path).is_file():
            logger.info(f'{self.file_path} does not exist, creating empty note')
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
            self.notes[str(self.path.absolute()).lower()] = self
            return

        with open(self.file_path, 'r', encoding='utf-8') as f:
            md.reset()
            md.links = set()

            try:
                post = frontmatter.load(f)
                self.content = md.convert(post.content)
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
                self.content = bs.prettify()
            if 'title' in post.metadata:
                self.title = post.metadata['title']
            elif h1_title is not None:
                self.title = h1_title
            else:
                self.title = ' '.join(str(self.path).split('_')).strip('/').capitalize()
                if self.title.endswith('.md'):
                    self.title = self.title[:-3]

            self.url = path_to_url(self.path)
            if 'slug' in post.metadata:
                self.url = post.metadata.get('url')
            self.meta = post.metadata
            self.links = md.links
            logger.debug(f'{self.title} links: {self.links}')
            self.tags = md.tags
            self.cites = md.cites
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

    def update_git_information(self):
        if self.parse_git:
            self.last_mod = get_last_modification_date(self.file_path)
            self.creation_date = get_creation_date(self.file_path)
            self.number_edits = get_number_commits(self.file_path)
        else:
            self.last_mod = datetime.date.today()
            self.creation_date = datetime.date.today()
            self.number_edits = 1

    def render(self, base_url):
        logger.debug(f'Preparing to render {self}')
        context = {
            'note': self,
            'static': static_url,
            'base_url': base_url,
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

        if 'template' in self.meta:
            template = env.get_template(self.meta.get('template'))
        else:
            template = template_article
        html = template.render(context)
        html = self._inject_network_graph(html)
        with open(out_path / 'index.html', 'w', encoding='utf-8') as out:
            logger.debug(f'Writing {template} with {self} information, to {out_path}')
            out.write(html)

    @classmethod
    def build_backlinks(cls):
        for note in list(cls.notes.values()):
            for link in note.links:
                logger.debug(f'{note.url} links to {link}')
                link_to = cls.notes.get(link, False)
                if link_to:
                    link_to.backlinks.add(note)
                    logger.debug(f'Adding {note} to backlinks of {link_to}')
                else:
                    new_note = Note.create_from_url(link)
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