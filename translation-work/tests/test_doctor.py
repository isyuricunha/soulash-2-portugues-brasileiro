import unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_project import ProjectFlow
from native import Invalid
class Doctor(unittest.TestCase):
 setUp=ProjectFlow.setUp
 tearDown=ProjectFlow.tearDown
 write=ProjectFlow.write
 def test_readonly_and_arch(self):
  before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  self.p.doctor()
  after={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  self.assertEqual(before,after)
  with patch('platform.system',return_value='Windows'):
   with self.assertRaises(Invalid):self.p.doctor(arm64=True)
