import unittest,sys,json,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_project
from toolkit import WORK,MANIFEST,lines_bytes
from storage import json_bytes
import native
class Scale(unittest.TestCase):
 setUp=test_project.ProjectFlow.setUp
 tearDown=test_project.ProjectFlow.tearDown
 write=test_project.ProjectFlow.write
 def test_500_apply_across_101_batches(self):
  self.write({f'key{i}':f'Entry {i}' for i in range(505)})
  self.p.sync(self.src,'0.10.5')
  m,rows,_,_=self.p.load();folder=self.root/WORK/'translations'
  for file in folder.glob('batch-*.jsonl'):file.unlink()
  m['batches']=[]
  for i in range(101):
   name=f'batch-{i+1:04}.jsonl';m['batches'].append(name);(folder/name).write_bytes(lines_bytes(rows[i*5:i*5+5]))
  (self.root/MANIFEST).write_bytes(json_bytes(m))
  last=folder/m['batches'][-1];untouched=last.stat().st_mtime_ns
  for i in range(500):
   r=rows[(i%100)*5]
   result=self.p.apply({'generation':m['generation'],'expected_count':1,'entries':[{'id':r['id'],'source_fingerprint':native.fingerprint(r),'PTBR':r['EN']+('!'*(i//100+1))}]},replace=True)
   self.assertEqual(len(result['changed_batches']),1)
   latest=self.p.store.receipts()[-1][1]
   self.assertEqual(len(latest['files']),1)
   self.assertTrue(latest['files'][0]['path'].endswith(result['changed_batches'][0]))
   stats=self.p.store.stats();self.assertLessEqual(stats['completed'],10);self.assertLessEqual(stats['bytes'],stats['retention_bytes'])
   if i%100==0:print('apply progress',i,flush=True)
  self.assertEqual(last.stat().st_mtime_ns,untouched)
  _,current,_,_=self.p.load();self.assertEqual(len(current),505)
