import unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import release
class Changelog(unittest.TestCase):
 def body(self,rows,old=None):
  with patch('release.history_rows',side_effect=lambda project,ref:rows if ref=='current' else old or {}):
   return release.changelog(None,'previous' if old is not None else None,'current',{'version':'0.10.5','outputs':{}})
 def test_dialogue_and_multiple_categories(self):
  rows={'a':{'source_file':'dialogues.json','EN':'Hello','PTBR':'Olá'},'b':{'source_file':'entities/1.json','EN':'Sword','PTBR':'Espada'}}
  body=self.body(rows,{})
  self.assertIn('Diálogos',body);self.assertIn('Itens e criaturas',body);self.assertIn('/compare/previous...current',body)
  self.assertLess(body.index('Download'),body.index('Pix'));self.assertIn('uFEwSMwUYb',body)
 def test_unknown_and_native_only(self):
  row={'a':{'source_file':'unknown.json','EN':'Hello','PTBR':'Olá'}}
  self.assertIn('Outros textos',self.body(row,{}))
  self.assertIn('recursos nativos',self.body(row,row))
 def test_first_presentation(self):
  text=self.body({});self.assertIn('Primeiro pacote',text);self.assertNotIn('![',text);self.assertNotIn('Commits',text)
