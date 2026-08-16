"""
Wikilinks with Backlinks
========================

Adapted directly from the official extension `Wikilinks <https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/meta.py>`_.
It adds a new list attribute to the markdown object that holds all the targets of the wiki links. With this, it is
possible to build the graph of backlinks, but it still requires a two-pass approach in order to have the information
ready for the template rendering.

"""
import logging

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as etree
import re
from pathlib import Path

from aqui_brain_dump.util import is_private_path


logger = logging.getLogger(__name__)


def build_url(label, base, end):
    """ Build a url from the label, a base, and an end. """
    label = label.split('|')[0]
    clean_label = re.sub(r'([ ]+_)|(_[ ]+)|([ ]+)', '_', label)
    return '{}{}{}'.format(base, clean_label, end)


class WikiLinkExtension(Extension):

    def __init__(self, **kwargs):
        self.config = {
            'base_url': ['/', 'String to append to beginning or URL.'],
            'end_url': ['/', 'String to append to end of URL.'],
            'html_class': ['wikilink', 'CSS hook. Leave blank for none.'],
            'build_url': [build_url, 'Callable formats URL from label.'],
            'bibliography_data': [{}, 'Bibliography data dictionary'],
        }

        super().__init__(**kwargs)

    def reset(self):
        self.md.links = set()

    def extendMarkdown(self, md):
        self.md = md
        self.reset()
        # append to end of inline patterns
        WIKILINK_RE = r'\[\[([\w_\|\/ \-.\@:]+)\]\]'
        wikilinkPattern = WikiLinksInlineProcessor(WIKILINK_RE, self.getConfigs())
        wikilinkPattern.md = md
        md.inlinePatterns.register(wikilinkPattern, 'wikilink', 75)


class WikiLinksInlineProcessor(InlineProcessor):
    def __init__(self, pattern, config):
        super().__init__(pattern)
        self.config = config

    def handleMatch(self, m, data):
        if m.group(1).strip():
            base_url, end_url, html_class = self._getMeta()
            label = m.group(1).strip()
            text = label.split('|')[-1]
            href = label.split('|')[0].lower().replace(' ', '_')
            if href.startswith('/'):
                href = href[1:]
            url = self.config['build_url'](href, base_url, end_url)
            logger.debug(f'Got link to {url}')
            if is_private_path(url) or is_private_path(href) or is_private_path(label):
                logger.debug(f'Wikilink {label} points to a private note, skipping wikilink processing.')
                if '|' in label:
                    display_text = label.split('|')[-1]
                else:
                    target = label.split('|')[0].strip('/')
                    display_text = Path(target).name
                return display_text, m.start(0), m.end(0)


            if not hasattr(self.md, 'links'):
                self.md.links = set()

            self.md.links.add(url)

            cite_key = text.strip('@').lower()
            biblio = self.config['bibliography_data'][0] if isinstance(self.config['bibliography_data'], (list, tuple)) else self.config.get('bibliography_data', {})
            if cite_key in biblio:
                a = etree.Element('a')
                a.text = text
                a.set('href', url.lower())
                a.set('class', 'litnote tooltip')
                span = etree.Element('span')
                span.text = biblio[cite_key]['title']
                span.set('class', 'tooltiptext')
                a.append(span)
            else:
                a = etree.Element('a')
                a.text = text
                a.set('href', url.lower())
                if html_class:
                    a.set('class', html_class)
        else:
            a = ''
        return a, m.start(0), m.end(0)

    def _getMeta(self):
        """ Return meta data or config data. """
        base_url = self.config['base_url']
        end_url = self.config['end_url']
        html_class = self.config['html_class']
        if hasattr(self.md, 'Meta'):
            if 'wiki_base_url' in self.md.Meta:
                base_url = self.md.Meta['wiki_base_url'][0]
            if 'wiki_end_url' in self.md.Meta:
                end_url = self.md.Meta['wiki_end_url'][0]
            if 'wiki_html_class' in self.md.Meta:
                html_class = self.md.Meta['wiki_html_class'][0]
        return base_url, end_url, html_class


def makeExtension(**kwargs):  # pragma: no cover
    return WikiLinkExtension(**kwargs)