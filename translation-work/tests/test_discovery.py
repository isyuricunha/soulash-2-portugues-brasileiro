import unittest,sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from toolkit import Project
from storage import json_bytes
import native
class Discovery(unittest.TestCase):
 def test_game_identity_and_spaces(self):
  with tempfile.TemporaryDirectory(prefix='Soulash space ') as d:
   root=Path(d);p=Project(root/'repo');game=root/'game with spaces';source=game/native.SOURCE;source.mkdir(parents=True)
   (game/'version.txt').write_text('0.10.5');(game/'Soulash 2.exe').write_bytes(b'fixture')
   (source/'mod.json').write_bytes(json_bytes({'name':'Core 2'}))
   self.assertEqual(p.game_source(game),(source,'0.10.5'))
   (source/'mod.json').write_bytes(json_bytes({'name':'Translated mod'}))
   with self.assertRaises(native.Invalid):p.game_source(game)
 def test_missing_fallback(self):
  with tempfile.TemporaryDirectory() as d:
   p=Project(d)
   with self.assertRaises(OSError):p.game_source(Path(d)/'missing')

 def test_unique_multiple_and_missing_candidates(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   p=Project(d)
   with patch('winreg.OpenKey',side_effect=OSError('no Steam fixture')):
    with self.assertRaises(native.Invalid):p.discover_game()
 def test_translation_metadata_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'language_metadata.json').write_bytes(json_bytes({'id':'ptbr','name':'PortuguÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Âªs Brasileiro'}))
   with self.assertRaises(native.Invalid):native.extract(root)

 def test_cached_unique_and_conflicting_steam(self):
  from unittest.mock import patch,MagicMock
  from storage import durable
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=Project(root/'repo');game=root/'game';source=game/native.SOURCE;source.mkdir(parents=True)
   (game/'version.txt').write_text('0.10.5');(game/'Soulash 2.exe').write_bytes(b'fixture');(source/'mod.json').write_bytes(json_bytes({'name':'Core 2'}))
   durable(p.path('translation-work/.state/game-path.json'),json_bytes({'path':str(game)}))
   with patch('winreg.OpenKey',side_effect=OSError('fixture')):self.assertEqual(p.discover_game(),str(game.resolve()))
   steam=root/'Steam';(steam/'steamapps').mkdir(parents=True);other=steam/'steamapps/common/Other';other_source=other/native.SOURCE;other_source.mkdir(parents=True)
   (other/'version.txt').write_text('0.10.5');(other/'Soulash 2.exe').write_bytes(b'fixture');(other_source/'mod.json').write_bytes(json_bytes({'name':'Core 2'}))
   (steam/'steamapps/appmanifest_2399160.acf').write_text('"installdir" "Other"')
   with patch('winreg.OpenKey',return_value=MagicMock()),patch('winreg.QueryValueEx',return_value=(str(steam),1)):
    with self.assertRaises(native.Invalid):p.discover_game()

 def test_update_dry_readonly(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=Project(root/'repo');game=root/'game';source=game/native.SOURCE;source.mkdir(parents=True)
   (game/'version.txt').write_text('0.10.5');(game/'Soulash 2.exe').write_bytes(b'fixture');(source/'mod.json').write_bytes(json_bytes({'name':'Core 2'}))
   before={str(x):x.read_bytes() for x in root.rglob('*') if x.is_file()}
   durable=p.path('translation-work/source-profiles.json');durable.parent.mkdir(parents=True,exist_ok=True)
   durable.write_bytes(json_bytes({'versions':{'0.10.5':{'sources':{}}}}))
   before={str(x):x.read_bytes() for x in root.rglob('*') if x.is_file()}
   with patch.object(p,'integrity'),patch('native.extract',return_value=({},[])),patch.object(p,'sync',return_value={'status':'fixture'}) as sync:
    self.assertEqual(p.update(game,dry=True),{'status':'fixture'});self.assertTrue(sync.call_args.kwargs['dry'])
   self.assertEqual(before,{str(x):x.read_bytes() for x in root.rglob('*') if x.is_file()})

 def test_modified_profile_refused_before_sync(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   p=Project(d);profile=p.path('translation-work/source-profiles.json');profile.parent.mkdir(parents=True);profile.write_bytes(json_bytes({'versions':{'0.10.5':{'sources':{'messages.json':'expected'}}}}))
   with patch.object(p,'integrity'),patch.object(p,'game_source',return_value=(Path(d),'0.10.5')),patch('native.extract',return_value=({'messages.json':b'modified'},[])),patch.object(p,'sync') as sync:
    with self.assertRaises(native.Invalid):p.update(d,dry=True)
    sync.assert_not_called()

 def test_update_checks_integrity_before_source_access(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   p=Project(d)
   with patch.object(p,'integrity',side_effect=native.Invalid('CHECKSUM_MISMATCH')),patch.object(p,'game_source') as source:
    with self.assertRaises(native.Invalid):p.update(d,dry=True)
    source.assert_not_called()

 def test_future_version_explicit_original_attestation(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   p=Project(d);profile=p.path('translation-work/source-profiles.json');profile.parent.mkdir(parents=True);profile.write_bytes(json_bytes({'versions':{}}))
   source=Path(d)/'source';source.mkdir();(source/'mod.json').write_bytes(json_bytes({'author':'Official'}))
   with patch.object(p,'integrity'),patch.object(p,'game_source',return_value=(source,'0.10.6')),patch('native.extract',return_value=({'messages.json':b'original'},[])),patch.object(p,'sync',return_value={'status':'preview'}) as sync:
    with self.assertRaises(native.Invalid):p.update(d,dry=True)
    sync.assert_not_called()
    result=p.update(d,dry=True,accept_new_version=True)
    self.assertEqual(result['status'],'preview');self.assertTrue(sync.call_args.kwargs['provenance']['original_files_attested'])
    self.assertFalse(p.path('translation-work/.state/game-path.json').exists())

 def test_accepted_future_version_is_idempotent_without_attestation(self):
  from unittest.mock import patch
  from storage import sha
  with tempfile.TemporaryDirectory() as d:
   p=Project(d);profile=p.path('translation-work/source-profiles.json');profile.parent.mkdir(parents=True);profile.write_bytes(json_bytes({'versions':{}}))
   manifest=p.path('translation-work/translations/manifest.json');manifest.parent.mkdir(parents=True);manifest.write_bytes(json_bytes({'version':'0.10.6','sources':{'messages.json':sha(b'original')}}))
   with patch.object(p,'integrity'),patch.object(p,'game_source',return_value=(Path(d),'0.10.6')),patch('native.extract',return_value=({'messages.json':b'original'},[])),patch.object(p,'sync',return_value={'status':'unchanged'}) as sync:
    self.assertEqual(p.update(d,dry=True)['status'],'unchanged')
    self.assertFalse(sync.call_args.kwargs['provenance']['original_files_attested'])
