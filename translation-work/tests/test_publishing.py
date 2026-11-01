import copy,json,subprocess,sys,unittest,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import release,native
from native import Invalid
from storage import sha,durable
from test_project import ProjectFlow
class GitHubMock:
    """Exercises Client.request URL/headers/body and publication side effects."""
    def __init__(self, head):
        self.head = head
        self.releases = []
        self.tags = {}
        self.calls = []
        self.fail_upload = False
        self.fail_upload_name = None
        self.statuses = []

    def transport(self, method, url, headers, raw):
        parsed = urllib.parse.urlparse(url)
        base = "/repos/"+release.REPOSITORY
        path = parsed.path
        self.calls.append((method, parsed.netloc, path, parsed.query))
        assert headers["Authorization"] == "Bearer test-token"
        assert path.startswith(base)
        endpoint = path[len(base):]
        assert not endpoint.endswith("/")
        if self.statuses:
            status = self.statuses.pop(0)
            if status != 200:
                return status, b'{}', {}
        data = json.loads(raw) if raw and "json" in headers.get("Content-Type", "") else None
        status, result = 200, None
        if endpoint == "":
            result = {"full_name": release.REPOSITORY, "default_branch": "main"}
        elif endpoint == "/commits/main":
            result = {"sha": self.head}
        elif endpoint == "/releases" and method == "GET":
            result = copy.deepcopy(self.releases)
        elif endpoint.startswith("/git/ref/tags/"):
            tag = urllib.parse.unquote(endpoint.split("/tags/", 1)[1])
            if tag in self.tags:
                result = {"object": {"type": "commit", "sha": self.tags[tag]}}
            else:
                status, result = 404, {"message": "Not Found"}
        elif endpoint == "/releases" and method == "POST":
            result = {**data, "id": len(self.releases)+1, "assets": []}
            self.releases.append(result)
        elif endpoint.startswith("/releases/"):
            parts = endpoint.split("/")
            rid = int(parts[2])
            r = next(r for r in self.releases if r["id"] == rid)
            if len(parts) == 4 and parts[3] == "assets":
                if method == "GET":
                    result = r["assets"]
                else:
                    assert parsed.netloc == "uploads.github.com"
                    asset_name = urllib.parse.parse_qs(parsed.query)["name"][0]
                    assert asset_name in {"PTBR.zip"}
                    if self.fail_upload or self.fail_upload_name == asset_name:
                        return 403, b'{}', {}
                    result = {"name": asset_name, "id": 100+rid+len(r["assets"]), "state": "uploaded",
                              "digest": "sha256:"+sha(raw), "size": len(raw)}
                    r["assets"].append(result)
            elif method == "PATCH":
                r.update(data)
                if not r["draft"]:
                    self.tags[r["tag_name"]] = r["target_commitish"]
                result = r
            else:
                result = r
        else:
            raise AssertionError((method, url))
        return status, json.dumps(result).encode(), {}


class Publishing(unittest.TestCase):
 tearDown=ProjectFlow.tearDown
 write=ProjectFlow.write
 apply_all=ProjectFlow.apply_all
 def setUp(self):
  ProjectFlow.setUp(self);self.apply_all();self.p.build()
  self.g('init','-q','-b','main');self.g('config','user.email','fixture@example.invalid');self.g('config','user.name','Fixture')
  durable(self.root/'.gitignore',b'translation-work/.state/\n__pycache__/\nfixture/\n')
  self.commit();self.server=GitHubMock(self.head());self.client=release.Client('test-token',transport=self.server.transport,sleeper=lambda _:None)
 def g(self,*args):return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.DEVNULL)
 def commit(self):self.g('add','.');self.g('commit','-qm','fixture')
 def head(self):return self.g('rev-parse','HEAD').decode().strip()
 def publish(self):return release.publish(self.p,self.client,self.head())
 def test_publish_patch_and_retry(self):
  self.assertEqual(self.publish()['tag'],'v1.0.0')
  self.assertEqual(self.publish()['status'],'unchanged')
  self.write({'greeting':'Goodbye ::name','other':'Welcome'});self.p.sync(self.src,'0.10.5');self.apply_all();self.p.build();self.commit();self.server.head=self.head()
  self.assertEqual(self.publish()['tag'],'v1.0.1');self.assertIn('Interface',self.server.releases[-1]['body'])
  self.assertEqual(self.publish()['status'],'unchanged')
  self.assertEqual([a['name'] for a in self.server.releases[-1]['assets']],['PTBR.zip'])
 def test_interrupted_draft(self):
  self.server.fail_upload=True
  with self.assertRaises(Invalid):self.publish()
  self.server.fail_upload=False;self.assertEqual(self.publish()['tag'],'v1.0.0');self.assertEqual(len(self.server.releases),1)
 def test_stale_head(self):
  self.server.head='0'*40
  with self.assertRaises(Invalid):self.publish()
 def test_unexpected_asset(self):
  self.publish();self.server.releases[0]['assets'].append({'name':'unexpected.txt'})
  with self.assertRaises(Invalid):self.publish()

 def test_readme_only_no_bump(self):
  self.publish();durable(self.root/'README.md',b'Evergreen documentation');self.commit();self.server.head=self.head()
  self.assertEqual(self.publish()['status'],'unchanged')
 def test_nonancestor_and_conflicting_tag(self):
  self.server.tags['v1.0.0']='1'*40
  with self.assertRaises(Invalid):self.publish()
 def test_extra_draft_asset(self):
  self.server.fail_upload=True
  with self.assertRaises(Invalid):self.publish()
  self.server.fail_upload=False;self.server.releases[0]['assets'].append({'name':'LICENSE'})
  with self.assertRaises(Invalid):self.publish()

 def test_preserved_legacy_release(self):
  import json
  from storage import json_bytes,canonical
  legacy={'schema':1,'tags':{'v0.0.19':self.head()}}
  durable(self.root/'translation-work/legacy-releases.json',json_bytes(legacy))
  tool=self.root/'translation-work/toolchain.json';spec=json.loads(tool.read_text());spec['files']['translation-work/legacy-releases.json']['sha256']=sha(json_bytes(legacy));durable(tool,json_bytes(spec))
  runtime=self.root/'translation-work/runtime-support.json';v=json.loads(runtime.read_text());v['toolchain_sha256']=sha(json_bytes(spec));durable(runtime,json_bytes(v))
  old=self.head();self.p.build();self.commit();self.server.head=self.head()
  self.server.tags['v0.0.19']=old;self.server.releases.append({'id':99,'tag_name':'v0.0.19','draft':False,'prerelease':False,'assets':[]})
  self.assertEqual(self.publish()['tag'],'v1.0.0')

 def test_nonancestor_managed_release(self):
  self.publish();self.server.tags['v1.0.0']='1'*40
  with self.assertRaises(Invalid):self.publish()
 def test_asset_digest_mismatch(self):
  self.server.fail_upload=True
  with self.assertRaises(Invalid):self.publish()
  self.server.fail_upload=False;self.server.releases[0]['assets'].append({'name':'PTBR.zip','state':'uploaded','digest':'sha256:wrong','size':1})
  with self.assertRaises(Invalid):self.publish()
