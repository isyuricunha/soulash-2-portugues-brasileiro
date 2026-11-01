import sys, tempfile, unittest, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native
from storage import Store, durable, sha, canonical

class Contract(unittest.TestCase):
 def test_native_fixture(self): self.assertIn('passed',native.smoke())
 def test_tokens(self):
  native.validate_text('Hello ::name','Olá ::name')
  with self.assertRaises(native.Invalid):native.validate_text('Hello ::name','Olá')
 def test_crash_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=Store(root);durable(root/'a',b'old')
   with self.assertRaises(native.Invalid):s.commit({'a':b'new','b':b'other'},crash_after=1)
   with self.assertRaises(native.Invalid):s.gc()
   s.recover();self.assertEqual((root/'a').read_bytes(),b'old');self.assertFalse((root/'b').exists())
 def test_small_updates_retention(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=Store(root,count=10,budget=1024*1024)
   for i in range(101):durable(root/f'batch-{i:04}.jsonl',b'original')
   untouched=(root/'batch-0100.jsonl').stat().st_mtime_ns
   for i in range(500):s.commit({f'batch-{i%100:04}.jsonl':str(i).encode()})
   self.assertLessEqual(s.stats()['completed'],10)
   self.assertLess(s.stats()['bytes'],1024*1024)
   self.assertEqual((root/'batch-0100.jsonl').stat().st_mtime_ns,untouched)
 def test_normalization(self):
  self.assertEqual(sha(canonical(b'{"a":1}\r\n')),sha(b'{"a":1}\n'))
  self.assertNotEqual(sha(canonical(b'{"a":2}\r\n')),sha(b'{"a":1}\n'))

 def test_markup_and_numbers(self):
  native.validate_text('[color=1,2,3,4]Damage 5[/color]','[color=1,2,3,4]Dano 5[/color]')
  for target in ['Dano 5','[color=1,2,3,4]Dano 6[/color]','[color=1,2,3,4]Dano 5']:
   with self.assertRaises(native.Invalid):native.validate_text('[color=1,2,3,4]Damage 5[/color]',target)
