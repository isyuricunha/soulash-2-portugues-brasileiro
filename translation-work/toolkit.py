#!/usr/bin/env python3
"""Offline Soulash 2 localization workspace, synchronization and verified builds."""
from __future__ import annotations
import argparse
import collections
import json
import os
from pathlib import Path
import platform
import re
import sys
sys.dont_write_bytecode = True
import zipfile
import native
from native import Invalid, DEPLOY, SOURCE
from errors import LocalizationError
from storage import Store, canonical, digest, json_bytes, read_json, safe, sha, durable

WORK='translation-work/'
MANIFEST=WORK+'translations/manifest.json'
BUILD=WORK+'build-manifest.json'
REPORT=WORK+'reports/sync-latest.json'
EDITABLE={'PTBR','gender','reviewed'}

def lines_bytes(rows):
    return b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n').encode('utf-8') for r in rows)

class Project:
    def __init__(self,root):
        self.root=Path(root).resolve()
        self.config=read_json(self.path(WORK+'config.json')) if self.path(WORK+'config.json').exists() else {}
        self.store=Store(self.root,**self.config.get('retention',{}))

    def path(self,rel):return safe(self.root,rel)

    def integrity(self):
        runtime=read_json(self.path(WORK+'runtime-support.json'))
        tool=self.path(WORK+'toolchain.json')
        if sha(canonical(tool.read_bytes()))!=runtime['toolchain_sha256']:
            raise Invalid('CHECKSUM_MISMATCH: toolchain.json')
        for rel,spec in read_json(tool)['files'].items():
            raw=self.path(rel).read_bytes()
            if spec['mode']=='git-lf':raw=canonical(raw)
            elif spec['mode']!='binary':raise Invalid('Unknown hash mode')
            if sha(raw)!=spec['sha256']:raise Invalid('CHECKSUM_MISMATCH: '+rel)
        if sys.version_info<(3,11):raise Invalid('MISSING_RUNTIME: Python 3.11 or newer')
        return runtime

    def load(self,deep=False):
        self.store.clean_state()
        m=read_json(self.path(MANIFEST))
        if m['schema']!=1 or m['deployment']!=DEPLOY:raise Invalid('Unknown manifest')
        if len(set(m['batches']))!=len(m['batches']) or any(not re.fullmatch(r'batch-\d{4,}\.jsonl',b) for b in m['batches']):
            raise Invalid('Invalid batch inventory')
        if sorted(m['batches'])!=sorted(p.name for p in self.path(WORK+'translations').glob('batch-*.jsonl')):
            raise Invalid('Batch inventory mismatch')
        rows=[]; members={}; expected={MANIFEST:digest(self.path(MANIFEST))}
        base={r['id']:r for r in m['catalog']}
        for b in m['batches']:
            rel=WORK+'translations/'+b; raw=self.path(rel).read_bytes(); expected[rel]=sha(raw)
            part=[json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
            if len(part)>m['batch_size']:raise Invalid('Batch exceeds cap')
            for r in part:
                if r['id'] in members or r['id'] not in base:raise Invalid('Duplicate/unknown record')
                if set(r)!=set(base[r['id']]) or any(r[k]!=base[r['id']][k] for k in r if k not in EDITABLE):
                    raise Invalid('Immutable source field changed: '+r['id'])
                native.validate_row(r)
                members[r['id']]=b
            rows.extend(part)
        if len(base)!=len(m['catalog']) or set(members)!=set(base) or len(rows)!=m['entries']:
            raise Invalid('Record inventory mismatch')
        if deep:
            files,current=native.extract(self.path('EN/'+SOURCE))
            if {k:sha(v) for k,v in files.items()}!=m['sources']:raise Invalid('SOURCE_CHANGED: run sync')
            if [{k:v for k,v in r.items() if k not in EDITABLE|{'origin'}} for r in current]!=[{k:v for k,v in r.items() if k not in EDITABLE|{'origin'}} for r in m['catalog']]:
                raise Invalid('Native mapping mismatch')
            expected.update({'EN/'+SOURCE+'/'+k:sha(v) for k,v in files.items()})
        return m,rows,members,expected

    def translation_hash(self,m):
        return sha(json_bytes({b:sha(canonical(self.path(WORK+'translations/'+b).read_bytes())) for b in m['batches']}))

    def status(self):
        storage=self.store.stats()
        if storage['protected']:return {'recovery_required':True,'storage':storage}
        m,rows,members,_=self.load()
        filled=sum(bool(r['PTBR']) for r in rows); reviewed=sum(r['reviewed'] for r in rows)
        pending=next((r for r in rows if not r['reviewed']),None)
        state='absent'
        if self.path(BUILD).exists():
            try:self.verify_output();state='verified'
            except (Invalid,OSError,ValueError):state='stale-or-invalid'
        return {'game':'Soulash 2','version':m['version'],'generation':m['generation'],'files':len(m['sources']),
                'entries':len(rows),'filled':filled,'empty':len(rows)-filled,'reviewed':reviewed,
                'review_pending':len(rows)-reviewed,'batches':len(m['batches']),'PTBR':state,
                'next':{'id':pending['id'],'batch':members[pending['id']]} if pending else None,'storage':storage}

    def sync(self,source,version=None,dry=False,initial=False,seeds=None,provenance=None):
        self.integrity(); files,candidate=native.extract(source)
        previous=None;oldrows=[];members={};expected={}
        if self.path(MANIFEST).exists():
            if initial:raise Invalid('EXISTS: use sync, not extract')
            previous,oldrows,members,expected=self.load()
            missing=set(previous['sources'])-set(files)
            if missing:raise Invalid('INCOMPLETE_SOURCE: removed files require adapter review: '+str(sorted(missing)[:10]))
        version=version or (previous['version'] if previous else None)
        if not version or not re.fullmatch(r'\d+\.\d+\.\d+(?:\.\d+)*',version):raise Invalid('Explicit verified game version required')
        hashes={k:sha(v) for k,v in files.items()}; generation=sha(json_bytes({'sources':hashes,'version':version,'adapter_revision':native.EXTRACTION_REVISION}))
        old={r['id']:r for r in oldrows}
        batches={b:[] for b in previous['batches']} if previous else {'batch-0001.jsonl':[]}
        reserved=collections.Counter(members.values())
        report={'previous_generation':previous['generation'] if previous else None,'generation':generation,
                'version':version,'counts':dict.fromkeys(['added','modified','removed','moved','unchanged','preserved_translations'],0),
                'resources':{'added':sorted(set(files)-set(previous['sources'] if previous else [])),
                    'modified':sorted(k for k in files if previous and k in previous['sources'] and hashes[k]!=previous['sources'][k]),'removed':[]},
                'changes':[],'affected_batches':[],'validation':'passed','warnings':[]}
        history=[]
        for r in candidate:
            prior=old.pop(r['id'],None);kind='added'
            if prior:
                b=members[r['id']];reserved[b]-=1
                if native.fingerprint(r)==native.fingerprint(prior):
                    for k in EDITABLE|{'origin'}:r[k]=prior[k]
                    kind='moved' if r['pointer']!=prior['pointer'] else 'unchanged'
                    if kind=='moved':history.append({'classification':kind,'previous':prior})
                    report['counts']['preserved_translations']+=bool(r['PTBR'])
                else:
                    kind='modified';history.append({'classification':kind,'previous':prior})
            else:
                b=list(batches)[-1]
                if len(batches[b])+reserved[b]>=500:
                    b=f'batch-{max(int(x[6:-6]) for x in batches)+1:04d}.jsonl';batches[b]=[]
                if seeds and r['id'] in seeds:
                    seed=seeds[r['id']]
                    if native.fingerprint(seed)==native.fingerprint(r):
                        r.update({k:seed[k] for k in EDITABLE|{'origin'}})
                        report['counts']['preserved_translations']+=bool(r['PTBR'])
            batches[b].append(r);report['counts'][kind]+=1
            if kind!='unchanged':report['changes'].append({'classification':kind,'id':r['id'],'batch':b,'previous':prior,'current':r})
        for rid,r in old.items():
            report['counts']['removed']+=1;history.append({'classification':'removed','previous':r})
            report['changes'].append({'classification':'removed','id':rid,'batch':members[rid],'previous':r,'current':None})
        if provenance is not None:report['source_provenance']=provenance
        report['pending']=sum(not r['PTBR'] for r in candidate)
        report['review_pending']=sum(not r['reviewed'] for r in candidate)
        report['affected_batches']=sorted({c['batch'] for c in report['changes']})
        if previous and generation==previous['generation'] and not any(report['counts'][k] for k in ('added','modified','removed','moved')):
            return {'status':'unchanged','generation':generation,'preserved':report['counts']['preserved_translations']}
        manifest={'schema':1,'adapter_revision':native.EXTRACTION_REVISION,'deployment':DEPLOY,'source_root':SOURCE,'version':version,'generation':generation,
            'sources':hashes,'entries':len(candidate),'batch_size':500,'batches':list(batches),'catalog':candidate}
        if dry:return report
        changes={'EN/'+SOURCE+'/'+k:v for k,v in files.items()}
        changes.update({WORK+'translations/'+b:lines_bytes(rs) for b,rs in batches.items()})
        changes[MANIFEST]=json_bytes(manifest)
        # The immutable JSONL context remains current; archived cross-references
        # must never silently describe a different accepted source generation.
        context_path=WORK+'reference/conversation-context.json'
        if previous and self.path(context_path).exists():
            context=read_json(self.path(context_path))
            if context.get('generation') != generation:
                changes[context_path]=json_bytes({'schema':1,'generation':generation,
                    'status':'invalidated-by-source-sync','previous_generation':previous['generation'],
                    'instruction':'Use current JSONL context and EN references; archived cross-reference belongs to an older source generation.'})
        txid=self.store.new_id();report['transaction']=txid
        changes[REPORT]=json_bytes(report)
        changes[WORK+'reports/sync-latest.md']=('# Sincronização Soulash 2 '+version+'\n\n'+
            '\n'.join(f'- {k}: {v}' for k,v in report['counts'].items())+
            '\n\nConsulte sync-latest.json para IDs, textos anteriores e lotes. Revise as pendências antes de build.\n').encode('utf-8')
        if previous:
            changes[WORK+'history/'+previous['generation']+'.json']=json_bytes({'previous_generation':previous['generation'],'version':previous['version'],'sources':previous['sources'],'added_ids':[c['id'] for c in report['changes'] if c['classification']=='added'],'changed_translations':history})
        self.store.commit(changes,expected,operation='sync',transaction_id=txid)
        return {k:v for k,v in report.items() if k not in ('changes','resources')} | {'resources':{k:len(v) for k,v in report['resources'].items()}}

    def game_source(self,game_root):
        root=Path(game_root).resolve()
        version=safe(root,'version.txt').read_text(encoding='utf-8').strip()
        source=safe(root,SOURCE)
        mod=read_json(safe(source,'mod.json'))
        if not (root/'Soulash 2.exe').is_file() or mod.get('name')!='Core 2':
            raise Invalid('WRONG_GAME_ROOT: expected original Soulash 2 installation')
        return source,version

    def discover_game(self):
        local=self.path(WORK+'.state/game-path.json')
        candidates=[]
        if local.exists():candidates.append(read_json(local)['path'])
        if os.name=='nt':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam') as key:
                    steam=Path(winreg.QueryValueEx(key,'SteamPath')[0])
                libraries=[steam]
                vdf=steam/'steamapps/libraryfolders.vdf'
                if vdf.exists():libraries += [Path(p.replace('\\\\','\\')) for p in re.findall(r'"path"\s+"([^"]+)"',vdf.read_text())]
                for library in libraries:
                    manifest=library/'steamapps/appmanifest_2399160.acf'
                    if manifest.exists():
                        match=re.search(r'"installdir"\s+"([^"]+)"',manifest.read_text())
                        if match:candidates.append(str(library/'steamapps/common'/match[1]))
            except OSError:pass
        valid={}
        for p in candidates:
            try:valid[str(Path(p).resolve())]=self.game_source(p)
            except (OSError,ValueError):pass
        if len(valid)!=1:raise Invalid('No unique verified installation; use update-sources --game-root "/path/to/Soulash 2"')
        return next(iter(valid))

    def update(self,game_root=None,dry=False,accept_new_version=False):
        self.integrity()
        game_root=game_root or self.discover_game()
        source,version=self.game_source(game_root)
        profiles=read_json(self.path(WORK+'source-profiles.json'))['versions']
        if self.path(MANIFEST).exists():
            accepted=read_json(self.path(MANIFEST))
            if accepted['version'] not in profiles:
                profiles[accepted['version']]={'sources':accepted['sources']}
        files,_=native.extract(source)
        candidate_hashes={name:sha(raw) for name,raw in files.items()}
        if version not in profiles and not accept_new_version:
            raise Invalid('UNVERIFIED_VERSION: verify original unmodified game files, then rerun update-sources --game-root "'+str(game_root)+'" --accept-new-version; --dry-run previews without importing')
        if version in profiles and candidate_hashes!=profiles[version]['sources']:
            raise Invalid('UNVERIFIED_SOURCE: installed files differ from the reviewed original profile; do not import translated or modified core_2')
        if version not in profiles:
            metadata=read_json(safe(source,'mod.json'))
            if metadata.get('author')!='Official':raise Invalid('UNVERIFIED_SOURCE: new version requires the Official core mod')
            if self.path(MANIFEST).exists():
                previous=read_json(self.path(MANIFEST))
                if tuple(map(int,version.split('.'))) <= tuple(map(int,previous['version'].split('.'))):
                    raise Invalid('VERSION_NOT_NEWER: refusing unverified downgrade or same-version replacement')
        provenance={'version':version,'original_files_attested':version not in profiles,'fingerprint':sha(json_bytes(candidate_hashes)),'verification':'explicit maintainer assertion' if version not in profiles else 'reviewed exact source inventory'}
        result=self.sync(source,version,dry=dry,provenance=provenance)
        if not dry:durable(self.path(WORK+'.state/game-path.json'),json_bytes({'path':str(Path(game_root).resolve())}))
        return result

    def apply(self,payload,replace=False):
        self.integrity();m,rows,members,expected=self.load()
        if payload.get('generation')!=m['generation']:raise Invalid('STALE_PAYLOAD: wrong source generation')
        updates=payload['entries']
        if not isinstance(updates,list) or payload.get('expected_count')!=len(updates):raise Invalid('Payload count mismatch')
        ids=[v['id'] for v in updates]
        if len(set(ids))!=len(ids):raise Invalid('Duplicate payload IDs')
        byid={r['id']:r for r in rows};dirty=set();failures=[];accepted=[]
        for entry in updates:
            rid=entry['id']
            try:
                if rid not in byid or set(entry)-({'id','source_fingerprint'}|EDITABLE):raise Invalid('Unknown ID/field')
                r=byid[rid]
                if entry.get('source_fingerprint')!=native.fingerprint(r):raise Invalid('Source fingerprint mismatch')
                target=dict(r);target.update({k:v for k,v in entry.items() if k in EDITABLE})
                if r['PTBR'] and target['PTBR']!=r['PTBR'] and not replace:raise Invalid('Existing PTBR: use --replace after review')
                native.validate_row(target)
                if target!=r:byid[rid]=target;dirty.add(members[rid])
                accepted.append(rid)
            except (Invalid,LocalizationError) as e:failures.append({'id':rid,'error':str(e)})
        changes={WORK+'translations/'+b:lines_bytes([byid[r['id']] for r in rows if members[r['id']]==b]) for b in dirty}
        tx=self.store.commit(changes,expected,operation='apply')
        return {'accepted':accepted,'rejected':failures,'transaction':tx,'changed_batches':sorted(dirty)}

    def build(self):
        self.integrity();m,rows,_,expected=self.load(deep=True)
        for r in rows:native.validate_row(r,complete=True)
        files={name:self.path('EN/'+SOURCE+'/'+name).read_bytes() for name in m['sources']}
        outputs=native.rebuild(files,rows,m['version'])
        receipt={'schema':1,'complete':True,'completed':len(rows),'generation':m['generation'],
            'version':m['version'],'translation_hash':self.translation_hash(m),'manifest_hash':sha(canonical(self.path(MANIFEST).read_bytes())),
            'toolchain_hash':sha(canonical(self.path(WORK+'toolchain.json').read_bytes())),
            'outputs':{k:sha(v) for k,v in outputs.items()}}
        changes={'PTBR/'+k:v for k,v in outputs.items()}
        if self.path('PTBR').exists():
            for p in self.path('PTBR').rglob('*'):
                if p.is_file():
                    rel=p.relative_to(self.root).as_posix();expected[rel]=digest(p)
                    if rel not in changes:changes[rel]=None
        changes[BUILD]=json_bytes(receipt)
        self.store.commit(changes,expected,operation='build')
        return self.verify_output()

    def verify_output(self):
        self.integrity();m,rows,_,_=self.load()
        for r in rows:native.validate_row(r,complete=True)
        receipt=read_json(self.path(BUILD))
        if (receipt.get('complete') is not True or receipt.get('completed')!=len(rows)
            or receipt.get('generation')!=m['generation'] or receipt.get('translation_hash')!=self.translation_hash(m)
            or receipt.get('manifest_hash')!=sha(canonical(self.path(MANIFEST).read_bytes()))
            or receipt.get('toolchain_hash')!=sha(canonical(self.path(WORK+'toolchain.json').read_bytes()))):
            raise Invalid('STALE_BUILD: complete flag is not proof; rebuild after source/translation/tool changes')
        actual_sources={p.relative_to(self.path('EN/'+SOURCE)).as_posix() for p in native.HANDLER.discover(self.path('EN/'+SOURCE))}
        if actual_sources!=set(m['sources']):raise Invalid('SOURCE_INVENTORY_MISMATCH')
        for name,h in m['sources'].items():
            if digest(self.path('EN/'+SOURCE+'/'+name))!=h:raise Invalid('SOURCE_CHECKSUM_MISMATCH: '+name)
        inventory={DEPLOY+'/translations/ptbr/'+name for name in m['sources']}|{DEPLOY+'/mod.json',DEPLOY+'/language_metadata.json'}
        if set(receipt['outputs'])!=inventory:raise Invalid('Invalid build inventory')
        actual={p.relative_to(self.path('PTBR')).as_posix():digest(self.path(p.relative_to(self.root).as_posix())) for p in self.path('PTBR').rglob('*') if p.is_file()}
        if actual!=receipt['outputs']:raise Invalid('OUTPUT_CHECKSUM_MISMATCH')
        return receipt

    def package(self):
        receipt=self.verify_output();target=self.path(WORK+'.state/PTBR.zip');target.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for rel in sorted(receipt['outputs']):
                info=zipfile.ZipInfo(rel,(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
                z.writestr(info,self.path('PTBR/'+rel).read_bytes())
        with zipfile.ZipFile(target) as z:
            if set(z.namelist())!=set(receipt['outputs']) or z.testzip():raise Invalid('Invalid ZIP')
        return {'zip':str(target),'sha256':digest(target),'members':len(receipt['outputs'])}

    def doctor(self,arm64=False):
        self.integrity()
        if arm64 and (platform.system()!='Linux' or platform.machine().lower() not in ('aarch64','arm64')):
            raise Invalid('UNSUPPORTED_ARCHITECTURE: --arm64 requires Linux aarch64')
        self.load(deep=True)
        return {'runtime':platform.python_version(),'system':platform.system(),'architecture':platform.machine(),
                'fixture':native.smoke(),'read_only':True,'ARM64':'verified here' if arm64 else 'pending target preflight'}

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr,'reconfigure'):sys.stderr.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['extract','sync','update-sources','apply','check','status','resume','diff','build','verify-output','package','doctor','gc','recover','rollback','export-payload'])
    parser.add_argument('--game-root');parser.add_argument('--source-root');parser.add_argument('--version')
    parser.add_argument('--payload');parser.add_argument('--replace',action='store_true');parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--accept-new-version',action='store_true',help='Explicitly attest new-version core files are original and unmodified; known-version tampering remains forbidden');parser.add_argument('--arm64',action='store_true');parser.add_argument('--break-lock',action='store_true')
    args=parser.parse_args()
    if args.dry_run and args.command not in ('sync','extract','update-sources','gc'):
        parser.error('--dry-run is supported only by sync, extract, update-sources and gc')
    if args.accept_new_version and args.command!='update-sources':parser.error('--accept-new-version is only for update-sources')
    if args.command=='apply' and not args.payload:parser.error('apply requires --payload')
    p=Project(Path(__file__).resolve().parent.parent)
    def run():
        c=args.command
        if c=='update-sources':return p.update(args.game_root,args.dry_run,args.accept_new_version)
        if c in ('extract','sync'):return p.sync(Path(args.source_root) if args.source_root else p.path('EN/'+SOURCE),args.version,dry=args.dry_run,initial=c=='extract')
        if c=='apply':return p.apply(read_json(Path(args.payload)),args.replace)
        if c=='export-payload':
            m,rows,_,_=p.load()
            return {'generation':m['generation'],'expected_count':len(rows),'entries':[{'id':r['id'],'source_fingerprint':native.fingerprint(r),'PTBR':r['PTBR'],'gender':r['gender'],'reviewed':r['reviewed']} for r in rows]}
        if c in ('status','resume'):return p.status()
        if c=='check':p.integrity();p.load(deep=True);return p.status()
        if c=='diff':return read_json(p.path(REPORT))
        if c=='build':return p.build()
        if c=='verify-output':return p.verify_output()
        if c=='package':return p.package()
        if c=='doctor':return p.doctor(args.arm64)
        if c=='gc':return p.store.gc(args.dry_run)
        if c=='recover':return p.store.recover()
        if c=='rollback':return {'transaction':p.store.rollback()}
    try:
        if args.break_lock:
            if args.command!='recover':raise Invalid('--break-lock is only for recover')
            p.store.break_lock()
        readonly=args.command in ('status','resume','check','diff','verify-output','doctor','export-payload') or args.dry_run
        if readonly:result=run()
        else:
            with p.store.lock():result=run()
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 1 if isinstance(result,dict) and result.get('rejected') else 0
    except (Invalid,LocalizationError,OSError,ValueError,KeyError,TypeError) as e:
        print('ERROR: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
