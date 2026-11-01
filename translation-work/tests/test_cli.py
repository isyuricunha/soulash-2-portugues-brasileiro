import unittest,subprocess,sys
from pathlib import Path
class CLI(unittest.TestCase):
 def test_unsupported_dry_run_refused(self):
  root=Path(__file__).resolve().parents[2]
  result=subprocess.run([sys.executable,str(root/'translation-work/toolkit.py'),'build','--dry-run'],capture_output=True)
  self.assertNotEqual(result.returncode,0);self.assertIn(b'--dry-run',result.stderr)
 def test_help_outside_repository(self):
  import tempfile
  root=Path(__file__).resolve().parents[2]
  with tempfile.TemporaryDirectory() as d:
   result=subprocess.run([sys.executable,str(root/'translation-work/toolkit.py'),'--help'],cwd=d,capture_output=True)
  self.assertEqual(result.returncode,0);self.assertIn(b'export-payload',result.stdout)
