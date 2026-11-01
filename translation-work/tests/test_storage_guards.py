import unittest,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage import Store,durable
from native import Invalid
class StorageGuards(unittest.TestCase):
 def test_gc_dry_and_corrupt_receipt(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=Store(root,count=2)
   for i in range(4):s.commit({'a':str(i).encode()})
   before={str(p):p.read_bytes() for p in s.txns.rglob('*') if p.is_file()};s.gc(dry=True)
   self.assertEqual(before,{str(p):p.read_bytes() for p in s.txns.rglob('*') if p.is_file()})
   folder=next(s.txns.iterdir());(folder/'receipt.sha256').write_text('bad')
   with self.assertRaises(Invalid):s.gc()
 def test_concurrent_edit_and_budget(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=Store(root,budget=20000);durable(root/'a',b'editor')
   with self.assertRaises(Invalid):s.commit({'a':b'new'},{'a':'wrong'})
   self.assertEqual((root/'a').read_bytes(),b'editor')
   with self.assertRaises(Invalid):s.commit({'a':b'x'*25000})
   self.assertEqual((root/'a').read_bytes(),b'editor')
 def test_rollback(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=Store(root);durable(root/'a',b'old');s.commit({'a':b'new'});s.rollback()
   self.assertEqual((root/'a').read_bytes(),b'old')

 def test_recovery_refuses_external_edit(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=Store(root);durable(root/'a',b'old');durable(root/'b',b'old')
   with self.assertRaises(Invalid):s.commit({'a':b'new','b':b'new'},crash_after=1)
   durable(root/'a',b'external')
   with self.assertRaises(Invalid):s.recover()
   self.assertEqual((root/'a').read_bytes(),b'external');self.assertEqual((root/'b').read_bytes(),b'old')
 def test_lock_exclusion(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(d)
   with s.lock():
    with self.assertRaises(Invalid):
     with s.lock():pass

 def test_each_promotion_boundary(self):
  for boundary in (1,2,3):
   with self.subTest(boundary=boundary),tempfile.TemporaryDirectory() as d:
    root=Path(d);s=Store(root)
    for name in ('a','b','c'):durable(root/name,b'original')
    with self.assertRaises(Invalid):s.commit({name:b'changed' for name in ('a','b','c')},crash_after=boundary)
    s.recover()
    self.assertTrue(all((root/name).read_bytes()==b'original' for name in ('a','b','c')))
 def test_staging_failure_preserves_live(self):
  from unittest.mock import patch
  import storage
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=Store(root);durable(root/'a',b'original');real=storage.durable
   def failing(path,data):
    if path.name.startswith('after-'):raise OSError('fixture staging failure')
    return real(path,data)
   with patch('storage.durable',side_effect=failing):
    with self.assertRaises(OSError):s.commit({'a':b'changed'})
   self.assertEqual((root/'a').read_bytes(),b'original');s.recover();self.assertEqual((root/'a').read_bytes(),b'original')

 def test_rollback_crash_is_recoverable(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=Store(root);durable(root/'a',b'old');durable(root/'b',b'old');s.commit({'a':b'new','b':b'new'})
   real=s.commit
   def interrupted(changes,expected=None,operation='apply',**kwargs):return real(changes,expected,operation=operation,crash_after=1)
   with patch.object(s,'commit',side_effect=interrupted):
    with self.assertRaises(Invalid):s.rollback()
   with self.assertRaises(Invalid):s.gc()
   s.recover();self.assertEqual((root/'a').read_bytes(),b'new');self.assertEqual((root/'b').read_bytes(),b'new')
