import codecs
import time
from distutils.dir_util import copy_tree
from shutil import copyfile
import frontmatter
from jinja2 import Environment, FileSystemLoader, Template
import markdown
import os

from aqui_brain_dump.backlinks_wikilinks import WikiLinkExtension

THIS_DIR = os.getcwd()

def main(
        base_website="https://www.aquiles.me/",
        content_dir='content',
        output_dir='output',
        static_dir='static',
        template_dir='templates',
        index_page='index.md',
):

    base_website = base_website

    dir = os.path.abspath(os.path.join(THIS_DIR, content_dir))
    out_dir = os.path.abspath(os.path.join(THIS_DIR, output_dir))
    static_dir = os.path.abspath(os.path.join(THIS_DIR, static_dir))
    template_dir = os.path.abspath(os.path.join(THIS_DIR,template_dir))

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    out_static_dir = os.path.join(out_dir, 'static')
    if not os.path.isdir(out_static_dir):
        os.makedirs(out_static_dir)
    copy_tree(static_dir, out_static_dir)


    md = markdown.Markdown(extensions=[
        'meta',
        WikiLinkExtension(),
        'admonition',
        'markdown_checklist.extension',
        'fenced_code',
        'codehilite',
        'pyembed.markdown',
        'footnotes',
    ])

    pages = {}
    f_walk = os.walk(dir)
    for dirs in f_walk:
        cur_dir = dirs[0]
        sub_dir = os.path.relpath(cur_dir, start=dir)
        if sub_dir == '.': sub_dir = ''
        if sub_dir.startswith('.'):
            continue
        if sub_dir: sub_dir = f'/{sub_dir}'
        for file in dirs[2]:
            if not file.endswith('.md'):
                copyfile(os.path.join(cur_dir, file), os.path.join(out_dir, sub_dir, file))
                continue

            filename = ''.join(file.split('.')[:-1])
            page_url = f"{sub_dir}/{filename}".lower()
            page_url = page_url.replace(' ', '_')
            if not page_url in pages:
                pages[page_url] = dict(content=None, links=[], meta={}, filename='', url='')

            with codecs.open(os.path.join(cur_dir, file), 'r', encoding='utf-8') as f:
                md.reset()
                md.links = []
                post = frontmatter.load(f)
                pages[page_url].update({
                    'content': md.convert(post.content),
                    'meta': post.metadata,
                    'filename': filename,
                    'url': base_website+page_url,
                    'last_mod': time.strftime('%Y-%m-%d', time.localtime(os.stat(os.path.join(cur_dir, file)).st_mtime))
                })
                for link in md.links:
                    link = link.replace(' ', '_').lower()
                    if link not in pages:
                        pages[link] = dict(content=None, links=[], meta={}, filename=link, url=base_website+link)

                    pages[link]['links'].append(
                        page_url if not file == index_page else f'{sub_dir}/'
                    )
                    print(f'{page_url}')

    env = Environment(loader=FileSystemLoader(template_dir))
    template_article = env.get_template('article.html')
    template_index = env.get_template('index.html')

    for page, values in pages.items():
        if page.startswith('/'): page = page[1:]
        print(f"Creating {page}")
        os.makedirs(os.path.join(out_dir, page), exist_ok=True)
        context = {
            'title': values['filename'].replace('_', ' '),
            'content': values['content'],
            'static': 'static',
            'inbound_links': values['links'],
            'meta': values['meta'],
            'url': values['url'],
        }
        context.update(values['meta'])
        if index_page.startswith(page):
            with open(os.path.join(out_dir, 'index.html'), 'w') as out_file:
                out_file.write(template_index.render(context))
            continue

        with open(os.path.join(out_dir, page, 'index.html'), 'w') as out_file:
            out_file.write(template_article.render(context))

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sitemap.xml'), 'r') as f:
        template = Template(f.read())

    with open(os.path.join(out_dir, 'sitemap.xml'), 'w') as f:
        f.write(template.render({'pages': pages}))


if __name__ == '__main__':
    main()