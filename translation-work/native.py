"""Soulash 2 UTF-8 JSON translation adapter. No network or translation engine."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from extractor import SoulashFormatHandler, _get_pointer, _set_pointer
from errors import LocalizationError
from protection import protect_text, validate_restored_translation, OPAQUE_TOKEN_RE

class Invalid(ValueError):
    pass

DEPLOY = 'data/mods/ptbr'
SOURCE = 'data/mods/core_2'
HANDLER = SoulashFormatHandler()

def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode('utf-8')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def validate_text(source, target):
    if not isinstance(target, str) or not target.strip() or OPAQUE_TOKEN_RE.search(target):
        raise Invalid('Translation must be nonempty native text without __KEEP_ tokens')
    try:
        validate_restored_translation(protect_text(source), target)
    except (ValueError, LocalizationError) as e:
        raise Invalid(str(e)) from e

def evidence(data, pointer):
    context = []
    current = data
    keys = {'id','npc_sex','player_sex','sex','gender','race','entities','type','speaker','character','name'}
    for depth, part in enumerate(pointer):
        if isinstance(current, dict):
            values = {k:v for k,v in current.items() if k in keys and isinstance(v,(str,int,bool,list))}
            if values:
                context.append({'pointer':list(pointer[:depth]),'values':values})
        current = current[part]
    return context

def extract(root):
    root = Path(root)
    from storage import safe
    for p in root.rglob('*'):
        safe(root, p.relative_to(root).as_posix())
    project = HANDLER.load(root)
    if not project.files:
        raise Invalid('MALFORMED_SOURCE: no supported localization files')
    metadata = project.files.get('language_metadata.json')
    if metadata is None or metadata.data != {'id':'en','name':'English'}:
        raise Invalid('NOT_ORIGINAL_EN: language_metadata.json must identify English')
    files = {name:parsed.raw_bytes for name,parsed in project.files.items()}
    rows = []
    for u in project.units:
        ctx = evidence(project.files[u.relative_path].data,u.pointer)
        # Context labels based on native selectors, never inferred from proper names.
        rows.append({'id':u.unit_id,'source_file':u.relative_path,'key':u.stable_path,
                     'pointer':list(u.pointer),'destination':list(u.destination_pointer),
                     'EN':u.source_text,'PTBR':'','gender':None,'reviewed':False,
                     'synthetic':u.synthetic,'gender_eligible':u.gender_eligible,
                     'context':ctx,'origin':None})
    return files, rows

def fingerprint(row):
    semantic={k:row[k] for k in ('source_file','key','EN','synthetic','gender_eligible')}
    # An ancestor's array position is a reconstruction locator, not meaning.
    semantic['context']=[item['values'] for item in row['context']]
    return sha(encoded(semantic))

def validate_row(r, complete=False):
    if not isinstance(r['PTBR'],str) or not isinstance(r['reviewed'],bool):
        raise Invalid('Invalid PTBR/reviewed type: '+r['id'])
    if r['gender'] not in (None,'masculine','feminine'):
        raise Invalid('Invalid grammatical gender: '+r['id'])
    if not r['gender_eligible'] and r['gender'] is not None:
        raise Invalid('Gender applies only to entity names')
    if r['PTBR']:
        validate_text(r['EN'],r['PTBR'])
    if r['reviewed'] and (not r['PTBR'].strip() or (r['gender_eligible'] and not r['gender'])):
        raise Invalid('Reviewed entry lacks text/gender: '+r['id'])
    if complete and not r['reviewed']:
        raise Invalid('INCOMPLETE: translation/review pending: '+r['id'])

def rebuild(files, rows, version):
    by_file = {}
    for r in rows:
        validate_row(r,complete=True)
        by_file.setdefault(r['source_file'],[]).append(r)
    outputs = {}
    for name, raw in files.items():
        if name.endswith('.txt'):
            outputs[DEPLOY+'/translations/ptbr/'+name]=raw
            continue
        data=json.loads(raw)
        if name=='language_metadata.json':
            data={'id':'ptbr','name':'Português Brasileiro'}
        else:
            original=copy.deepcopy(data)
            for r in by_file.get(name,[]):
                if _get_pointer(original,tuple(r['pointer'])) != r['EN']:
                    raise Invalid('Source mapping mismatch: '+r['id'])
                _set_pointer(data,tuple(r['destination']),r['PTBR'])
                if r['gender_eligible']:
                    data.pop('feminine_form',None)
                    data.pop('neuter_form',None)
                    if r['gender']=='feminine':data['feminine_form']=True
        raw_output=encoded(data)
        if json.loads(raw_output)!=data:raise Invalid('Native round-trip mismatch: '+name)
        outputs[DEPLOY+'/translations/ptbr/'+name]=raw_output
    outputs[DEPLOY+'/language_metadata.json']=encoded({'id':'ptbr','name':'Português Brasileiro'})
    outputs[DEPLOY+'/mod.json']=encoded({'author':'Yuri Cunha','description':'Tradução para Português Brasileiro.',
        'name':'Português Brasileiro - PTBR','version':'1.0.0','game_required':version,
        'mods_required':[],'disable_transition_tiles':True,'draw_all_glyphs':True})
    return outputs

def smoke():
    import tempfile
    with tempfile.TemporaryDirectory(prefix='soulash-doctor-') as tmp:
        p=Path(tmp)
        (p/'language_metadata.json').write_bytes(encoded({'id':'en','name':'English'}))
        (p/'messages.json').write_bytes(encoded({'greeting':'Hello ::name'}))
        files,rows=extract(p)
        for r in rows:r.update(PTBR=r['EN'],reviewed=True)
        output=rebuild(files,rows,'0.10.5')
        assert json.loads(output[DEPLOY+'/translations/ptbr/messages.json'])=={'greeting':'Hello ::name'}
    return 'parse/rebuild fixture passed'
