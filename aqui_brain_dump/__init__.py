from pathlib import Path

import markdown

from aqui_brain_dump.backlinks_wikilinks import WikiLinkExtension
from aqui_brain_dump.extension_citations import CitationExtension
from aqui_brain_dump.extension_tags import TagExtension
from aqui_brain_dump.extension_wikiimage import WikiImageExtension
from aqui_brain_dump.git_process import get_creation_date, get_last_modification_date, get_number_commits
from aqui_brain_dump.parse_bibliography import parse_bibliography


content_path = Path('./content').absolute()
static_path = Path('.') / 'static'
output_path = Path('./output').absolute()
template_path = Path('./templates').absolute()
bibliography_file = Path('./citation_library.json').absolute()
bibliography = parse_bibliography(bibliography_file)
static_url = 'static'
base_url = 'https://notes.aquiles.me'

md = markdown.Markdown(extensions=[
        'meta',
        WikiLinkExtension(),
        WikiImageExtension(),
        TagExtension(),
        CitationExtension(bibliography_data=bibliography),
        'admonition',
        'markdown_checklist.extension',
        'fenced_code',
        'codehilite',
        # 'pyembed.markdown',
        'footnotes',
        'md4mathjax',
    ])

DEFUALT_MATHJAX_SETTING = r"""
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [["$$", "$$"], ['\\[', '\\]']],
    packages: {
      '[+]': ['mhchem']
    }
  },
  loader: {
    load: ['[tex]/mhchem']
  },
}
"""