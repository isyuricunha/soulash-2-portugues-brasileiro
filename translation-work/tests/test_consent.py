import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import consent
from native import Invalid
class Consent(unittest.TestCase):
 def test_no_inferred_consent(self):
  event={'number':1,'pull_request':{'body':'Thanks','user':{'login':'contributor'},'html_url':'https://github.com/example/repo/pull/1'}}
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(Invalid):consent.check(Path(d),event)

 def test_affirmative_record(self):
  import json
  event={'number':7,'pull_request':{'body':'- [x] '+consent.ATTESTATION,'user':{'login':'contributor'},'html_url':'https://github.com/example/repo/pull/7'}}
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);folder=root/'translation-work/contributor-consents';folder.mkdir(parents=True)
   record={'identity':'contributor','pull_request':event['pull_request']['html_url'],'scope':'original contributions in this pull request','permission':'CC-BY-NC-SA-4.0 + official-game-commercial-integration','affirmative':True}
   (folder/'PR-7.json').write_text(json.dumps(record));self.assertEqual(consent.check(root,event)['consent'],'recorded')
