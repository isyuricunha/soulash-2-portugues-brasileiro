import unittest
import native


class PreviewTest(unittest.TestCase):
    def row(self, text):
        return {'id': 'test', 'PTBR': text, 'EN': 'Hello', 'reviewed': False,
                'gender': None, 'gender_eligible': False, 'source_file': 'messages.json',
                'pointer': ['greeting'], 'destination': ['greeting']}

    def test_preview_preserves_review_status_and_final_gate(self):
        row = self.row('Olá')
        files = {'messages.json': b'{"greeting":"Hello"}'}
        output = native.rebuild(files, [row], '0.10.5', require_review=False)
        self.assertIn(native.DEPLOY+'/translations/ptbr/messages.json', output)
        self.assertFalse(row['reviewed'])
        with self.assertRaises(native.Invalid):
            native.rebuild(files, [row], '0.10.5')

    def test_preview_rejects_empty_text(self):
        with self.assertRaises(native.Invalid):
            native.rebuild({}, [self.row('')], '0.10.5', require_review=False)
