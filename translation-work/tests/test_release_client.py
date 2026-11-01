import sys,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release import Client,REPOSITORY
from native import Invalid
class ReleaseClient(unittest.TestCase):
 def test_canonical_root_and_upload(self):
  calls=[]
  def transport(method,url,headers,body):
   calls.append((method,url,body));return 200,b'{"id":1}',{}
  c=Client('fixture',transport=transport)
  c.request('GET');c.request('POST','/releases',{'draft':True})
  c.request('POST','/releases/1/assets?name=PTBR.zip',b'zip',upload=True)
  self.assertEqual(calls[0][1],'https://api.github.com/repos/'+REPOSITORY)
  self.assertEqual(calls[2][1],'https://uploads.github.com/repos/'+REPOSITORY+'/releases/1/assets?name=PTBR.zip')
 def test_http_failures(self):
  for code in (401,403,404):
   with self.subTest(code=code):
    c=Client('fixture',transport=lambda *args:(code,b'{}',{}))
    with self.assertRaises(Invalid):c.request('GET')
 def test_missing_ref(self):
  c=Client('fixture',transport=lambda *args:(404,b'{}',{}))
  self.assertIsNone(c.tag_sha('v1.0.0'))
 def test_retry(self):
  replies=iter([(503,b'{}',{}),(200,b'{}',{})])
  c=Client('fixture',transport=lambda *args:next(replies),sleeper=lambda _:None)
  self.assertEqual(c.request('GET'),{})

 def test_nested_tag_encoding(self):
  calls=[]
  def transport(method,url,headers,body):calls.append(url);return 404,b'{}',{}
  c=Client('fixture',transport=transport);self.assertIsNone(c.tag_sha('release/test'))
  self.assertTrue(calls[0].endswith('/git/ref/tags/release%2Ftest'))
 def test_unexpected_repository_refused(self):
  with self.assertRaises(Invalid):Client('fixture',repository='someone/else')
