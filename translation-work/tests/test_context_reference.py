import unittest,json
from pathlib import Path
class Reference(unittest.TestCase):
 def test_context_matches_native_ids(self):
  root=Path(__file__).resolve().parents[2];ref=json.loads((root/'translation-work/reference/conversation-context.json').read_text(encoding='utf-8'))
  native=json.loads((root/'EN/data/mods/core_2/conversations.json').read_bytes())['conversations']
  self.assertEqual(len(ref['conversations']),len(native))
  for r,source in zip(ref['conversations'],native):
   self.assertEqual(r['id'],source.get('id'));self.assertEqual(r['npc_sex_raw'],source.get('npc_sex'))
   for entity in r['entities']:
    for match in entity['matches']:
     data=json.loads((root/'EN/data/mods/core_2'/match['file']).read_bytes())
     self.assertEqual(str(data['id']),entity['id']);self.assertEqual(data.get('name'),match['name'])
