"""
Extract tags from the markdown files and add them as a metadata value to be later processed in the templates.
"""
import re

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as etree

RE_TAGS = re.compile(r"(?<!`)(#+([^#\s.,\/!$%\^&\*;{}\[\]'\"=`~()<>”\\]|:[a-zA-Z0-9])+)")


class TagInlineProcessor(InlineProcessor):
    RE_TAGS = r"(#+([^#\s.,\/!$%\^&\*;{}\[\]'\"=`~()<>”\\]|:[a-zA-Z0-9])+)"

    def handleMatch(self, m, data):
        if m.group(1):
            if not hasattr(self.md, 'tags'):
                self.md.tags = set()

            self.md.tags.add(m.group(1))
            a = etree.Element('a')
            a.text = m[0]
            a.set('href', '/tags/{}'.format(m.group(1).strip('#')))
            return a, m.start(0), m.end(0)


class TagExtension(Extension):
    def extendMarkdown(self, md):
        self.md = md
        md.registerExtension(self)
        md.inlinePatterns.register(TagInlineProcessor(TagInlineProcessor.RE_TAGS, md), 'tags', 65)

    def reset(self):
        self.md.tags = set()


def makeExtension(**kwargs):  # pragma: no cover
    return TagExtension(**kwargs)