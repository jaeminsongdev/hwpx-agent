"""Future envelope decoder with bounded expanded-output work per checkpoint.

Not connected to product writers/readers or case157; v1 stays immutable.
Wire schema and exact bytes/hash validation unchanged. No external IO/cache.
"""
import base64
import binascii
import hashlib
import json
import zlib
import re
from runtime_record_envelope_v1 import (
    CHUNK_BYTES, MAX_BYTES, SCHEMA, encode, require, unique)

SELF="tools/p09/runtime_record_envelope_v2.py"
TEST="tools/p09/tests/test_runtime_record_envelope_v2.py"

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
            pending=compressed[offset:offset+CHUNK_BYTES]
            while True:
                checkpoint()
                # 입력이 작아도 팽창한 출력 작업은 한 번에 64KiB 이하.
                limit=min(CHUNK_BYTES,size-len(result)+1)
                chunk=inflater.decompress(pending,limit)
                require(len(result)+len(chunk)<=size,"EXPANSION_EXCEEDS_DECLARED_SIZE")
                result.extend(chunk)
                require(not inflater.unused_data,"TRAILING_OR_CONCATENATED_STREAM")
                tail=inflater.unconsumed_tail
                if not tail and len(chunk)<limit:break
                require(bool(chunk) or len(tail)<len(pending),"NO_DECOMPRESS_PROGRESS")
                pending=tail
                # Empty pending drains buffered output until less than limit.
        require(inflater.eof,"TRUNCATED_COMPRESSED_STREAM")
    except zlib.error:raise ValueError("RUNTIME_ENVELOPE_COMPRESSION_INVALID") from None
    checkpoint()
    require(len(result)==size and hashlib.sha256(result).hexdigest()==row["original_sha256"],"EXACT_ORIGINAL_BYTES_AND_HASH")
    result=bytes(result);checkpoint();return result
