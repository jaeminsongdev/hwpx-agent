"""Whole r51 wait documents before P173 terminal/P174 cost progress."""
import base64
import hashlib
import json
from pathlib import Path
root=Path('D:/개발/hwpx-agent')
dest=root/'implementation/p09/source-archive/p09-174-pre-progress-r52/document-preimages.v1.json'
assert Path.cwd().resolve()==root and not dest.exists()
files=[]
for n in ('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'):
    raw=(root/n).read_bytes()
    files.append(dict(path=n,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode()))
dest.parent.mkdir(parents=True,exist_ok=True)
with dest.open('x',encoding='utf-8') as out:json.dump(dict(state='WHOLE_PREIMAGES_NOT_RUNTIME_PASS',files=files),out,indent=2)
print(json.dumps(dict(whole_preimages_preserved=2)))
