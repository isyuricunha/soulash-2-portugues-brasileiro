import unittest,json,zipfile,hashlib,subprocess
from pathlib import Path
class Migration(unittest.TestCase):
 def test_preserved_archive(self):
  root=Path(__file__).resolve().parents[1]/'reference';m=json.loads((root/'private-worktree-manifest.json').read_text(encoding='utf-8'))
  with zipfile.ZipFile(root/'private-worktree.zip') as z:
   self.assertEqual(set(z.namelist()),set(m))
   for name,digest in m.items():self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest,name)
 def test_history_bundle(self):
  root=Path(__file__).resolve().parents[2]
  p=subprocess.run(['git','-C',str(root),'bundle','verify',str(root/'translation-work/reference/private-history.bundle')],capture_output=True)
  self.assertEqual(p.returncode,0,p.stderr.decode(errors='replace'))
