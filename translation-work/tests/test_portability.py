import unittest,tempfile,subprocess,sys,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from toolkit import Project
from storage import sha,canonical,json_bytes
from native import Invalid
class Portability(unittest.TestCase):
 def test_git_index_normalization_and_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);w=root/'translation-work';w.mkdir()
   subprocess.run(['git','init','-q',d],check=True)
   (root/'.gitattributes').write_bytes(b'*.json text eol=lf\n*.bin -text\n')
   metadata=b'{"schema":1}\r\n';binary=b'opaque\r\n'
   (w/'metadata.json').write_bytes(metadata);(w/'native.bin').write_bytes(binary)
   spec={'files':{'translation-work/metadata.json':{'mode':'git-lf','sha256':sha(canonical(metadata))},'translation-work/native.bin':{'mode':'binary','sha256':sha(binary)}}}
   (w/'toolchain.json').write_bytes(json_bytes(spec));(w/'runtime-support.json').write_bytes(json_bytes({'toolchain_sha256':sha(json_bytes(spec))}))
   subprocess.run(['git','-C',d,'add','.'],check=True,capture_output=True)
   blob=subprocess.check_output(['git','-C',d,'show',':translation-work/metadata.json'])
   self.assertEqual(blob,b'{"schema":1}\n');Project(root).integrity()
   (w/'metadata.json').write_bytes(blob);Project(root).integrity()
   (w/'native.bin').write_bytes(b'opaque\n')
   with self.assertRaises(Invalid):Project(root).integrity()
   (w/'native.bin').write_bytes(binary);(w/'metadata.json').write_bytes(b'{"schema":2}\n')
   with self.assertRaises(Invalid):Project(root).integrity()

 def test_nested_metadata_link(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);w=root/'translation-work';w.mkdir()
   shape=b'{"format":"soulash-json"}\r\n';(w/'engine-shapes.json').write_bytes(shape)
   spec={'files':{'translation-work/engine-shapes.json':{'mode':'git-lf','sha256':sha(canonical(shape))}}}
   (w/'toolchain.json').write_bytes(json_bytes(spec));(w/'runtime-support.json').write_bytes(json_bytes({'toolchain_sha256':sha(json_bytes(spec))}))
   Project(root).integrity();(w/'engine-shapes.json').write_bytes(canonical(shape));Project(root).integrity()
   (w/'engine-shapes.json').write_bytes(b'{"format":"changed"}\n')
   with self.assertRaises(Invalid):Project(root).integrity()
