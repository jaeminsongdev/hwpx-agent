"""Bounded self-contained JSON DAG: no compression, external carrier or status change.

Repeated scalars AND complete containers share backward-only nodes. Every key,
value, order, sample and original status round-trips. Old567 and consumed010
sources stay unchanged. Expanded bytes/nodes/depth and original writer cap stay.
"""
import hashlib,json,math
import compact_receipt_json as compact

PROFILE='hwpx-agent.crossref-inline-json-dag/v1'
MAX_INPUT_BYTES=4*1024*1024
MAX_NODES=100000
MAX_DEPTH=64

def require(ok,code='INVALID'):
    if not ok:raise ValueError('XREF_DAG610_'+code)

def encode(row,checkpoint=lambda:None):
    require(type(row)is dict and type(row.get('state'))is str,'ROOT_STATE')
    data=compact.raw(row);require(0<len(data)<=MAX_INPUT_BYTES,'RAW_LIMIT')
    nodes=[];intern={};visits=0
    def visit(value,depth):
        nonlocal visits
        visits+=1;require(visits<=MAX_NODES and depth<=MAX_DEPTH,'EXPANSION_LIMIT')
        if visits%128==0:checkpoint()
        if type(value)is dict:
            require(all(type(k)is str for k in value),'STRING_KEYS')
            node=[2,[ref for key,item in value.items()for ref in(visit(key,depth+1),visit(item,depth+1))]]
        elif type(value)is list:node=[1,[visit(item,depth+1)for item in value]]
        else:
            require(value is None or type(value)in(str,int,bool,float),'SCALAR_TYPE')
            require(type(value)is not float or math.isfinite(value),'FINITE_NUMBER');node=[0,value]
        key=compact.raw(node)
        if key not in intern:
            require(len(nodes)<MAX_NODES,'NODE_LIMIT');intern[key]=len(nodes);nodes.append(node)
        return intern[key]
    root=visit(row,0);checkpoint()
    return dict(state=row['state'],profile=PROFILE,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),nodes=nodes,root=root)

def decode(packet,checkpoint=lambda:None):
    require(type(packet)is dict and set(packet)=={'state','profile','raw_bytes','raw_sha256','nodes','root'},'ENVELOPE')
    require(packet['profile']==PROFILE and type(packet['state'])is str and type(packet['raw_bytes'])is int
        and 0<packet['raw_bytes']<=MAX_INPUT_BYTES,'PROFILE_OR_LIMIT')
    require(type(packet['raw_sha256'])is str and len(packet['raw_sha256'])==64
        and all(ch in '0123456789abcdef'for ch in packet['raw_sha256']),'HASH_SHAPE')
    require(len(compact.raw(packet))<=MAX_INPUT_BYTES,'ENCODED_LIMIT')
    nodes=packet['nodes'];root=packet['root']
    require(type(nodes)is list and 0<len(nodes)<=MAX_NODES and type(root)is int and root==len(nodes)-1,'ROOT_NODE')
    keys=set();scalar_bytes={}
    for i,node in enumerate(nodes):
        if i%128==0:checkpoint()
        require(type(node)is list and len(node)==2 and type(node[0])is int and node[0]in(0,1,2),'NODE_SHAPE')
        tag,value=node;key=compact.raw(node);require(key not in keys,'DUPLICATE_NODE');keys.add(key)
        if tag==0:
            require(value is None or type(value)in(str,int,bool,float),'SCALAR_TYPE')
            require(type(value)is not float or math.isfinite(value),'FINITE_NUMBER');scalar_bytes[i]=len(compact.raw(value))
        else:
            require(type(value)is list and all(type(ref)is int and 0<=ref<i for ref in value),'BACK_REFERENCES_ONLY')
            if tag==2:
                require(len(value)%2==0,'DICT_PAIRS')
                require(all(nodes[ref][0]==0 and type(nodes[ref][1])is str for ref in value[::2]),'STRING_KEY_REFERENCES')
                names=[nodes[ref][1]for ref in value[::2]];require(len(names)==len(set(names)),'DUPLICATE_KEY')
    visits=0;expanded=0;seen=set()
    def charge(size):
        nonlocal expanded
        expanded+=size;require(expanded<=packet['raw_bytes'],'EXPANDED_BYTE_LIMIT')
    def expand(index,depth):
        nonlocal visits
        visits+=1;require(visits<=MAX_NODES and depth<=MAX_DEPTH,'EXPANSION_LIMIT');seen.add(index)
        if visits%128==0:checkpoint()
        tag,value=nodes[index]
        if tag==0:charge(scalar_bytes[index]);return value
        if tag==1:
            charge(2+max(0,len(value)-1));return [expand(ref,depth+1)for ref in value]
        charge(2+max(0,len(value)//2-1)+len(value)//2)
        return {expand(value[i],depth+1):expand(value[i+1],depth+1)for i in range(0,len(value),2)}
    row=expand(root,0);checkpoint();require(len(seen)==len(nodes),'NO_UNREACHABLE_NODES')
    require(type(row)is dict and row.get('state')==packet['state'],'STATE_UNCHANGED')
    data=compact.raw(row)
    require(expanded==len(data)==packet['raw_bytes']and hashlib.sha256(data).hexdigest()==packet['raw_sha256'],'WHOLE_LOSSLESS_INTEGRITY')
    return row

def pack(row,checkpoint=lambda:None):
    value=encode(row,checkpoint);require(compact.raw(decode(value,checkpoint))==compact.raw(row),'ROUND_TRIP')
    return compact.pack(value)

def unpack(packet,checkpoint=lambda:None):return decode(compact.unpack(packet),checkpoint)
