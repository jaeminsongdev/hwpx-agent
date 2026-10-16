"""Lossless columnar pins under the original 16 KiB worker wire ceiling.

Every descriptor/path/size/256-bit hash travels in the packet. Only JSON wire
representation changes; original worker context/hash/Binding bodies still run.
No table reference, omitted row, receipt IO, hash cache or execution permission.
"""
import base64
import hashlib
import json
from types import FunctionType,SimpleNamespace as NS
import zlib

SELF='tools/p09/bounded_binary_capsule_wire_v3.py'
TEST='tools/p09/tests/test_bounded_binary_capsule_wire_v3.py'
SCHEMA='hwpx-agent.p09-bounded-binary-worker-capsule/v3'
COMPACT_SCHEMA='hwpx-agent.p09-compact-worker-capsule-wire/v1'
MAX_BYTES=16384
MAX_EXPANDED_BYTES=131072
MAX_BINDINGS=249
MAGIC=b'P09W3\x00'


def require(ok,label):
    if not ok: raise ValueError('BINARY_CAPSULE_V3_'+label)


def uint(value):
    require(type(value) is int and 0<=value<2**63,'BOUNDED_UINT63')
    data=bytearray()
    while value>=128: data.append((value&127)|128); value>>=7
    data.append(value); return bytes(data)


class Cursor:
    def __init__(self,data): self.data=data; self.offset=0
    def take(self,size):
        require(type(size) is int and 0<=size<=MAX_EXPANDED_BYTES and self.offset+size<=len(self.data),'COMPLETE_BOUNDED_BINARY_FIELD')
        value=self.data[self.offset:self.offset+size]; self.offset+=size; return value
    def uint(self):
        start=self.offset; value=0
        for shift in range(0,63,7):
            byte=self.take(1)[0]; value|=(byte&127)<<shift
            if byte<128:
                require(self.data[start:self.offset]==uint(value),'CANONICAL_UINT63'); return value
        raise ValueError('BINARY_CAPSULE_V3_UINT_TOO_LONG')


def canonical(value):
    return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')


def compact_pins(row):
    require(type(row) is dict and set(row)=={'schema_version','context','descriptor_context','manifest','authority','prior','bindings'}
        and row['schema_version']==COMPACT_SCHEMA,'CLOSED_ORIGINAL_COMPACT_SHAPE')
    context,common,rows=row['context'],row['descriptor_context'],row['bindings']
    require(type(context) is list and len(context)==3 and type(context[0]) is str and 0<len(context[0])<=256
        and type(context[1]) is int and 1<=context[1]<=249 and type(context[2]) is int and 0<=context[2]<249,'TYPED_CONTEXT')
    require(type(common) is list and len(common)==2 and type(common[0]) is str and 0<len(common[0])<=256
        and type(common[1]) is int and common[1]==context[1],'TYPED_DESCRIPTOR_CONTEXT')
    require(type(rows) is list and 0<len(rows)<=MAX_BINDINGS and all(type(p) is list and len(p)==2 for p in rows),'ALL_BOUNDED_PAIRS')
    pins=[row['manifest'],row['authority'],row['prior']]+[p[0] for p in rows]+[p[1] for p in rows]
    for p in pins:
        require(type(p) is list and len(p)==3 and type(p[0]) is str and 0<len(p[0].encode('utf-8'))<=16384
            and type(p[1]) is int and 0<p[1]<2**63 and type(p[2]) is str and len(p[2])==64
            and all(c in '0123456789abcdef' for c in p[2]),'EXACT_ALL_PIN_FIELDS')
    require(len(canonical(row))<=MAX_EXPANDED_BYTES,'ORIGINAL_COMPACT_JSON128K')
    return pins


