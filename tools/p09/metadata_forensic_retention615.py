"""Bounded canonical metadata spool BEFORE optional encoding; never an acceptance carrier.
Tuples are ordinary JSON arrays: normalize only through byte-identical canonical JSON.
"""
import hashlib,json
import compact_receipt_json as compact
import crossref_generation010_publication as io
MAXIMUM=4*1024*1024

def require(ok,code):
    if not ok:raise ValueError('METADATA615_'+code)

def normalize(row):
    raw=compact.raw(row);require(0<len(raw)<=MAXIMUM,'ROW_LIMIT')
    normalized=json.loads(raw,object_pairs_hook=compact.unique)
    require(type(normalized)is dict and type(normalized.get('state'))is str and compact.raw(normalized)==raw,'EXACT_CANONICAL_JSON')
    return normalized,raw

def retain(root,name,row):
    normalized,raw=normalize(row);root=io.base(root);path=root/name;io.directory(path.parent,root)
    require(not(path.exists()or path.is_symlink()or path.is_junction()),'IMMUTABLE_SPOOL')
    path.mkdir();parts=[]
    for index,start in enumerate(range(0,len(raw),65536)):
        data=raw[start:start+65536];part=f'part-{index:04}.bin';io.write_once(path/part,data)
        actual=io.read_bound(path/part,65536);require(actual==data,'PART_ROUND_TRIP')
        parts.append(dict(path=part,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    manifest=dict(state='RAW_METADATA_RETAINED_NOT_ACCEPTANCE_OR_NATIVE_PERMIT',profile='hwpx-agent.private.canonical-metadata-retention/v1',
        bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),parts=parts)
    io.write_once(path/'manifest.v1.json',compact.raw(manifest))
    actual=b''.join(io.read_bound(path/p['path'],65536)for p in parts)
    require(actual==raw,'WHOLE_ROUND_TRIP')
    return normalized,dict(path=name+'/manifest.v1.json',raw_bytes=len(raw),raw_sha256=manifest['sha256'])
