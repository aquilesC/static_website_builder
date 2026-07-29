import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import tempfile
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from aqui_brain_dump import datetimeformat


class TestSitemapAndRSS(unittest.TestCase):

    def setUp(self):
        self.template_dir = Path(__file__).parent.parent / 'aqui_brain_dump'
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['xml', 'rss', 'html']),
        )
        self.env.filters['datetime'] = datetimeformat

        class DummyNote:
            def __init__(self, url, title, description, content, edits=1):
                self.url = url
                self.title = title
                self.description = description
                self.content = content
                self.number_edits = edits
                self.last_mod = None
                self.creation_date = None

        self.notes = {
            'note_with_ampersand': DummyNote(
                url='scipreneurs/Playbook/10_-_resource_&_capital_strategy/',
                title='Resource & Capital Strategy',
                description='Notes on R&D & capital funding',
                content='<p>Section 1 & Section 2</p>',
            ),
            'normal_note': DummyNote(
                url='regular/note/',
                title='Regular Note',
                description='Simple description',
                content='<p>Simple content</p>',
            )
        }

    def test_sitemap_xml_validity_with_ampersands(self):
        sitemap_template = self.env.get_template('sitemap.xml')
        rendered = sitemap_template.render({
            'notes': self.notes,
            'min_edits': 1,
            'max_edits': 10,
            'network_priorities': {},
            'today': '2026-07-29',
            'base_url': 'https://notes.aquiles.me/'
        })

        # Must parse without XML parsing error
        try:
            root = ET.fromstring(rendered)
        except ET.ParseError as e:
            self.fail(f"sitemap.xml is not well-formed XML: {e}\nRendered content:\n{rendered}")

        # Ensure the URL with & was properly escaped to &amp; in <loc>
        self.assertIn('https://notes.aquiles.me/scipreneurs/Playbook/10_-_resource_&amp;_capital_strategy/', rendered)
        self.assertNotIn('10_-_resource_&_capital_strategy/', rendered)

    def test_feed_rss_validity_with_ampersands(self):
        rss_template = self.env.get_template('feed.rss')
        rendered = rss_template.render({
            'notes': self.notes,
            'today': 'Wed, 29 Jul 2026 12:00:00 +0000',
            'base_url': 'https://notes.aquiles.me/'
        })

        # Must parse without XML parsing error
        try:
            root = ET.fromstring(rendered)
        except ET.ParseError as e:
            self.fail(f"feed.rss is not well-formed XML: {e}\nRendered content:\n{rendered}")

        # Check escaped elements
        self.assertIn('Resource &amp; Capital Strategy', rendered)
        self.assertIn('Notes on R&amp;D &amp; capital funding', rendered)


if __name__ == '__main__':
    unittest.main()
