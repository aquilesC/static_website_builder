import re
from markdown.util import etree

from markdown import Extension
from markdown.inlinepatterns import InlineProcessor

RE_CITES = r"(@+([^#\s.,\/!$%\^&\*;{}\[\]'\"=`~()<>”\\]|:[a-zA-Z0-9])+)"


class CitationInlineProcessor(InlineProcessor):
    RE_CITES = RE_CITES
    
    def __init__(self, pattern, md, biblio):
        self.biblio = biblio
        super(CitationInlineProcessor, self).__init__(pattern, md)

    def handleMatch(self, m, data):
        if m.group(1):
            if not hasattr(self.md, 'cites'):
                self.md.cites = []
            cite = m.group(1).strip('@').lower()
            self.md.cites.append(cite)
            if cite in self.biblio:
                a = etree.Element('span')
                a.text = m[0]
                b = etree.Element('span')
                b.text = self.biblio[cite]['title']
                b.set('class', 'tooltiptext')
                a.append(b)
                a.set('class', 'tooltip')
            else:
                a = m[0]
            return a, m.start(0), m.end(0)


class CitationExtension(Extension):
    def __init__(self, **kwargs):
        self.biblio = kwargs.pop('bibliography_data')
        super().__init__(**kwargs)
        
    def extendMarkdown(self, md):
        self.md = md
        md.registerExtension(self)
        md.inlinePatterns.register(CitationInlineProcessor(RE_CITES, md, self.biblio), 'cites', 66)

    def reset(self):
        self.md.cites = []


def makeExtension(**kwargs):
    return CitationExtension(**kwargs)