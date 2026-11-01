import unittest,tempfile,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native
class NativeContext(unittest.TestCase):
 def test_selectors_preserved_without_inference(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'language_metadata.json').write_bytes(native.encoded({'id':'en','name':'English'}))
   source={'conversations':[{'id':'speaker_example','npc_sex':2,'player_sex':1,'answer_positive':'He is tired.','text':'I am ready.'}]}
   (p/'conversations.json').write_bytes(native.encoded(source));files,rows=native.extract(p)
   for r in rows:
    self.assertIn('npc_sex',str(r['context']));self.assertIsNone(r['gender']);r.update(PTBR=r['EN'],reviewed=True)
   rebuilt=native.rebuild(files,rows,'0.10.5');data=json.loads(rebuilt[native.DEPLOY+'/translations/ptbr/conversations.json'])
   self.assertEqual(data,source)
 def test_duplicate_native_key(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'language_metadata.json').write_bytes(native.encoded({'id':'en','name':'English'}));(p/'messages.json').write_bytes(b'{"a":"one","a":"two"}')
   with self.assertRaises(Exception):native.extract(p)
 def test_reorder_identity(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'language_metadata.json').write_bytes(native.encoded({'id':'en','name':'English'}))
   items=[{'id':'a','text':'First'},{'id':'b','text':'Second'}]
   (p/'conversations.json').write_bytes(native.encoded({'conversations':items}));_,before=native.extract(p)
   (p/'conversations.json').write_bytes(native.encoded({'conversations':items[::-1]}));_,after=native.extract(p)
   self.assertEqual({r['id'] for r in before},{r['id'] for r in after})
   self.assertEqual({r['id']:native.fingerprint(r) for r in before},{r['id']:native.fingerprint(r) for r in after})

 def test_language_label(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'language_metadata.json').write_bytes(native.encoded({'id':'en','name':'English'}))
   files,rows=native.extract(p);out=native.rebuild(files,rows,'0.10.5')
   label=json.loads(out[native.DEPLOY+'/language_metadata.json'])['name']
   self.assertEqual(label,'Portugu\u00eas Brasileiro')

 def test_entity_gender_and_affix(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'entities').mkdir();(p/'language_metadata.json').write_bytes(native.encoded({'id':'en','name':'English'}))
   (p/'entities/1.json').write_bytes(native.encoded({'id':1,'name':'Sword','resource':{'affix':'Iron'},'damage':5}))
   files,rows=native.extract(p)
   for r in rows:r.update(PTBR=r['EN'],reviewed=True,gender='feminine' if r['gender_eligible'] else None)
   out=native.rebuild(files,rows,'0.10.5');entity=json.loads(out[native.DEPLOY+'/translations/ptbr/entities/1.json'])
   self.assertTrue(entity['feminine_form']);self.assertEqual(entity['damage'],5);self.assertEqual(entity['resource']['feminine_affix'],'Iron')

 def test_alignment_is_native_metadata_not_translation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'language_metadata.json').write_bytes(native.encoded({'id':'en','name':'English'}))
   (p/'messages.json').write_bytes(native.encoded({'main':[{'id':1,'format':'Hello','align':'middle'}]}))
   files,rows=native.extract(p);self.assertEqual([r['EN'] for r in rows],['Hello'])
   for r in rows:r.update(PTBR='Oi',reviewed=True)
   output=native.rebuild(files,rows,'0.10.5');self.assertEqual(json.loads(output[native.DEPLOY+'/translations/ptbr/messages.json'])['main'][0]['align'],'middle')

 def test_ability_none_sentinels_stay_native(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'language_metadata.json').write_bytes(native.encoded({'id':'en','name':'English'}))
   data={'ability':[{'id':116,'effect':'Restrict To Tag','success':'none','fail':'none'}]}
   (p/'messages.json').write_bytes(native.encoded(data));files,rows=native.extract(p)
   self.assertEqual([r['EN'] for r in rows],['Restrict To Tag'])
   for r in rows:r.update(PTBR='Restringir à Etiqueta',reviewed=True)
   out=native.rebuild(files,rows,'0.10.5');rebuilt=json.loads(out[native.DEPLOY+'/translations/ptbr/messages.json'])
   self.assertEqual(rebuilt['ability'][0]['success'],'none');self.assertEqual(rebuilt['ability'][0]['fail'],'none')
