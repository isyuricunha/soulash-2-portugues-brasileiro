import sys,tempfile,unittest,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from toolkit import Project,MANIFEST,WORK,BUILD
from storage import json_bytes,sha,canonical
import native
class ProjectFlow(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.p=Project(self.root)
  source=Path(__file__).resolve().parents[1]
  for name in ['toolkit.py','native.py','extractor.py','models.py','protection.py','storage.py','errors.py','release.py','consent.py','toolchain.json','runtime-support.json','legacy-releases.json','source-profiles.json']:
   dest=self.root/WORK/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,dest)
  self.src=self.root/'fixture';self.src.mkdir()
  (self.src/'language_metadata.json').write_bytes(native.encoded({'id':'en','name':'English'}))
  self.write({'greeting':'Hello ::name','other':'Welcome'})
  self.p.sync(self.src,'0.10.5',initial=True)
 def tearDown(self):self.tmp.cleanup()
 def write(self,value):(self.src/'messages.json').write_bytes(native.encoded(value))
 def apply_all(self):
  m,rows,_,_=self.p.load()
  return self.p.apply({'generation':m['generation'],'expected_count':len(rows),'entries':[{'id':r['id'],'source_fingerprint':native.fingerprint(r),'PTBR':r['EN'],'reviewed':True} for r in rows]})
 def test_complete_build_gate(self):
  with self.assertRaises(native.Invalid):self.p.build()
  self.assertFalse((self.root/'PTBR').exists())
  self.apply_all();receipt=self.p.build();self.p.verify_output()
  import zipfile
  with zipfile.ZipFile(self.p.package()['zip']) as z:self.assertEqual(set(z.namelist()),set(receipt['outputs']))
  out=self.root/'PTBR'/next(iter(receipt['outputs']));out.write_bytes(b'tamper')
  with self.assertRaises(native.Invalid):self.p.verify_output()
 def test_incremental_sync(self):
  self.apply_all();self.write({'greeting':'Goodbye ::name','other':'Welcome','new':'New'})
  report=self.p.sync(self.src,'0.10.5');self.assertEqual(report['counts']['modified'],1)
  _,rows,_,_=self.p.load();values={r['EN']:r['PTBR'] for r in rows}
  self.assertEqual(values['Welcome'],'Welcome');self.assertEqual(values['Goodbye ::name'],'')
  self.assertEqual(self.p.sync(self.src,'0.10.5')['status'],'unchanged')
 def test_stale_apply_and_dry_run(self):
  before=(self.root/MANIFEST).read_bytes();self.write({'greeting':'Changed','other':'Welcome'})
  self.p.sync(self.src,'0.10.5',dry=True);self.assertEqual(before,(self.root/MANIFEST).read_bytes())
  with self.assertRaises(native.Invalid):self.p.apply({'generation':'wrong','expected_count':0,'entries':[]})
 def test_source_tamper(self):
  self.apply_all();self.p.build()
  (self.root/'EN'/native.SOURCE/'messages.json').write_bytes(b'{}')
  with self.assertRaises(native.Invalid):self.p.verify_output()

 def test_duplicate_and_unknown_payload(self):
  m,rows,_,_=self.p.load();r=rows[0];entry={'id':r['id'],'source_fingerprint':native.fingerprint(r),'PTBR':r['EN']}
  with self.assertRaises(native.Invalid):self.p.apply({'generation':m['generation'],'expected_count':2,'entries':[entry,entry]})
  bad=dict(entry,id='unknown');result=self.p.apply({'generation':m['generation'],'expected_count':2,'entries':[entry,bad]})
  self.assertEqual(len(result['accepted']),1);self.assertEqual(len(result['rejected']),1)
 def test_incomplete_source_refused(self):
  (self.src/'messages.json').unlink()
  with self.assertRaises(native.Invalid):self.p.sync(self.src,'0.10.5')
 def test_forged_complete_flag(self):
  self.apply_all();self.p.build();m,rows,_,_=self.p.load()
  batch=self.root/WORK/'translations'/m['batches'][0]
  rs=[json.loads(line) for line in batch.read_text(encoding='utf-8').splitlines()];rs[0]['reviewed']=False
  batch.write_text(''.join(json.dumps(r)+'\n' for r in rs),encoding='utf-8')
  with self.assertRaises(native.Invalid):self.p.verify_output()

 def test_overwritten_en_sync(self):
  self.apply_all();en=self.root/'EN'/native.SOURCE
  (en/'messages.json').write_bytes(native.encoded({'greeting':'Changed ::name','other':'Welcome'}))
  result=self.p.sync(en,'0.10.5');self.assertEqual(result['counts']['modified'],1)
  _,rows,_,_=self.p.load();self.assertEqual(next(r for r in rows if r['EN']=='Welcome')['PTBR'],'Welcome')
 def test_batch_sizes_and_noop(self):
  self.write({f'key{i}':f'Text {i}' for i in range(1001)});self.p.sync(self.src,'0.10.5')
  m,rows,_,_=self.p.load();self.assertTrue(all(sum(1 for _ in (self.root/WORK/'translations'/b).read_text().splitlines())<=500 for b in m['batches']))
  before={b:(self.root/WORK/'translations'/b).stat().st_mtime_ns for b in m['batches']}
  self.p.sync(self.src,'0.10.5')
  self.assertEqual(before,{b:(self.root/WORK/'translations'/b).stat().st_mtime_ns for b in m['batches']})

 def test_unaccepted_new_source_stales_output(self):
  self.apply_all();self.p.build()
  (self.root/'EN'/native.SOURCE/'skills.json').write_bytes(native.encoded({'name':'New source'}))
  with self.assertRaises(native.Invalid):self.p.verify_output()
 def test_overwrite_guard(self):
  self.apply_all();m,rows,_,_=self.p.load();r=rows[0]
  result=self.p.apply({'generation':m['generation'],'expected_count':1,'entries':[{'id':r['id'],'source_fingerprint':native.fingerprint(r),'PTBR':r['EN']+'!'}]})
  self.assertEqual(len(result['rejected']),1)

 def test_incomplete_rebuild_preserves_previous_output(self):
  self.apply_all();receipt=self.p.build();before={str(p.relative_to(self.root)):p.read_bytes() for p in (self.root/'PTBR').rglob('*') if p.is_file()}
  self.write({'greeting':'Changed ::name','other':'Welcome'});self.p.sync(self.src,'0.10.5')
  with self.assertRaises(native.Invalid):self.p.build()
  self.assertEqual(before,{str(p.relative_to(self.root)):p.read_bytes() for p in (self.root/'PTBR').rglob('*') if p.is_file()})

 def test_modified_translation_history(self):
  self.apply_all();m,rows,_,_=self.p.load();old_generation=m['generation']
  self.write({'greeting':'Changed ::name','other':'Welcome'});self.p.sync(self.src,'0.10.5')
  history=json.loads((self.root/WORK/'history'/(old_generation+'.json')).read_text(encoding='utf-8'))
  changed=history['changed_translations'];self.assertTrue(any(v['previous']['PTBR']=='Hello ::name' for v in changed))

 def test_removed_record_history(self):
  self.apply_all();self.write({'greeting':'Hello ::name'});report=self.p.sync(self.src,'0.10.5')
  self.assertEqual(report['counts']['removed'],1)
  _,rows,_,_=self.p.load();self.assertEqual(len(rows),1)
 def test_new_file_does_not_invalidate_existing(self):
  self.apply_all();(self.src/'skills.json').write_bytes(native.encoded({'name':'New skill'}));report=self.p.sync(self.src,'0.10.5')
  self.assertEqual(report['counts']['added'],1);self.assertEqual(report['counts']['preserved_translations'],2)

 def test_immutable_field_edit_refused(self):
  m,rows,_,_=self.p.load();batch=self.root/WORK/'translations'/m['batches'][0]
  rows[0]['EN']='tampered';batch.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
  with self.assertRaises(native.Invalid):self.p.load()
 def test_duplicate_record_refused(self):
  m,rows,_,_=self.p.load();batch=self.root/WORK/'translations'/m['batches'][0]
  batch.write_text(''.join(json.dumps(r)+'\n' for r in rows+[rows[0]]),encoding='utf-8')
  with self.assertRaises(native.Invalid):self.p.load()

 def test_apply_noop_preserves_batch(self):
  m,rows,_,_=self.p.load();r=rows[0];payload={'generation':m['generation'],'expected_count':1,'entries':[{'id':r['id'],'source_fingerprint':native.fingerprint(r),'PTBR':r['EN']}]}
  first=self.p.apply(payload);batch=self.root/WORK/'translations'/first['changed_batches'][0];stamp=batch.stat().st_mtime_ns
  second=self.p.apply(payload);self.assertIsNone(second['transaction']);self.assertEqual(batch.stat().st_mtime_ns,stamp)

 def test_source_sync_invalidates_old_reference(self):
  ref=self.root/WORK/'reference/conversation-context.json';ref.parent.mkdir(parents=True,exist_ok=True)
  ref.write_text(json.dumps({'schema':1,'generation':'old','conversations':[]}),encoding='utf-8')
  self.write({'greeting':'Changed ::name','other':'Welcome'});self.p.sync(self.src,'0.10.5')
  current=json.loads(ref.read_text(encoding='utf-8'));self.assertEqual(current['status'],'invalidated-by-source-sync')
  self.assertNotIn('previous_reference',current)

 def test_reordered_conversation_preserves_reviewed_translation(self):
  path=self.src/'conversations.json';items=[{'id':'a','text':'First'},{'id':'b','text':'Second'}]
  path.write_bytes(native.encoded({'conversations':items}));self.p.sync(self.src,'0.10.5');self.apply_all()
  path.write_bytes(native.encoded({'conversations':items[::-1]}));result=self.p.sync(self.src,'0.10.5')
  self.assertEqual(result['counts']['modified'],0);self.assertEqual(result['counts']['moved'],2)
  _,rows,_,_=self.p.load();self.assertTrue(all(r['reviewed'] and r['PTBR'] for r in rows))

 def test_previous_catalog_reconstructed_from_delta(self):
  self.apply_all();old,prior,_,_=self.p.load()
  self.write({'greeting':'Changed ::name','new':'Added'});self.p.sync(self.src,'0.10.5')
  _,current,_,_=self.p.load();history=json.loads((self.root/WORK/'history'/(old['generation']+'.json')).read_text(encoding='utf-8'))
  restored={r['id']:r for r in current if r['id'] not in history['added_ids']}
  for change in history['changed_translations']:restored[change['previous']['id']]=change['previous']
  self.assertEqual(restored,{r['id']:r for r in prior})
