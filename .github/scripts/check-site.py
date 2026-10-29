#!/usr/bin/env python3
"""Check the exact static artifact, retained versions and Pages path relocation."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SITE=ROOT/'site';BASE='/mobile-redesign-preview/'
manifest=json.loads((ROOT/'release-manifest.json').read_text())
assert manifest['design_status']=='REVIEW_PENDING — NOT APPROVED'
actual={p.relative_to(SITE).as_posix() for p in SITE.rglob('*') if p.is_file()}
assert actual==set(manifest['files']), 'Unlisted or missing static files'
for name,meta in manifest['files'].items():
 p=SITE/name;assert not p.is_symlink();data=p.read_bytes()
 assert len(data)==meta['bytes'] and hashlib.sha256(data).hexdigest()==meta['sha256'],name
 if p.suffix in ['.html','.js','.css','.json']:
  s=data.decode('utf-8')
  assert not re.search(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----',s),name+' credential pattern'
  assert '/Users/' not in s and '/private/tmp/' not in s,name+' local path'
  assert not re.search(r'''["'`(]/(?:assets/|history/|versions/|review/|review-versions\.json|review-viewer\.(?:css|js)|favicon\.svg|e2-(?:system|compare)\.html|\?version=)''',s),name+' unrelocated root URL'
  # All declared HTML resources and CSS url() dependencies must resolve under Pages.
  refs=re.findall(r'''(?:src|href)=["']([^"']+)["']''',s) if p.suffix=='.html' else re.findall(r'''url\(["']?([^\s)'";]+)''',s) if p.suffix=='.css' else []
  for ref in refs:
   if ref.startswith(('http:','https:','data:','#','mailto:','tel:')) or '${' in ref:continue
   target=ref.split('#')[0].split('?')[0]
   if not target:continue
   if target.startswith(BASE):q=SITE/target[len(BASE):]
   elif target.startswith('/'):raise AssertionError(name+' off-base resource '+target)
   else:q=p.parent/target
   assert q.exists(),name+' missing '+target
catalog=json.loads((SITE/'review-versions.json').read_text())
assert all(v['approved'] is False for v in catalog['versions'])
assert set(['A','B','C','D','D-polish','E','E.1','E.2'])<={v['label'] for v in catalog['versions']}
for v in catalog['versions']:
 assert v['url'].startswith(BASE)
 assert '<div id="root"></div>' in (SITE/v['url'][len(BASE):]).read_text(),v['id']+' must be interactive'
print(json.dumps({'status':'PASS','files':len(actual),'versions':len(catalog['versions']),'archives':len(manifest['archives']),'bytes':sum(v['bytes'] for v in manifest['files'].values())}))
