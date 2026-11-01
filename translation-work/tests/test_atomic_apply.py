import unittest,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_project,native
from toolkit import WORK
class AtomicApply(unittest.TestCase):
 setUp=test_project.ProjectFlow.setUp
 tearDown=test_project.ProjectFlow.tearDown
 write=test_project.ProjectFlow.write
 def test_receipt_only_dirty_batch(self):
  m,rows,_,_=self.p.load();r=rows[0]
  result=self.p.apply({'generation':m['generation'],'expected_count':1,'entries':[{'id':r['id'],'source_fingerprint':native.fingerprint(r),'PTBR':r['EN']}]})
  receipt=self.p.store.receipts()[-1][1]
  self.assertEqual([v['path'] for v in receipt['files']],[WORK+'translations/'+result['changed_batches'][0]])