def pack_binary(row,checkpoint):
    checkpoint(); pins=compact_pins(row)
    header=canonical(dict(context=row['context'],descriptor_context=row['descriptor_context'],count=len(row['bindings'])))
    data=bytearray(MAGIC+uint(len(header))+header); previous=b''
    # Semantic paths, then physical paths: shared prefixes are encoded once,
    # while the original order and all exact Unicode bytes remain invertible.
    for path,size,digest in pins:
        checkpoint(); path=path.encode('utf-8'); common=0
        while common<min(len(previous),len(path)) and previous[common]==path[common]: common+=1
        suffix=path[common:]; data.extend(uint(common)+uint(len(suffix))+suffix); previous=path
    for path,size,digest in pins: checkpoint(); data.extend(uint(size))
    for path,size,digest in pins: checkpoint(); data.extend(bytes.fromhex(digest))
    require(0<len(data)<=MAX_EXPANDED_BYTES,'BINARY_EXPANSION128K'); checkpoint(); return bytes(data)


def unpack_binary(raw,checkpoint):
    checkpoint(); require(type(raw) is bytes and 0<len(raw)<=MAX_EXPANDED_BYTES,'BOUNDED_BINARY128K')
    cursor=Cursor(raw); require(cursor.take(len(MAGIC))==MAGIC,'EXACT_BINARY_MAGIC')
    length=cursor.uint(); require(length<=4096,'SMALL_CLOSED_HEADER')
    try: header=json.loads(cursor.take(length).decode('ascii'),object_pairs_hook=unique)
    except (UnicodeError,json.JSONDecodeError): raise ValueError('BINARY_CAPSULE_V3_INVALID_HEADER') from None
    require(type(header) is dict and set(header)=={'context','descriptor_context','count'}
        and type(header['count']) is int and 0<header['count']<=MAX_BINDINGS,'CLOSED_HEADER_AND_COUNT')
    count=header['count']; paths=[]; previous=b''
    for i in range(3+2*count):
        checkpoint(); common=cursor.uint(); length=cursor.uint()
        require(common<=len(previous) and common+length<=16384,'BOUNDED_PATH_PREFIX_AND_SUFFIX')
        previous=previous[:common]+cursor.take(length)
        try: paths.append(previous.decode('utf-8'))
        except UnicodeError: raise ValueError('BINARY_CAPSULE_V3_INVALID_PATH_UTF8') from None
    sizes=[]
    for path in paths: checkpoint(); sizes.append(cursor.uint())
    pins=[]
    for path,size in zip(paths,sizes): checkpoint(); pins.append([path,size,cursor.take(32).hex()])
    require(cursor.offset==len(raw),'NO_TRAILING_BINARY_BYTES')
    row=dict(schema_version=COMPACT_SCHEMA,context=header['context'],descriptor_context=header['descriptor_context'],
        manifest=pins[0],authority=pins[1],prior=pins[2],bindings=[[pins[3+i],pins[3+count+i]] for i in range(count)])
    compact_pins(row); require(pack_binary(row,checkpoint)==raw,'EXACT_CANONICAL_BINARY_INVERSE'); return row


def unique(pairs):
    result={}
    for key,value in pairs: require(key not in result,'DUPLICATE_KEY'); result[key]=value
    return result


def encode_compact(row,checkpoint):
    raw=pack_binary(row,checkpoint); compressed=zlib.compress(raw,9)
    outer=dict(schema_version=SCHEMA,raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),
        zlib_base85=base64.b85encode(compressed).decode('ascii'))
    data=canonical(outer); require(0<len(data)<=MAX_BYTES,'ORIGINAL_16K_TRANSPORT'); checkpoint(); return data.decode('ascii')


