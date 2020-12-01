import codecs
import sys
from datetime import datetime, timezone
from distutils.dir_util import copy_tree
from shutil import copyfile
import frontmatter
from jinja2 import Environment, FileSystemLoader, Template
import markdown
import os
from bs4 import BeautifulSoup

from aqui_brain_dump.backlinks_wikilinks import WikiLinkExtension
from aqui_brain_dump.extension_citations import CitationExtension
from aqui_brain_dump.extension_tags import TagExtension
from aqui_brain_dump.git_process import get_creation_date, get_last_modification_date, get_number_commits
from aqui_brain_dump.parse_bibliography import parse_bibliography

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
        bibliography_file='citation_library.json',
):
    if len(sys.argv) > 1:
        base_website = sys.argv[1]
    print(base_website)
    dir = os.path.abspath(os.path.join(THIS_DIR, content_dir))
    out_dir = os.path.abspath(os.path.join(THIS_DIR, output_dir))
    static_dir = os.path.abspath(os.path.join(THIS_DIR, static_dir))
    template_dir = os.path.abspath(os.path.join(THIS_DIR, template_dir))

    tags = {}

    creation_dates = get_creation_date(content_dir)
    modification_dates = get_last_modification_date(content_dir)
    number_of_edits = get_number_commits(content_dir)

    # bibliography_file = os.path.join(content_dir, bibliography_file)
    bibliography = parse_bibliography(bibliography_file)

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    tags_dir = os.path.join(out_dir, 'tags')
    if not os.path.isdir(tags_dir):
        os.makedirs(tags_dir)

    out_static_dir = os.path.join(out_dir, 'static')
    if not os.path.isdir(out_static_dir):
        os.makedirs(out_static_dir)
    copy_tree(static_dir, out_static_dir)

    md = markdown.Markdown(extensions=[
        'meta',
        WikiLinkExtension(),
        TagExtension(),
        CitationExtension(bibliography_data=bibliography),
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
                    last_mod='None',
                    creation_date='None',
                    number_of_edits='None',
                    description='',
                    title='',
                    backlinks=[],
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
                    'title': title
                })

                if len(md.tags):
                    for tag in md.tags:
                        if tag not in tags:
                            tags[tag] = []
                        tags[tag].append(pages[page_url])

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
                            last_mod='None',
                            creation_date='None',
                            number_edits='None',
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
            'backlinks': values['backlinks'],
            'meta': values['meta'],
            'url': values['url'],
            'page': values,
        }
        context.update(values['meta'])

        if index_page.startswith(page):
            with open(os.path.join(out_dir, 'index.html'), 'w', encoding="utf-8") as out_file:
                out_file.write(template_index.render(context))
            continue

        with open(os.path.join(out_dir, page, 'index.html'), 'w', encoding="utf-8") as out_file:
            try:
                out_file.write(template_article.render(context))
            except UnicodeEncodeError as e:
                print(f'Problem creating page for {page}')

    for tag, values in tags.items():
        # tag = tag.strip('#')
        context = {
            'title': tag,
            'backlinks': tags[tag],
            'static': 'static',
            'meta': {
                'title': 'Tag: ' + tag,
                'description': 'Articles containing the tag ' + tag
            },
            'page': {
                'content': None,
                'backlinks': tags[tag],
            }
        }

        tag_dir = os.path.join(tags_dir, tag.strip('#'))
        try:
            os.makedirs(tag_dir, exist_ok=True)
        except OSError as e:
            print(f'Problem creating tag: {tag.strip("#")}')
            continue

        with open(os.path.join(tag_dir, 'index.html'), 'w') as out_file:
            try:
                out_file.write(template_article.render(context))
            except UnicodeEncodeError as e:
                print(f'Problem creating page for {tag.strip("#")}')

    try:
        min_number_edits = min(number_of_edits.values())
        max_number_edits = max(number_of_edits.values())
    except:
        min_number_edits = 1
        max_number_edits = 10
    today = datetime.now(tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')
    env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
    env.filters['datetime'] = datetimeformat
    sitemap = env.get_template('sitemap.xml')
    with open(os.path.join(out_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap.render(
            {'pages': pages,
             'min_edits': min_number_edits,
             'max_edits': max_number_edits,
             'today': today}))

    rss_feed = env.get_template('feed.rss')
    with open(os.path.join(out_dir, 'feed.rss'), 'w', encoding='utf-8') as f:
        f.write(rss_feed.render(
            {'pages': pages,
             'min_edits': min_number_edits,
             'max_edits': max_number_edits,
             'today': today
             }))


if __name__ == '__main__':
    main()