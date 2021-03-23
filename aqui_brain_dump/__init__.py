from pathlib import Path

import markdown

from aqui_brain_dump.backlinks_wikilinks import WikiLinkExtension
from aqui_brain_dump.extension_citations import CitationExtension
from aqui_brain_dump.extension_tags import TagExtension
from aqui_brain_dump.git_process import get_creation_date, get_last_modification_date, get_number_commits
from aqui_brain_dump.parse_bibliography import parse_bibliography


content_path = Path('/Users/aquiles/Documents/Web/aquiles.me/content')
output_path = Path('/Users/aquiles/Documents/Web/aquiles.me/new_output')
template_path = Path('/Users/aquiles/Documents/Web/aquiles.me/templates')
bibliography_file = '/Users/aquiles/Documents/Web/aquiles.me/citation_library.json'
bibliography = parse_bibliography(bibliography_file)
static_url = 'static'

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
