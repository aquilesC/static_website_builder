"""
Extract tags from the markdown files and add them as a metadata value to be later processed in the templates.
"""
import re

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.util import etree

RE_TAGS = re.compile(r"(?<!`)(#+([^#\s.,\/!$%\^&\*;{}\[\]'\"=`~()<>”\\]|:[a-zA-Z0-9])+)")


class TagInlineProcessor(InlineProcessor):
    RE_TAGS = r"(#+([^#\s.,\/!$%\^&\*;{}\[\]'\"=`~()<>”\\]|:[a-zA-Z0-9])+)"

    def handleMatch(self, m, data):
        if m.group(1):
            if not hasattr(self.md, 'tags'):
                self.md.tags = []
            self.md.tags.append(m.group(1))

            a = etree.Element('a')
            a.text = m[0]
            a.set('href', '/tags/{}'.format(m.group(1)))
            print(m.group(1))
            return a, m.start(0), m.end(0)


class TagExtension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        md.inlinePatterns.register(TagInlineProcessor(TagInlineProcessor.RE_TAGS, md), 'tag', 65)

    def reset(self):
        self.md.tags = []


def makeExtension(**kwargs):  # pragma: no cover
    return TagExtension(**kwargs)