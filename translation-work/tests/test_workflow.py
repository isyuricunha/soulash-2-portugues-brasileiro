import unittest
from pathlib import Path
class Workflow(unittest.TestCase):
 def test_release_wiring(self):
  root=Path(__file__).resolve().parents[2];text=(root/'.github/workflows/auto-release.yml').read_text()
  for token in ['contents: write','concurrency:','PTBR/**','translation-work/build-manifest.json','toolkit.py verify-output','translation-work/release.py','secrets.GITHUB_TOKEN']:self.assertIn(token,text)
  self.assertNotIn('*.zip',text);self.assertNotIn('Nexus',text);self.assertNotIn('translations/**',text)
 def test_consent_wiring(self):
  root=Path(__file__).resolve().parents[2];text=(root/'.github/workflows/consent.yml').read_text()
  self.assertIn('pull_request:',text);self.assertIn('translation-work/consent.py',text)

 def test_toolkit_is_not_gitignored(self):
  import subprocess
  root=Path(__file__).resolve().parents[2]
  for relative in ['translation-work/toolkit.py','translation-work/native.py','translation-work/release.py','translation-work/tests/test_project.py']:
   result=subprocess.run(['git','-C',str(root),'check-ignore','-q',relative],capture_output=True)
   self.assertEqual(result.returncode,1,relative+' must be included in ordinary git add')
