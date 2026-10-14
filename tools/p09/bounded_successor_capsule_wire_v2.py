"""Lossless bounded wire around the unchanged complete compact capsule.

Same original encode/decode body, context, transport hash and Binding checks.
Never drop rows or increase the original 16 KiB transport ceiling.
"""
import base64
import hashlib
import json
from types import FunctionType,SimpleNamespace as NS
import zlib

SELF="tools/p09/bounded_successor_capsule_wire_v2.py"
TEST="tools/p09/tests/test_bounded_successor_capsule_wire_v2.py"
SCHEMA="hwpx-agent.p09-bounded-compressed-worker-capsule/v2"
MAX_BYTES=16384
MAX_EXPANDED_BYTES=131072


def require(value,label):
    if not value:raise ValueError("SUCCESSOR_WIRE_V2_"+label)


def encode_compact(compact,checkpoint):
    checkpoint()
    raw=json.dumps(compact,ensure_ascii=True,sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")
    require(0<len(raw)<=MAX_EXPANDED_BYTES,"BOUNDED_EXPANDED_BYTES")
    compressed=zlib.compress(raw,9)
    row=dict(schema_version=SCHEMA,raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),
        zlib_base64=base64.b64encode(compressed).decode("ascii"))
    encoded=json.dumps(row,ensure_ascii=True,sort_keys=True,separators=(",",":"),allow_nan=False)
    require(0<len(encoded.encode("ascii"))<=MAX_BYTES,"ORIGINAL_16K_TRANSPORT")
    checkpoint()
    return encoded


def decode_compact(data,checkpoint,**options):
    require(type(data) is str and 0<len(data.encode("ascii"))<=MAX_BYTES,"ORIGINAL_16K_INPUT")
    checkpoint()
    row=json.loads(data,**options)
    require(type(row) is dict and set(row)=={"schema_version","raw_bytes","raw_sha256","zlib_base64"}
        and row["schema_version"]==SCHEMA,"CLOSED_WIRE_V2")
    require(type(row["raw_bytes"]) is int and 0<row["raw_bytes"]<=MAX_EXPANDED_BYTES
        and type(row["raw_sha256"]) is str and len(row["raw_sha256"])==64
        and all(c in "0123456789abcdef" for c in row["raw_sha256"])
        and type(row["zlib_base64"]) is str,"BOUNDED_WIRE_FIELDS")
    try:compressed=base64.b64decode(row["zlib_base64"],validate=True)
    except (ValueError,base64.binascii.Error):raise ValueError("SUCCESSOR_WIRE_V2_BASE64") from None
    decoder=zlib.decompressobj()
    try:raw=decoder.decompress(compressed,MAX_EXPANDED_BYTES+1)
    except zlib.error:raise ValueError("SUCCESSOR_WIRE_V2_ZLIB") from None
    require(decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data
        and len(raw)==row["raw_bytes"]<=MAX_EXPANDED_BYTES,"EXACT_COMPLETE_BOUNDED_EXPANSION")
    require(hashlib.sha256(raw).hexdigest()==row["raw_sha256"],"EXACT_EXPANDED_HASH")
    try:text=raw.decode("ascii")
    except UnicodeError:raise ValueError("SUCCESSOR_WIRE_V2_ASCII") from None
    result=json.loads(text,**options)
    # Exact inverse, not a lossy projection or permissive second schema.
    require(encode_compact(result,checkpoint)==data,"CANONICAL_LOSSLESS_INVERSE")
    checkpoint()
    return result


def connect(worker,checkpoint):
    require(worker.MAX_BYTES==MAX_BYTES,"ORIGINAL_WORKER_BOUND")
    old_json=worker.encode.__globals__["json"]
    require(worker.decode.__globals__["json"] is old_json,"ONE_ORIGINAL_COMPACT_JSON_NAMESPACE")
    pack=old_json.dumps.__globals__["pack"]
    unpack=old_json.loads.__globals__["unpack"]
    class WireJSON:
        @staticmethod
        def dumps(row,**options):
            require(options==dict(ensure_ascii=True,sort_keys=True,separators=(",",":"),allow_nan=False),
                "ORIGINAL_ENCODER_JSON_OPTIONS")
            return encode_compact(pack(row),checkpoint)
        @staticmethod
        def loads(data,**options):return unpack(decode_compact(data,checkpoint,**options))
    values=dict(vars(worker))
    for name in ("encode","decode"):
        original=getattr(worker,name)
        env=dict(original.__globals__,json=WireJSON)
        fn=FunctionType(original.__code__,env,argdefs=original.__defaults__,closure=original.__closure__)
        fn.__kwdefaults__=original.__kwdefaults__
        require(fn.__code__ is original.__code__ and fn.__defaults__ is original.__defaults__
            and fn.__closure__ is original.__closure__,"WHOLE_ORIGINAL_FUNCTION_RETAINED")
        values[name]=fn
    return NS(**values),dict(wire_schema=SCHEMA,maximum_wire_bytes=MAX_BYTES,
        maximum_expanded_compact_bytes=MAX_EXPANDED_BYTES,all_original_compact_pack_unpack_checks_retained=True,
        original_encode_decode_code_defaults_closure_retained=True,descriptor_rows_removed=0,
        default_namespace_mutated=False,actual_worker_product_or_Native_qualified=False)


def install(connections,checkpoint):
    """Only a private namespace may receive this explicit wire dependency."""
    original=connections.worker_api
    require(original.__globals__.get("__name__","").startswith("p09_exact_"),"PRIVATE_CONNECTION_NAMESPACE_ONLY")
    def worker_api(*args,**kwargs):
        worker,proof=original(*args,**kwargs)
        linked,new=connect(worker,checkpoint)
        return linked,dict(proof,bounded_compressed_wire_proof=new)
    original.__globals__["worker_api"]=worker_api
    connections.worker_api=worker_api
    return connections
