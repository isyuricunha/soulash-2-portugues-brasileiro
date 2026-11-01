import unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from toolkit import Project
class Inventory(unittest.TestCase):
 def test_real_sources_and_batches(self):
  root=Path(__file__).resolve().parents[2];p=Project(root);p.integrity();m,rows,_,_=p.load()
  self.assertEqual(len(rows),29202);self.assertEqual(len(m['batches']),59)
  for b in m['batches'][:-1]:self.assertLessEqual(len((root/'translation-work/translations'/b).read_text(encoding='utf-8').splitlines()),500)
  # Translation progress may grow; the migrated text must not disappear.
  self.assertGreaterEqual(sum(bool(r['PTBR']) for r in rows),25138)
  self.assertFalse(any(r['source_file']=='messages.json' and r['pointer'][-1]=='align' for r in rows))
  self.assertFalse(any(r['source_file']=='messages.json' and r['pointer'][-1] in ('success','fail') and r['EN']=='none' for r in rows))
  self.assertTrue(all(not r['reviewed'] or bool(r['PTBR'].strip()) for r in rows))
