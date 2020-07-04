from distutils.dir_util import copy_tree
from shutil import copyfile
import frontmatter
from jinja2 import Environment, FileSystemLoader
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

    env = Environment(loader=FileSystemLoader(template_dir))
    template_article = env.get_template('article.html')
    template_index = env.get_template('index.html')

    for page, values in pages.items():
        if page.startswith('/'): page = page[1:]
        print(f"Creating {page}")
        os.makedirs(os.path.join(out_dir, page), exist_ok=True)
        context = {
            'title': values['filename'],
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

if __name__ == '__main__':
    main()