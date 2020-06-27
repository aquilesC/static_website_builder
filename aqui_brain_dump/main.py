from distutils.dir_util import copy_tree
from shutil import copyfile
import frontmatter
from jinja2 import Template
import markdown
import os

from aqui_brain_dump.backlinks_wikilinks import WikiLinkExtension

base_website = "https://www.aquiles.me/"

dir = os.path.abspath(os.path.join('..', 'content'))
out_dir = os.path.abspath(os.path.join('..', 'output'))
static_dir = os.path.abspath(os.path.join('..', 'static'))
template_dir = os.path.abspath(os.path.join('..', 'templates'))

if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

out_static_dir = os.path.join(out_dir, 'static')
if not os.path.isdir(out_static_dir):
    os.makedirs(out_static_dir)
copy_tree(static_dir, out_static_dir)

with open(os.path.join(template_dir, 'base.html'), 'r') as f:
    template = Template(f.read())

md = markdown.Markdown(extensions=[
    'meta',
    WikiLinkExtension(),
    'admonition',
    'markdown_checklist.extension',
    'fenced_code',
    'codehilite',
    'pyembed.markdown',
])

pages = {}
f_walk = os.walk(dir)
for dirs in f_walk:
    cur_dir = dirs[0]
    sub_dir = os.path.relpath(cur_dir, start=dir)
    if sub_dir == '.': sub_dir = ''
    for file in dirs[2]:
        if not file.endswith('.md'):
            print(os.path.join(cur_dir, file))
            copyfile(os.path.join(cur_dir, file), os.path.join(out_dir, sub_dir, file))
            continue

        filename = ''.join(file.split('.')[:-1])
        page_url = f"{sub_dir}/{filename}"
        if not page_url in pages:
            pages[page_url] = dict(content=None, links=[], meta={}, filename='', url='')

        with open(os.path.join(cur_dir, file), 'r') as f:
            md.reset()
            md.links = []
            post = frontmatter.load(f)
            pages[page_url].update({
                'content': md.convert(post.content),
                'meta': post.metadata,
                'filename': filename,
                'url': base_website+page_url,
            })
            for link in md.links:
                if link not in pages:
                    pages[link] = dict(content=None, links=[], meta={}, filename=link, url=base_website+link)
                pages[link]['links'].append(page_url)

for page, values in pages.items():
    if page.startswith('/'): page = page[1:]
    print(f"Creating {page}")
    os.makedirs(os.path.join(out_dir, page), exist_ok=True)
    with open(os.path.join(out_dir, page, 'index.html'), 'w') as out_file:
        context = {
            'title': values['filename'],
            'content': values['content'],
            'static': 'static',
            'inbound_links': values['links'],
            'meta': values['meta'],
            'url': values['url'],
        }
        context.update(values['meta'])
        out_file.write(template.render(context))