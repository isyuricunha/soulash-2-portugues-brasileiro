import unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from toolkit import Project
class Inventory(unittest.TestCase):
 def test_real_sources_and_batches(self):
  root=Path(__file__).resolve().parents[2];p=Project(root);p.integrity();m,rows,_,_=p.load()
  self.assertEqual(len(rows),29434);self.assertEqual(len(m['batches']),59)
  for b in m['batches'][:-1]:self.assertEqual(len((root/'translation-work/translations'/b).read_text(encoding='utf-8').splitlines()),500)
  self.assertEqual(sum(bool(r['PTBR']) for r in rows),25249)
  self.assertTrue(all(not r['reviewed'] for r in rows))
