import unittest
import tempfile
import shutil
from pathlib import Path

import markdown

from aqui_brain_dump.util import is_private_path
from aqui_brain_dump.note import Note
from aqui_brain_dump.backlinks_wikilinks import WikiLinkExtension


class TestPrivateNotes(unittest.TestCase):

    def test_is_private_path(self):
        self.assertTrue(is_private_path('_private'))
        self.assertTrue(is_private_path('_private/note.md'))
        self.assertTrue(is_private_path('content/_private/secret.md'))
        self.assertTrue(is_private_path('literature/_private/paper.md'))
        self.assertTrue(is_private_path('/literature/_private/paper/'))
        self.assertTrue(is_private_path(Path('essays/_private/draft.md')))

        self.assertFalse(is_private_path('content/public/note.md'))
        self.assertFalse(is_private_path('content/not_private/note.md'))
        self.assertFalse(is_private_path(''))
        self.assertFalse(is_private_path(None))

    def test_note_creation_skips_private(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            private_file = tmp_path / '_private' / 'secret.md'
            private_file.parent.mkdir(parents=True, exist_ok=True)
            private_file.write_text('# Secret Note\nThis is private.', encoding='utf-8')

            note = Note.create_from_path(private_file)
            self.assertIsNone(note)

            url_note = Note.create_from_url('/_private/secret/')
            self.assertIsNone(url_note)

    def test_wikilinks_neglect_private(self):
        md = markdown.Markdown(extensions=[WikiLinkExtension()])

        # Public link
        html_public = md.convert('[[public_note]]')
        self.assertIn('href="/public_note/"', html_public)
        self.assertIn('/public_note/', md.links)

        # Private links
        md.reset()
        html_private = md.convert('[[_private/test_private]]')
        self.assertNotIn('href=', html_private)
        self.assertNotIn('/_private/test_private/', md.links)
        self.assertEqual(html_private, '<p>test_private</p>')

        md.reset()
        html_nested_private = md.convert('[[literature/_private/test private|test private]]')
        self.assertNotIn('href=', html_nested_private)
        self.assertNotIn('/literature/_private/test_private/', md.links)
        self.assertEqual(html_nested_private, '<p>test private</p>')



    def test_build_backlinks_ignores_private(self):
        # Reset Note class state
        Note.notes = {}
        Note.futures_executor = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            content_dir = Path(tmp_dir) / 'content'
            content_dir.mkdir()

            # Create a public note
            public_file = content_dir / 'public.md'
            public_file.write_text('# Public\nLink to [[target]] and [[_private/secret]].', encoding='utf-8')

            target_file = content_dir / 'target.md'
            target_file.write_text('# Target\nContent here.', encoding='utf-8')

            # Mock content_path in note module temporarily
            import aqui_brain_dump.note as note_mod
            orig_content_path = note_mod.content_path
            note_mod.content_path = content_dir
            try:
                n1 = Note.create_from_path(public_file)
                n2 = Note.create_from_path(target_file)

                Note.build_backlinks()

                # Verify target receives backlink from public
                self.assertIn(n1, n2.backlinks)

                # Verify no note or backlink exists for _private/secret
                self.assertNotIn('/_private/secret/', Note.notes)
            finally:
                note_mod.content_path = orig_content_path
                Note.notes = {}


if __name__ == '__main__':
    unittest.main()
