import codecs
import sys
from distutils.dir_util import copy_tree
from shutil import copyfile
import frontmatter
from jinja2 import Environment, FileSystemLoader, Template
import markdown
import os
from bs4 import BeautifulSoup

from aqui_brain_dump.backlinks_wikilinks import WikiLinkExtension
from aqui_brain_dump.git_process import get_creation_date, get_last_modification_date, get_number_commits

THIS_DIR = os.getcwd()


def datetimeformat(value, format='%Y-%m-%d'):
    try:
        return value.strftime(format)
    except AttributeError:
        return value


def main(
        base_website="https://www.aquiles.me",
        content_dir='content',
        output_dir='output',
        static_dir='static',
        template_dir='templates',
        index_page='index.md',
):
    if len(sys.argv) > 1:
        base_website = sys.argv[1]
    print(base_website)
    dir = os.path.abspath(os.path.join(THIS_DIR, content_dir))
    out_dir = os.path.abspath(os.path.join(THIS_DIR, output_dir))
    static_dir = os.path.abspath(os.path.join(THIS_DIR, static_dir))
    template_dir = os.path.abspath(os.path.join(THIS_DIR, template_dir))


    creation_dates = get_creation_date(content_dir)
    modification_dates = get_last_modification_date(content_dir)
    number_of_edits = get_number_commits(content_dir)

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
        if sub_dir == '.':
            sub_dir = ''

        if sub_dir.startswith('.'):
            continue

        if sub_dir:
            sub_dir = f'/{sub_dir}'

        for file in dirs[2]:
            if not file.endswith('.md'):
                copyfile(os.path.join(cur_dir, file), os.path.join(out_dir, sub_dir, file))
                continue

            filename = ''.join(file.split('.')[:-1])
            page_url = f"{sub_dir}/{filename}".lower()
            page_url = page_url.replace(' ', '_')
            if page_url not in pages:
                pages[page_url] = dict(
                    content=None,
                    links=[],
                    meta={},
                    filename='',
                    url='',
                    last_mod=None,
                    creation_date=None,
                    description='',
                    title='',
                )

            with codecs.open(os.path.join(cur_dir, file), 'r', encoding='utf-8') as f:
                md.reset()
                md.links = []
                post = frontmatter.load(f)
                content = md.convert(post.content)
                bs = BeautifulSoup(content, 'html.parser')
                h1 = bs.find('h1')
                h1_title = None
                if h1 is not None and h1.get_text() != '':
                    h1_title = h1.get_text()
                    h1.decompose()
                    content = bs.prettify()
                if 'title' in post.metadata:
                    title = post.metadata['title']
                elif h1_title is not None:
                    title = h1_title
                else:
                    title = ' '.join(page_url.split('_')).strip('/')

                pages[page_url].update({
                    'content': content,
                    'meta': post.metadata,
                    'filename': filename,
                    'url': base_website+'/' if index_page.startswith(filename) else base_website+page_url+'/',
                    'last_mod': modification_dates.get(page_url, 'None'),
                    'creation_date': creation_dates.get(page_url, 'None'),
                    'number_edits': number_of_edits.get(page_url, 'None'),
                    'links': md.links,
                    'backlinks': [],
                    'title': title
                })

                for link in md.links:
                    link = link.replace(' ', '_').lower()
                    link = f"/{link}"
                    if link not in pages:
                        pages[link] = dict(
                            content=None,
                            links=[],
                            backlinks=[],
                            meta={},
                            filename='',
                            url=base_website + link,
                            last_mod=None,
                            creation_date=None,
                            description='',
                            title='',
                        )
                    if pages[page_url] not in pages[link]['backlinks']:
                        pages[link]['backlinks'].append(pages[page_url])

    env = Environment(loader=FileSystemLoader(template_dir))
    env.filters['datetime'] = datetimeformat

    template_article = env.get_template('article.html')
    template_index = env.get_template('index.html')

    for page, values in pages.items():
        if page.startswith('/'): page = page[1:]
        os.makedirs(os.path.join(out_dir, page), exist_ok=True)
        context = {
            'title': values['filename'].replace('_', ' '),
            'content': values['content'],
            'static': 'static',
            'base_url': base_website,
            'backlinks': values['links'],
            'meta': values['meta'],
            'url': values['url'],
            'page': values,
        }
        context.update(values['meta'])

        if index_page.startswith(page):
            with open(os.path.join(out_dir, 'index.html'), 'w') as out_file:
                out_file.write(template_index.render(context))
            continue

        with open(os.path.join(out_dir, page, 'index.html'), 'w') as out_file:
            try:
                out_file.write(template_article.render(context))
            except UnicodeEncodeError as e:
                print(f'Problem creating page for {page}')

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sitemap.xml'), 'r') as f:
        template = Template(f.read())

    with open(os.path.join(out_dir, 'sitemap.xml'), 'w') as f:
        f.write(template.render({'pages': pages}))




if __name__ == '__main__':
    main()