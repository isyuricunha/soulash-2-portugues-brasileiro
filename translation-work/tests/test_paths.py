import unittest,tempfile,sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage import safe
from native import Invalid
class Paths(unittest.TestCase):
 def test_escapes(self):
  with tempfile.TemporaryDirectory() as d:
   for rel in ['../outside','/absolute','C:/outside','a/../b','a\\b']:
    with self.assertRaises(Invalid):safe(d,rel)
 def test_link(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'target').mkdir()
   try:(root/'link').symlink_to(root/'target',target_is_directory=True)
   except OSError:self.skipTest('Symlink privilege unavailable')
   with self.assertRaises(Invalid):safe(root,'link/file')

 def test_symlink_attribute_guard(self):
  from unittest.mock import patch
  from types import SimpleNamespace
  import stat
  with tempfile.TemporaryDirectory() as d:
   original=Path.lstat
   def fake(path,*args,**kwargs):
    if path.name=='link':return SimpleNamespace(st_mode=stat.S_IFLNK,st_file_attributes=0)
    return original(path,*args,**kwargs)
   with patch.object(Path,'lstat',fake):
    with self.assertRaises(Invalid):safe(d,'link/file')
