"""Preserve P171 pre-launch binding adapter, not actual compiler evidence."""
import base64
import hashlib
import json
from pathlib import Path
root=Path('D:/개발/hwpx-agent')
names=('tools/p09/build_observed_writer_product.py','tools/p09/tests/test_observed_writer_product.py',
 'implementation/p09/evidence/p09-171-observed-writer-product-build.light-run03.v1.json')
dest=root/'implementation/p09/source-archive/p09-171-pre-binding-fixture-fix-r50/preimages.v1.json'
assert Path.cwd().resolve()==root and not dest.exists()
files=[]
for n in names:
 raw=(root/n).read_bytes();files.append(dict(path=n,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode()))
dest.parent.mkdir(parents=True,exist_ok=True)
with dest.open('x',encoding='utf-8') as out:json.dump(dict(state='FAILED_BINDING_NOT_ACTUAL_BUILD',
 error_code='P152_PREP_P157_BUILD_WRITER_BUILD_CONTRACT6_PLUS136_PLUS36',files=files),out,indent=2)
print(json.dumps(dict(whole_preimages_preserved=3,actual_compiler_started=False)))
