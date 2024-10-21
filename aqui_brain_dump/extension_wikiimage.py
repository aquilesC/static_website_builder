"""
WikiImage Extension
===================

Adapted directly from the official extension `Wikilinks <https://github.com/Python-Markdown/markdown/blob/master/markdown/extensions/meta.py>`_.
The scope is to be able to render images that use the wikiformat (``![image](path.png)``).
"""

import logging

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as etree
import re


logger = logging.getLogger(__name__)


def build_url(label, base, end):
    """ Build a url from the label, a base, and an end. """
    label = label.split('|')[0]
    return '{}{}{}'.format(base, label, end)


class WikiImageExtension(Extension):

    def __init__(self, **kwargs):
        self.config = {
            'base_url': ['/', 'String to append to beginning or URL.'],
            'end_url': ['', 'String to append to end of URL.'],
            'html_class': ['wikiimage', 'CSS hook. Leave blank for none.'],
            'build_url': [build_url, 'Callable formats URL from label.'],
        }

        super().__init__(**kwargs)

    def reset(self):
        self.md.images = []

    def extendMarkdown(self, md):
        self.md = md

        # append to end of inline patterns
        WIKIIMAGE_RE = r'\!\[\[([\w0-9\/_\| -.]+)\]\]'
        wikiimage_pattern = WikiImageInlineProcessor(WIKIIMAGE_RE, self.getConfigs())
        wikiimage_pattern.md = md
        md.inlinePatterns.register(wikiimage_pattern, 'wikiimage', 80)


class WikiImageInlineProcessor(InlineProcessor):
    def __init__(self, pattern, config):
        super().__init__(pattern)
        self.config = config

    def handleMatch(self, m, data):
        if m.group(1).strip():
            base_url, end_url, html_class = self._getMeta()
            label = m.group(1).strip()
            alt = label.split('|')[-1]
            src = label.split('|')[0]
            url = self.config['build_url'](src, base_url, end_url)
            logger.debug(f'Got image at {url}')
            img = etree.Element('img')
            img.set('alt', alt)
            img.set('src', url.lower())

            if html_class:
                img.set('class', html_class)
        else:
            img = ''
        return img, m.start(0), m.end(0)

    def _getMeta(self):
        """ Return meta data or config data. """
        base_url = self.config['base_url']
        end_url = self.config['end_url']
        html_class = self.config['html_class']
        if hasattr(self.md, 'Meta'):
            if 'base_url' in self.md.Meta:
                base_url = self.md.Meta['base_url'][0]
            if 'end_url' in self.md.Meta:
                end_url = self.md.Meta['end_url'][0]
            if 'html_class' in self.md.Meta:
                html_class = self.md.Meta['html_class'][0]
        return base_url, end_url, html_class


def makeExtension(**kwargs):  # pragma: no cover
    return WikiImageExtension(**kwargs)