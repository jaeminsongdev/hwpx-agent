"""Bounded lossless carrier610; consumed010 and legacy567 stay unchanged.

Explicit NEW compression profile, not silently substituted in old decoders.
All original bytes/statuses remain. 4MiB expansion, 100000 nodes, 64 depth,
180000 compressed bytes and the original 256KiB writer cap stay enforced.
"""
import base64,binascii,hashlib,json,math,zlib
import compact_receipt_json as compact
PROFILE='hwpx-agent.crossref-bounded-lossless-deflate/v1'
MAX_INPUT_BYTES=4*1024*1024
MAX_NODES=100000
MAX_DEPTH=64
MAX_COMPRESSED_BYTES=180000
CHUNK_BYTES=65536

def require(ok,code='INVALID'):
    if not ok:raise ValueError('XREF_LOSSLESS610_'+code)

def validate_tree(value,checkpoint):
    count=0
    def visit(item,depth):
        nonlocal count
        count+=1;require(count<=MAX_NODES and depth<=MAX_DEPTH,'TREE_LIMIT')
        if count%128==0:checkpoint()
        if type(item)is dict:
            require(all(type(k)is str for k in item),'STRING_KEYS')
            for key,child in item.items():visit(key,depth+1);visit(child,depth+1)
        elif type(item)is list:
            for child in item:visit(child,depth+1)
        else:
            require(item is None or type(item)in(str,int,float,bool),'SCALAR_TYPE')
            require(type(item)is not float or math.isfinite(item),'FINITE_NUMBER')
    visit(value,0);checkpoint();return count

def encode(row,checkpoint=lambda:None):
    require(type(row)is dict and type(row.get('state'))is str,'ROOT_STATE')
    validate_tree(row,checkpoint);data=compact.raw(row);require(0<len(data)<=MAX_INPUT_BYTES,'RAW_LIMIT')
    compressor=zlib.compressobj(level=1,wbits=zlib.MAX_WBITS);pieces=[];size=0
    for offset in range(0,len(data),CHUNK_BYTES):
        checkpoint();piece=compressor.compress(data[offset:offset+CHUNK_BYTES]);size+=len(piece)
        require(size<=MAX_COMPRESSED_BYTES,'COMPRESSED_LIMIT');pieces.append(piece)
    checkpoint();piece=compressor.flush();size+=len(piece);require(0<size<=MAX_COMPRESSED_BYTES,'COMPRESSED_LIMIT');pieces.append(piece)
    compressed=b''.join(pieces)
    return dict(state=row['state'],profile=PROFILE,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),
        compressed_bytes=len(compressed),payload_base64=base64.b64encode(compressed).decode('ascii'))

def decode(packet,checkpoint=lambda:None):
    require(type(packet)is dict and set(packet)=={'state','profile','raw_bytes','raw_sha256','compressed_bytes','payload_base64'},'ENVELOPE')
    require(packet['profile']==PROFILE and type(packet['state'])is str and type(packet['raw_bytes'])is int
        and 0<packet['raw_bytes']<=MAX_INPUT_BYTES,'PROFILE_OR_RAW_LIMIT')
    require(type(packet['compressed_bytes'])is int and 0<packet['compressed_bytes']<=MAX_COMPRESSED_BYTES,'COMPRESSED_LIMIT')
    require(type(packet['raw_sha256'])is str and len(packet['raw_sha256'])==64
        and all(ch in '0123456789abcdef'for ch in packet['raw_sha256']),'HASH_SHAPE')
    text=packet['payload_base64'];require(type(text)is str and 0<len(text)<=4*((MAX_COMPRESSED_BYTES+2)//3),'BASE64_LIMIT')
    try:compressed=base64.b64decode(text,validate=True)
    except(binascii.Error,ValueError,UnicodeError):raise ValueError('XREF_LOSSLESS610_BASE64_INVALID')from None
    require(len(compressed)==packet['compressed_bytes']and base64.b64encode(compressed).decode('ascii')==text,'BASE64_CANONICAL_LENGTH')
    decompressor=zlib.decompressobj(wbits=zlib.MAX_WBITS);data=bytearray()
    try:
        for offset in range(0,len(compressed),CHUNK_BYTES):
            checkpoint()
            piece=decompressor.decompress(compressed[offset:offset+CHUNK_BYTES],packet['raw_bytes']-len(data)+1)
            require(len(data)+len(piece)<=packet['raw_bytes'],'EXPANDED_BYTE_LIMIT');data.extend(piece)
            require(not decompressor.unconsumed_tail and not decompressor.unused_data,'NO_TRAILING_OR_CONCATENATED_STREAM')
    except zlib.error:raise ValueError('XREF_LOSSLESS610_DEFLATE_INVALID')from None
    # No unbounded flush(): a complete zlib stream already emitted all bytes.
    require(decompressor.eof and len(data)==packet['raw_bytes'],'COMPLETE_BOUNDED_STREAM')
    raw=bytes(data);checkpoint();require(hashlib.sha256(raw).hexdigest()==packet['raw_sha256'],'WHOLE_RAW_HASH')
    try:row=json.loads(raw.decode('ascii'),object_pairs_hook=compact.unique,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('XREF_LOSSLESS610_NONFINITE')))
    except(UnicodeError,RecursionError,json.JSONDecodeError):raise ValueError('XREF_LOSSLESS610_JSON_INVALID')from None
    validate_tree(row,checkpoint);require(type(row)is dict and row.get('state')==packet['state']and compact.raw(row)==raw,'STATE_AND_CANONICAL_BYTES_UNCHANGED')
    return row

def pack(row,checkpoint=lambda:None):
    packet=encode(row,checkpoint);require(compact.raw(decode(packet,checkpoint))==compact.raw(row),'ROUND_TRIP')
    return compact.pack(packet)

def unpack(packet,checkpoint=lambda:None):return decode(compact.unpack(packet),checkpoint)
