#!/usr/bin/env python3
"""Import an already verified static viewer. Never edits the source checkout."""
import argparse,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE='/mobile-redesign-preview'
TEXT={'.html','.js','.css','.json'}
ALLOWED=TEXT|{'.svg','.png','.jpg','.jpeg','.webp','.gif','.avif','.ttf','.woff','.woff2','.ico'}
PATHS=re.compile(r'''(["'`(])/(assets/|history/|versions/|review/|review-versions\.json|review-viewer\.(?:css|js)|favicon\.svg|e2-(?:system|compare)\.html|\?version=)''')

def adapt(data, suffix):
 if suffix not in TEXT:return data
 return PATHS.sub(lambda m:m.group(1)+BASE+'/'+m.group(2),data.decode('utf-8')).encode('utf-8')

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--dist',type=Path,required=True)
 parser.add_argument('--archives',type=Path,help='Optional existing public/ containing retained history/ and versions/')
 parser.add_argument('--source-revision',required=True)
 args=parser.parse_args(); dist=args.dist.resolve(); site=ROOT/'site'
 catalog=json.loads((dist/'review-versions.json').read_text())
 assert catalog['versions'] and all(v['approved'] is False for v in catalog['versions'])
 incoming={}
 def collect(folder,prefix=Path()):
  for p in sorted(folder.rglob('*')):
   if p.is_symlink():raise ValueError('Symlink not allowed: '+str(p))
   if not p.is_file():continue
   relative=prefix/p.relative_to(folder)
   if any(part.startswith('.') for part in relative.parts) or p.suffix.lower() not in ALLOWED:
    raise ValueError('Unreviewed file type/path: '+str(relative))
   incoming[relative]=adapt(p.read_bytes(),p.suffix)
 if args.archives:
  for name in ['history','versions']:
   folder=args.archives/name
   if folder.exists():collect(folder,Path(name))
 collect(dist)
 # Retain previously published files even if a later build omits an archive.
 previous_manifest=ROOT/'release-manifest.json'
 if previous_manifest.exists():
  for name,meta in json.loads(previous_manifest.read_text())['files'].items():
   p=Path(name)
   if p not in incoming:
    data=(site/p).read_bytes()
    assert hashlib.sha256(data).hexdigest()==meta['sha256'], 'Retained file changed: '+name
    incoming[p]=data
 for v in catalog['versions']:
  assert Path(v['url'].lstrip('/')) in incoming, v['id']
 # Reviewer navigation only; application HTML/CSS/JS changes are URL relocation only.
 root=Path('index.html');html=incoming[root].decode()
 html=html.replace('Демонстрационные данные · ни один вариант не утверждён','Демонстрационные данные · ни один вариант не утверждён · <a href="'+BASE+'/archive-index.html">Архив</a>')
 incoming[root]=html.encode()
 current={v['url'].lstrip('/') for v in catalog['versions']}
 archives=[p.as_posix() for p in incoming if p.name=='index.html' and p.parts[0] in ['history','versions'] and p.as_posix() not in current]
 archive_page='<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DonorSearch · архив прототипов</title><style>body{font:16px/1.6 system-ui;margin:32px auto;max-width:760px;padding:0 16px;color:#25272c}a{color:#b52620}li{margin:12px 0}</style><h1>Архив интерактивных прототипов</h1><p>Демонстрационные данные. REVIEW_PENDING — NOT APPROVED.</p><p><a href="'+BASE+'/">Текущий просмотрщик A–E.2</a></p><ul>'
 archive_page+=''.join('<li><a href="'+BASE+'/'+p+'#/">'+p.replace('/index.html','')+'</a></li>' for p in archives)
 incoming[Path('archive-index.html')]=(archive_page+'</ul></html>').encode()
 # A routine release may add versions but cannot silently replace retained snapshots/assets.
 for p,data in incoming.items():
  old=site/p
  if old.exists() and p.parts[0] in ['assets','history','versions'] and old.read_bytes()!=data:
   raise ValueError('Retained resource changed; use a new version/asset path: '+str(p))
 if (site/'review-versions.json').exists():
  previous=json.loads((site/'review-versions.json').read_text())
  assert {v['id'] for v in previous['versions']} <= {v['id'] for v in catalog['versions']}, 'Version removal is not permitted'
 for p,data in incoming.items():
  target=site/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 manifest={p.as_posix():{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for p,data in incoming.items()}
 release={'source_revision':args.source_revision,'base_path':BASE+'/', 'design_status':'REVIEW_PENDING — NOT APPROVED','versions':[v['label'] for v in catalog['versions']],'archives':archives,'files':manifest}
 (ROOT/'release-manifest.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'files':len(manifest),'bytes':sum(x['bytes'] for x in manifest.values()),'versions':release['versions'],'archives':len(archives)}))

if __name__=='__main__':main()
