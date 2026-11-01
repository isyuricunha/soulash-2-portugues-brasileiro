import unittest,json
from pathlib import Path,PurePosixPath
class ManifestPaths(unittest.TestCase):
 def test_all_sources_safe_and_present(self):
  root=Path(__file__).resolve().parents[2];m=json.loads((root/'translation-work/translations/manifest.json').read_text(encoding='utf-8'))
  for name in m['sources']:
   self.assertFalse(PurePosixPath(name).is_absolute());self.assertNotIn('..',PurePosixPath(name).parts)
   self.assertTrue((root/'EN/data/mods/core_2'/name).is_file())
  for row in m['catalog']:self.assertIn(row['source_file'],m['sources'])
