"""Future008 final-result publication only. No Native, claim, retry or acceptance entry.

The accepted packet is self-contained and keeps the original 256KiB writer cap.
An independent bounded private spool preserves the exact canonical row BEFORE
encoding, including failures. It is forensic data, never an acceptance carrier.
Consumed001..004 and their publishers are not modified or reconstructed.
"""
import hashlib,json,os
from pathlib import Path
from types import SimpleNamespace as NS
import compact_receipt_json as compact
import crossref_inline_receipt567 as layout
import successor_preparation_workspace_v1 as original

GENERATION=8
OUTPUT='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run008.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-generation008-final-result-spool'
MANIFEST='retained-row.v1.json'
PROFILE='hwpx-agent.private-unpublished-canonical-row/v1'
CHUNK_BYTES=65536
MAX_BYTES=layout.MAX_INPUT_BYTES
MAX_PARTS=MAX_BYTES//CHUNK_BYTES
STATES={'FAILED_EXTERNAL_QUALIFIED_ENTRY','CAPTURED_CURRENT_NATIVE_FIXED_EIGHT_SEMANTICS_AND_P09_UNQUALIFIED'}

def require(ok,code='XREF008_PUBLICATION_INVALID'):
    if not ok:raise ValueError(code)

def exact(value,expected,code):require(value==expected,code)

def validate(row):
    require(type(row)is dict and type(row.get('generation'))is int and row['generation']==GENERATION,'XREF008_PUBLICATION_ONLY_FIXED008')
    require(type(row.get('state'))is str and row['state']in STATES and row.get('P09_gate')=='OPEN'and row.get('P10_started')is False
        and type(row.get('accepted_count_delta'))is int and row['accepted_count_delta']==0
        and row.get('Native011_executed')is False and row.get('native_startup_qualified')is False
        and row.get('crossref_semantics_qualified')is False,'XREF008_PUBLICATION_NEVER_AUTHORITY_OR_GATE')
    if row['state'].startswith('CAPTURED_'):
        require(row.get('fixed_eight_executed')is True and type(row.get('captured_cases'))is int
            and row['captured_cases']==8,'XREF008_PUBLICATION_CAPTURE_IS_NOT_SEMANTIC_ACCEPTANCE')

def base(root):
    require(isinstance(root,Path)and root.is_absolute()and root.is_dir()and not root.is_symlink()and not root.is_junction(),'XREF008_PUBLICATION_ROOT')
    require(root.resolve(strict=True)==root,'XREF008_PUBLICATION_ROOT_ALIAS')
    return root

def directory(path,root):
    require(path.is_relative_to(root),'XREF008_PUBLICATION_PATH_SCOPE')
    for item in(path,*path.parents):
        require(item.is_dir()and not item.is_symlink()and not item.is_junction(),'XREF008_PUBLICATION_NO_REPARSE')
        if item==root:break

def write_once(path,data):
    require(0<len(data)<=CHUNK_BYTES,'XREF008_PUBLICATION_SINGLE_WRITE_BOUND')
    with path.open('xb')as stream:
        require(stream.write(data)==len(data),'XREF008_PUBLICATION_COMPLETE_WRITE');stream.flush();os.fsync(stream.fileno())

def read_bound(path,limit):
    require(path.is_file()and not path.is_symlink()and not path.is_junction(),'XREF008_PUBLICATION_REGULAR_PART')
    with path.open('rb')as stream:data=stream.read(limit+1)
    require(0<len(data)<=limit,'XREF008_PUBLICATION_READ_BOUND')
    return data

def retained_row(root):
    """Forensic read only; never publishes, executes or authorizes a stored result."""
    root=base(root);where=root/SPOOL;directory(where,root)
    manifest_raw=read_bound(where/MANIFEST,16384);manifest=json.loads(manifest_raw,object_pairs_hook=compact.unique)
    require(type(manifest)is dict and set(manifest)=={'profile','state','generation','bytes','sha256','parts'}
        and manifest['profile']==PROFILE and manifest['state']=='RAW_ROW_RETAINED_NOT_ACCEPTANCE'
        and type(manifest['generation'])is int and manifest['generation']==GENERATION,'XREF008_PUBLICATION_RETAINED_MANIFEST')
    require(type(manifest['bytes'])is int and 0<manifest['bytes']<=MAX_BYTES
        and type(manifest['parts'])is list and 0<len(manifest['parts'])<=MAX_PARTS,'XREF008_PUBLICATION_RETAINED_BOUND')
    output=bytearray()
    for index,pin in enumerate(manifest['parts']):
        name=f'part-{index:04}.bin'
        require(type(pin)is dict and set(pin)=={'path','bytes','sha256'}and pin['path']==name
            and type(pin['bytes'])is int and 0<pin['bytes']<=CHUNK_BYTES,'XREF008_PUBLICATION_EXACT_PART')
        data=read_bound(where/name,CHUNK_BYTES)
        require(len(data)==pin['bytes']and hashlib.sha256(data).hexdigest()==pin['sha256'],'XREF008_PUBLICATION_RETAINED_PART_INTEGRITY')
        require(len(output)+len(data)<=MAX_BYTES,'XREF008_PUBLICATION_TOTAL_READ_BOUND');output.extend(data)
    data=bytes(output);require(len(data)==manifest['bytes']and hashlib.sha256(data).hexdigest()==manifest['sha256'],'XREF008_PUBLICATION_RETAINED_WHOLE_INTEGRITY')
    row=json.loads(data,object_pairs_hook=compact.unique);validate(row)
    require(compact.raw(row)==data,'XREF008_PUBLICATION_RETAINED_CANONICAL_ROW')
    return row

def publish_final(root,row):
    """New008 only. Does not create a Native claim or permit re-execution on any failure."""
    root=base(root);validate(row);data=compact.raw(row)
    require(0<len(data)<=MAX_BYTES,'XREF008_PUBLICATION_ROW_BOUND')
    where=root/SPOOL;destination=root/OUTPUT;directory(where.parent,root);directory(destination.parent,root)
    require(not destination.exists()and not destination.is_symlink()and not destination.is_junction(),'XREF008_PUBLICATION_FINAL_IMMUTABLE')
    require(not where.exists()and not where.is_symlink()and not where.is_junction(),'XREF008_PUBLICATION_SPOOL_IMMUTABLE_NO_REPLAY')
    where.mkdir();parts=[]
    for index,start in enumerate(range(0,len(data),CHUNK_BYTES)):
        piece=data[start:start+CHUNK_BYTES];name=f'part-{index:04}.bin';write_once(where/name,piece)
        parts.append(dict(path=name,bytes=len(piece),sha256=hashlib.sha256(piece).hexdigest()))
    manifest=dict(profile=PROFILE,state='RAW_ROW_RETAINED_NOT_ACCEPTANCE',generation=GENERATION,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=parts)
    manifest_raw=compact.raw(manifest);require(len(manifest_raw)<=16384,'XREF008_PUBLICATION_MANIFEST_BOUND');write_once(where/MANIFEST,manifest_raw)
    require(compact.raw(retained_row(root))==data,'XREF008_PUBLICATION_PREPUBLISHED_COPY_VERIFIED')
    try:packet=layout.pack(row)
    except(ValueError,TypeError,OverflowError,RecursionError):
        raise ValueError('XREF008_PUBLICATION_ENCODING_FAILED_EXACT_RAW_ROW_RETAINED')from None
    # This packet carries ALL original data; its validity never depends on the private spool.
    return original.publish(root,OUTPUT,packet,NS(require=require,exact=exact))
