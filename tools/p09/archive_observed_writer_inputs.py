"""Immutable whole preimages for P171 fixture repair and document sync."""
import base64
import hashlib
import json
from pathlib import Path
ROOT=Path('D:/개발/hwpx-agent')
NAMES=('tools/p09/build_observed_writer_product.py','tools/p09/tests/test_observed_writer_product.py',
    'implementation/p09/evidence/p09-171-observed-writer-product-build.light-run01.v1.json',
    'CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
DEST=ROOT/'implementation/p09/source-archive/p09-171-initial-fixture-and-documents-r50/preimages.v1.json'
assert Path.cwd().resolve()==ROOT and not DEST.exists()
files=[]
for name in NAMES:
    raw=(ROOT/name).read_bytes()
    files.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
        base64=base64.b64encode(raw).decode('ascii')))
DEST.parent.mkdir(parents=True,exist_ok=True)
with DEST.open('x',encoding='utf-8') as out:json.dump(dict(state='PRESERVED_NOT_PASS',files=files),out,indent=2)
print(json.dumps(dict(whole_preimages_preserved=len(files),path=DEST.relative_to(ROOT).as_posix())))
