import unittest,ast
from pathlib import Path
class Offline(unittest.TestCase):
 def test_active_translation_path_has_no_provider(self):
  root=Path(__file__).resolve().parents[1]
  for name in ['toolkit.py','native.py','extractor.py','protection.py','storage.py']:
   tree=ast.parse((root/name).read_text(encoding='utf-8'))
   imports=[]
   for node in ast.walk(tree):
    if isinstance(node,ast.Import):imports.extend(a.name for a in node.names)
    if isinstance(node,ast.ImportFrom):imports.append(node.module or '')
   self.assertFalse(any(v.startswith(('openai','requests','httpx','urllib','provider')) for v in imports),name)
