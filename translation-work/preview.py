"""Build an explicitly unreviewed prerelease, without a final build receipt."""
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
import native
from toolkit import Project
from storage import json_bytes, sha


def build_preview(root):
    p = Project(root)
    p.integrity()
    m, rows, _, _ = p.load(deep=True)
    files = {name: p.path('EN/'+native.SOURCE+'/'+name).read_bytes() for name in m['sources']}
    outputs = native.rebuild(files, rows, m['version'], require_review=False)
    legacy = p.path('ptbr')
    metadata = json.loads((legacy/'mod.json').read_bytes())
    metadata.update(version='1.0.0-preview.1', game_required=m['version'],
                    description='Prévia experimental da tradução PT-BR. Revisão linguística pendente; sem teste dentro do jogo.')
    outputs[native.DEPLOY+'/mod.json'] = native.encoded(metadata)
    for image in ('S2.png', 'LogoMod.png'):
        outputs[native.DEPLOY+'/'+image] = (legacy/image).read_bytes()
    target = p.path('translation-work/.state/preview/PTBR.zip')
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, raw in sorted(outputs.items()):
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, raw)
    with zipfile.ZipFile(target) as z:
        if z.testzip() or set(z.namelist()) != set(outputs):
            raise native.Invalid('Invalid preview ZIP')
        for name, raw in outputs.items():
            if z.read(name) != raw:
                raise native.Invalid('Preview member mismatch: '+name)
    report = {'prerelease': True, 'game_version': m['version'], 'entries': len(rows),
              'reviewed': sum(r['reviewed'] for r in rows),
              'review_pending': sum(not r['reviewed'] for r in rows),
              'runtime_tested': False, 'generation': m['generation'],
              'zip': str(target), 'sha256': sha(target.read_bytes()), 'members': len(outputs)}
    p.path('translation-work/reports/preview-build.json').write_bytes(json_bytes(report))
    return report


if __name__ == '__main__':
    print(json.dumps(build_preview(Path(__file__).resolve().parent.parent), ensure_ascii=False, indent=2))
