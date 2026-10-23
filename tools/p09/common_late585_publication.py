"""One SQL585 result only: bounded private forensic preservation before self-contained encoding.

Reuse the qualified generic file primitives without changing any005 namespace,
validator, runtime or approval. The spool never grants execution or acceptance.
"""
import hashlib,json
from pathlib import Path
from types import SimpleNamespace as NS
import crossref_generation005_publication as files
import crossref_inline_receipt567 as layout
OUTPUT='implementation/p09/evidence/p09-361-common-late-sql585.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-common-late585-final-spool'
MANIFEST='retained-row.v1.json'
CHUNK=65536


def require(ok,code):
    if not ok:raise ValueError(code)


def validate(row):
    require(type(row)is dict and row.get('state')in('FAILED_COMMON_LATE_SQL585','PASS_COMMON_LATE_SQL585_CURRENT_CAS_DENIAL_RESTART_NOT_NATIVE_OR_GATE')
        and type(row.get('accepted_count_delta'))is int and row['accepted_count_delta']==0 and row.get('P09_gate')=='OPEN'
        and row.get('P10_started')is False and row.get('Hancom_COM_Native_or_249_started')is False,
        'SQL585_PUBLICATION_NEVER_NATIVE_AUTHORITY_OR_GATE')


def retained_row(root):
    root=files.base(root);folder=root/SPOOL;files.directory(folder,root)
    meta=json.loads(files.read_bound(folder/MANIFEST,16384))
    require(type(meta)is dict and set(meta)=={'profile','bytes','sha256','parts'}and meta['profile']=='common-late585-forensic-only/v1',
        'SQL585_EXACT_FORENSIC_MANIFEST')
    require(type(meta['bytes'])is int and 0<meta['bytes']<=layout.MAX_INPUT_BYTES and type(meta['parts'])is list
        and len(meta['parts'])==(meta['bytes']+CHUNK-1)//CHUNK,'SQL585_FORENSIC_BOUNDS')
    chunks=[]
    for index,part in enumerate(meta['parts']):
        name=f'part-{index:03}.json-bytes'
        require(type(part)is dict and set(part)=={'name','bytes','sha256'}and part['name']==name
            and type(part['bytes'])is int and part['bytes']==min(CHUNK,meta['bytes']-index*CHUNK),'SQL585_CLOSED_FORENSIC_PART')
        raw=files.read_bound(folder/name,CHUNK)
        require(len(raw)==part['bytes']and hashlib.sha256(raw).hexdigest()==part['sha256'],'SQL585_FORENSIC_PART_INTEGRITY');chunks.append(raw)
    raw=b''.join(chunks)
    require(len(raw)==meta['bytes']and hashlib.sha256(raw).hexdigest()==meta['sha256'],'SQL585_FORENSIC_WHOLE_INTEGRITY')
    row=json.loads(raw);validate(row);return row


def publish_final(root,row):
    validate(row);root=files.base(root);output=root/OUTPUT;folder=root/SPOOL
    require(not(output.exists()or output.is_symlink()or output.is_junction()or folder.exists()or folder.is_symlink()or folder.is_junction()),
        'SQL585_NO_EXISTING_RESULT_OR_FORENSICS_REUSE')
    files.directory(folder.parent,root)
    raw=json.dumps(row,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    require(0<len(raw)<=layout.MAX_INPUT_BYTES,'SQL585_CANONICAL_ROW_BOUND');folder.mkdir();parts=[]
    for index,offset in enumerate(range(0,len(raw),CHUNK)):
        chunk=raw[offset:offset+CHUNK];name=f'part-{index:03}.json-bytes';files.write_once(folder/name,chunk)
        parts.append(dict(name=name,bytes=len(chunk),sha256=hashlib.sha256(chunk).hexdigest()))
    meta=dict(profile='common-late585-forensic-only/v1',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),parts=parts)
    manifest=json.dumps(meta,separators=(',',':')).encode();require(len(manifest)<=16384,'SQL585_FORENSIC_MANIFEST_BOUND')
    files.write_once(folder/MANIFEST,manifest)
    require(retained_row(root)==row,'SQL585_EXACT_RETAINED_ROW_BEFORE_ENCODING')
    # Any encoder/writer failure leaves the exact private row. No forensic part is
    # accepted as the formal packet or as a SQL/Native/P09 qualification carrier.
    return files.original.publish(root,OUTPUT,layout.pack(row),NS(require=require,exact=files.exact))
