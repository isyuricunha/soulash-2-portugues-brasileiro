import unittest,re
from pathlib import Path
class Documents(unittest.TestCase):
 def test_public_contract(self):
  root=Path(__file__).resolve().parents[2];text=(root/'README.md').read_text(encoding='utf-8')
  for needle in ['header.jpg','/releases','PTBR.zip','data/mods/ptbr','uFEwSMwUYb','pix@yuricunha.com','CONTRIBUTING.md','GAME-DEVELOPER-PERMISSION.md','./LICENSE']:self.assertIn(needle,text)
  for needle in ['100%','Ella','Sayuri','Codex','ChatGPT','JSONL','batch-']:self.assertNotIn(needle,text)
  self.assertLessEqual(text.count('img.shields.io'),5)
  legal=(root/'LICENSE').read_text(encoding='utf-8');self.assertGreater(len(legal),18000);self.assertIn('Attribution-NonCommercial-ShareAlike 4.0 International',legal)
 def test_no_persona_in_authored_docs(self):
  root=Path(__file__).resolve().parents[1]
  for p in list((root/'docs').glob('*.md'))+[root/'README.md']:
   self.assertIsNone(re.search(r'\b(Ella|Sayuri|Codex|ChatGPT)\b',p.read_text(encoding='utf-8')),str(p))

 def test_release_text_encoding(self):
  root=Path(__file__).resolve().parents[1];text=(root/'release.py').read_text(encoding='utf-8')
  self.assertNotIn('\u00c3',text);self.assertIn('instala\u00e7\u00e3o',text);self.assertIn('Di\u00e1logos',text)

 def test_cli_explicit_utf8(self):
  root=Path(__file__).resolve().parents[1];text=(root/'toolkit.py').read_text(encoding='utf-8')
  self.assertIn("sys.stdout.reconfigure(encoding='utf-8')",text)

 def test_all_active_modules_utf8(self):
  root=Path(__file__).resolve().parents[1]
  for name in ['toolkit.py','native.py','release.py']:
   self.assertNotIn(chr(195),(root/name).read_text(encoding='utf-8'),name)
