"""Lossless inline interning of repeated file pins; original 256KiB publication cap.

Preparation only: not wired into consumed Native generations, no replay/recovery of lost rows.
No external payload, compression, omission, evidence deduplication or status promotion.
"""
import json,re
import compact_receipt_json as compact
import resource_sample_table as samples

PROFILE='hwpx-agent.crossref-inline-file-pin-dictionary/v1'
REF='$p'
MAX_INPUT_BYTES=4*1024*1024
MAX_NODES=100_000
MAX_DEPTH=64
MAX_PINS=4096

def require(ok):
    if not ok:raise ValueError('XREF_INLINE_RECEIPT_INVALID')

def pin(value):
    return (type(value)is dict and set(value)=={'path','bytes','sha256'}
        and type(value['path'])is str and 0<len(value['path'])<=4096
        and type(value['bytes'])is int and 0<=value['bytes']<=2**63-1
        and type(value['sha256'])is str and re.fullmatch('[0-9a-f]{64}',value['sha256'])is not None)

def walk(value,visit):
    nodes=0
    def step(item,depth=0):
        nonlocal nodes
        nodes+=1;require(nodes<=MAX_NODES and depth<=MAX_DEPTH)
        transformed,done=visit(item)
        if done:return transformed
        if type(item)is dict:return {key:step(v,depth+1)for key,v in item.items()}
        if type(item)is list:return [step(v,depth+1)for v in item]
        return item
    return step(value)

def encode(row):
    require(type(row)is dict and type(row.get('state'))is str and len(row)<=256 and all(type(k)is str for k in row))
    raw=compact.raw(row);require(0<len(raw)<=MAX_INPUT_BYTES)
    value=json.loads(raw);has_samples='resource_samples'in value
    if has_samples:value=samples.encode(value)
    pins=[];indices={}
    def intern(item):
        if type(item)is dict:require(REF not in item)
        if not pin(item):return item,False
        key=compact.raw(item)
        if key not in indices:
            require(len(pins)<MAX_PINS);indices[key]=len(pins);pins.append(item)
        return {REF:indices[key]},True
    document=walk(value,intern)
    packet=dict(state=row['state'],profile=PROFILE,root_keys=list(row),sample_columns=has_samples,pins=pins,document=document)
    require(compact.raw(decode(packet))==raw)
    return packet

def decode(packet):
    require(type(packet)is dict and set(packet)=={'state','profile','root_keys','sample_columns','pins','document'}
        and packet['profile']==PROFILE and type(packet['state'])is str and type(packet['sample_columns'])is bool)
    require(len(compact.raw(packet))<=MAX_INPUT_BYTES)
    pins=packet['pins'];require(type(pins)is list and len(pins)<=MAX_PINS and all(pin(p)for p in pins))
    expanded_bytes=0
    def expand(item):
        nonlocal expanded_bytes
        if type(item)is dict and REF in item:
            require(set(item)=={REF} and type(item[REF])is int and 0<=item[REF]<len(pins))
            expanded_bytes+=len(compact.raw(pins[item[REF]]));require(expanded_bytes<=MAX_INPUT_BYTES)
            return dict(pins[item[REF]]),True
        return item,False
    value=walk(packet['document'],expand)
    if packet['sample_columns']:value=samples.decode(value)
    keys=packet['root_keys']
    require(type(value)is dict and type(keys)is list and len(keys)<=256 and all(type(k)is str for k in keys)
        and len(keys)==len(set(keys))and set(keys)==set(value))
    value={k:value[k]for k in keys}
    require(value.get('state')==packet['state']and len(compact.raw(value))<=MAX_INPUT_BYTES)
    return value

def pack(row):return compact.pack(encode(row))
def unpack(packet):return decode(compact.unpack(packet))
