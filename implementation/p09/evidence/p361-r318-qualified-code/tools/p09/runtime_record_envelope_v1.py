"""Bounded lossless future runtime-record envelope,not connected to a writer.

Fresh encode/decode per call;no bytes/hash/JSON cache,threads or external IO.
Opaque serializer bytes round-trip exactly;JSON validation stays with the
original caller. Encoding is explicit and must not be relabelled as an old
plain-JSON receipt by a future integration.
"""
import base64
import binascii
import hashlib
import json
import re
import zlib

SELF="tools/p09/runtime_record_envelope_v1.py"
TEST="tools/p09/tests/test_runtime_record_envelope_v1.py"
SCHEMA="hwpx-agent.p09-runtime-record-envelope/v1"
MAX_BYTES=16*1024*1024
CHUNK_BYTES=64*1024

def require(ok,code):
    if not ok:raise ValueError("RUNTIME_ENVELOPE_"+code)

def encode(raw,checkpoint):
    require(type(raw) is bytes and 0<len(raw)<=MAX_BYTES and callable(checkpoint),"RAW_BYTES_AND_GUARD")
    checkpoint()
    compressor=zlib.compressobj(level=1)
    chunks=[]
    for offset in range(0,len(raw),CHUNK_BYTES):
        checkpoint();chunks.append(compressor.compress(raw[offset:offset+CHUNK_BYTES]))
    checkpoint();chunks.append(compressor.flush());compressed=b"".join(chunks)
    checkpoint()
    row=dict(schema_version=SCHEMA,encoding="zlib-base64",original_bytes=len(raw),
        original_sha256=hashlib.sha256(raw).hexdigest(),payload=base64.b64encode(compressed).decode("ascii"))
    result=(json.dumps(row,ensure_ascii=True,allow_nan=False,separators=(",",":"))+"\n").encode("utf-8")
    require(len(result)<=MAX_BYTES,"ENCODED_INPUT_BUDGET")
    checkpoint();return result

def unique(pairs):
    out={}
    for key,value in pairs:
        require(key not in out,"DUPLICATE_ENVELOPE_KEY")
        out[key]=value
    return out

def decode(raw,checkpoint):
    require(type(raw) is bytes and 0<len(raw)<=MAX_BYTES and callable(checkpoint),"ENCODED_BYTES_AND_GUARD")
    checkpoint()
    try:row=json.loads(raw.decode("utf-8"),object_pairs_hook=unique)
    except (UnicodeDecodeError,json.JSONDecodeError):raise ValueError("RUNTIME_ENVELOPE_JSON_INVALID") from None
    require(type(row) is dict and set(row)=={"schema_version","encoding","original_bytes","original_sha256","payload"},"CLOSED_ENVELOPE")
    require(row["schema_version"]==SCHEMA and row["encoding"]=="zlib-base64","EXPLICIT_FORMAT")
    size=row["original_bytes"]
    require(type(size) is int and 0<size<=MAX_BYTES,"EXPANDED_INPUT_BUDGET")
    require(type(row["original_sha256"]) is str and re.fullmatch("[0-9a-f]{64}",row["original_sha256"]),"ORIGINAL_HASH_SHAPE")
    require(type(row["payload"]) is str and 0<len(row["payload"])<=MAX_BYTES,"PAYLOAD_BUDGET")
    checkpoint()
    try:compressed=base64.b64decode(row["payload"],validate=True)
    except (ValueError,binascii.Error):raise ValueError("RUNTIME_ENVELOPE_BASE64_INVALID") from None
    inflater=zlib.decompressobj();result=bytearray()
    try:
        for offset in range(0,len(compressed),CHUNK_BYTES):
            checkpoint()
            chunk=inflater.decompress(compressed[offset:offset+CHUNK_BYTES],size-len(result)+1)
            require(len(result)+len(chunk)<=size and not inflater.unconsumed_tail,"EXPANSION_EXCEEDS_DECLARED_SIZE")
            result.extend(chunk)
            require(not inflater.unused_data,"TRAILING_OR_CONCATENATED_STREAM")
        require(inflater.eof,"TRUNCATED_COMPRESSED_STREAM")
    except zlib.error:raise ValueError("RUNTIME_ENVELOPE_COMPRESSION_INVALID") from None
    checkpoint()
    require(len(result)==size and hashlib.sha256(result).hexdigest()==row["original_sha256"],"EXACT_ORIGINAL_BYTES_AND_HASH")
    result=bytes(result);checkpoint();return result
