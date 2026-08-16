import unittest
import markdown

from aqui_brain_dump.backlinks_wikilinks import WikiLinkExtension
from aqui_brain_dump.extension_citations import CitationExtension
from aqui_brain_dump.note import fix_markdown_lists


class TestNoteRendering(unittest.TestCase):

    def test_wikilink_literature_cite(self):
        bib = {'dunford2019': {'title': 'Obviously Awesome'}}
        md = markdown.Markdown(extensions=[
            WikiLinkExtension(bibliography_data=bib),
            CitationExtension(bibliography_data=bib)
        ])

        html = md.convert('[[literature/@dunford2019|@dunford2019]]')
        self.assertIn('href="/literature/@dunford2019/"', html)
        self.assertIn('class="litnote tooltip"', html)
        self.assertIn('<span class="tooltiptext">Obviously Awesome</span>', html)
        self.assertNotIn('[[', html)
        self.assertNotIn(']]', html)

    def test_fix_markdown_lists(self):
        raw = "Header text:\n- Item 1\n- Item 2"
        processed = fix_markdown_lists(raw)
        self.assertEqual(processed, "Header text:\n\n- Item 1\n- Item 2")

        md = markdown.Markdown()
        html = md.convert(processed)
        self.assertIn('<p>Header text:</p>', html)
        self.assertIn('<ul>', html)
        self.assertIn('<li>Item 1</li>', html)


if __name__ == '__main__':
    unittest.main()