def decode_compact(data,checkpoint,**options):
    require(type(data) is str and 0<len(data.encode('ascii'))<=MAX_BYTES,'ORIGINAL_16K_INPUT'); checkpoint()
    row=json.loads(data,**options)
    require(type(row) is dict and set(row)=={'schema_version','raw_bytes','raw_sha256','zlib_base85'} and row['schema_version']==SCHEMA,'CLOSED_V3_WIRE')
    require(type(row['raw_bytes']) is int and 0<row['raw_bytes']<=MAX_EXPANDED_BYTES and type(row['raw_sha256']) is str
        and len(row['raw_sha256'])==64 and all(c in '0123456789abcdef' for c in row['raw_sha256'])
        and type(row['zlib_base85']) is str,'BOUNDED_WIRE_FIELDS')
    try: compressed=base64.b85decode(row['zlib_base85'])
    except (ValueError,UnicodeError): raise ValueError('BINARY_CAPSULE_V3_INVALID_BASE85') from None
    require(base64.b85encode(compressed).decode('ascii')==row['zlib_base85'],'CANONICAL_BASE85')
    decoder=zlib.decompressobj(); checkpoint()
    try: raw=decoder.decompress(compressed,MAX_EXPANDED_BYTES+1)
    except zlib.error: raise ValueError('BINARY_CAPSULE_V3_INVALID_ZLIB') from None
    require(decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data and len(raw)==row['raw_bytes']<=MAX_EXPANDED_BYTES,'COMPLETE_BOUNDED_ZLIB')
    require(hashlib.sha256(raw).hexdigest()==row['raw_sha256'],'EXACT_EXPANDED_SHA256'); checkpoint()
    result=unpack_binary(raw,checkpoint); require(encode_compact(result,checkpoint)==data,'WHOLE_CANONICAL_WIRE_INVERSE'); return result


def describe_compact(row,checkpoint):
    raw=pack_binary(row,checkpoint); encoded=encode_compact(row,checkpoint)
    return dict(expanded_bytes=len(raw),compact_JSON_bytes=len(canonical(row)),compressed_bytes=len(zlib.compress(raw,9)),
        wire_bytes=len(encoded.encode('ascii')),wire_limit_bytes=MAX_BYTES,expanded_limit_bytes=MAX_EXPANDED_BYTES,fits_wire=True)


def connect(worker,checkpoint):
    require(worker.MAX_BYTES==MAX_BYTES,'UNCHANGED_ORIGINAL_WORKER_BOUND')
    old=worker.encode.__globals__['json']
    require(worker.decode.__globals__['json'] is old,'ONE_CURRENT_WIRE_NAMESPACE')
    require(old.dumps.__code__.co_filename.replace('\\','/').endswith('bounded_successor_capsule_wire_v2.py'),'EXACT_PREDECESSOR_V2_DEPENDENCY')
    closure=lambda fn:dict(zip(fn.__code__.co_freevars,(c.cell_contents for c in fn.__closure__ or ())))
    pack,unpack=closure(old.dumps)['pack'],closure(old.loads)['unpack']
    class WireJSON:
        @staticmethod
        def dumps(row,**options):
            require(options==dict(ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False),'ORIGINAL_JSON_OPTIONS')
            return encode_compact(pack(row),checkpoint)
        @staticmethod
        def loads(data,**options): return unpack(decode_compact(data,checkpoint,**options))
    values=dict(vars(worker))
    for name in ('encode','decode'):
        original=getattr(worker,name)
        require(type(original) is FunctionType and original.__globals__.get('__name__','').startswith('p09_exact_'),'PRIVATE_ORIGINAL_ENCODER_DECODER')
        fn=FunctionType(original.__code__,dict(original.__globals__,json=WireJSON),original.__name__,original.__defaults__,original.__closure__)
        fn.__kwdefaults__=original.__kwdefaults__; values[name]=fn
        require(fn.__code__ is original.__code__ and fn.__closure__ is original.__closure__ and fn.__defaults__ is original.__defaults__,'WHOLE_ORIGINAL_CODE_DEFAULTS_CLOSURE')
    return NS(**values),dict(wire_schema=SCHEMA,all_descriptors_paths_sizes_and256bit_hashes_carried=True,
        descriptor_rows_omitted=0,external_table_or_receipt_lookup=False,original_encode_decode_code_defaults_closure_retained=True,
        maximum_wire_bytes=MAX_BYTES,maximum_binary_and_compact_JSON_bytes=MAX_EXPANDED_BYTES,
        default_modules_mutated=False,worker_reconstruction_or_Native_or_GO_qualified=False)
