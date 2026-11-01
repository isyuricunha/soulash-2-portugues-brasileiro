import unittest,re
from pathlib import Path

def invalid(text):
 return bool(re.search(r'\b(Ella|Sayuri|Codex|ChatGPT)\b',text) or re.search(r'Yuri (?:traduziu|testou|concluiu)',text,re.I))
class Copy(unittest.TestCase):
 def test_negative_fixtures(self):
  self.assertTrue(invalid('Tradução por Ella'));self.assertTrue(invalid('Yuri testou tudo'))
  self.assertFalse(invalid('Coordenação e manutenção: Yuri Cunha.'))
 def test_current_public_copy(self):
  root=Path(__file__).resolve().parents[2];self.assertFalse(invalid((root/'README.md').read_text(encoding='utf-8')))
