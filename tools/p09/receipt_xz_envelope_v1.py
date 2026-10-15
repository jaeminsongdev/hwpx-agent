"""Explicit candidate XZ envelope; no runtime connection or external IO.

Opaque bytes only, not JSON normalization. Decoder allocation/work is bounded;
old zlib envelopes must continue through their original decoder, not this one.
"""
import base64
import binascii
import hashlib
import json
import lzma
import re

SELF="tools/p09/receipt_xz_envelope_v1.py"
SCHEMA="hwpx-agent.p09-runtime-record-envelope-xz/v1"
ENCODING="xz-lzma2-base64"
MAX_BYTES=16*1024*1024
CHUNK_BYTES=64*1024
DICTIONARY_BYTES=8*1024*1024
DECODE_MEMORY_LIMIT=32*1024*1024


def require(ok,label):
    if not ok:raise ValueError("RECEIPT_XZ_"+label)


def unique(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,"DUPLICATE_KEY");result[key]=value
    return result


def encode(raw,checkpoint):
    require(type(raw) is bytes and 0<len(raw)<=MAX_BYTES and callable(checkpoint),"BOUNDED_RAW_AND_GUARD")
    checkpoint()
    compressor=lzma.LZMACompressor(format=lzma.FORMAT_XZ,check=lzma.CHECK_CRC64,
        filters=[dict(id=lzma.FILTER_LZMA2,preset=6,dict_size=DICTIONARY_BYTES)])
    chunks=[]
    for offset in range(0,len(raw),CHUNK_BYTES):
        checkpoint();chunks.append(compressor.compress(raw[offset:offset+CHUNK_BYTES]))
    checkpoint();chunks.append(compressor.flush());compressed=b"".join(chunks)
    checkpoint()
    row=dict(schema_version=SCHEMA,encoding=ENCODING,original_bytes=len(raw),
        original_sha256=hashlib.sha256(raw).hexdigest(),payload=base64.b64encode(compressed).decode("ascii"))
    encoded=(json.dumps(row,ensure_ascii=True,allow_nan=False,separators=(",",":"))+"\n").encode("ascii")
    require(len(encoded)<=MAX_BYTES,"ENCODED_BOUND");checkpoint();return encoded


def decode(raw,checkpoint):
    require(type(raw) is bytes and 0<len(raw)<=MAX_BYTES and callable(checkpoint),"BOUNDED_ENCODED_AND_GUARD")
    checkpoint()
    try:row=json.loads(raw.decode("utf-8"),object_pairs_hook=unique)
    except (UnicodeDecodeError,json.JSONDecodeError):raise ValueError("RECEIPT_XZ_INVALID_JSON") from None
    require(type(row) is dict and set(row)=={"schema_version","encoding","original_bytes","original_sha256","payload"},"CLOSED_ENVELOPE")
    require(row["schema_version"]==SCHEMA and row["encoding"]==ENCODING,"EXPLICIT_XZ_FORMAT")
    size=row["original_bytes"]
    require(type(size) is int and 0<size<=MAX_BYTES,"DECLARED_OUTPUT_BOUND")
    require(type(row["original_sha256"]) is str and re.fullmatch("[0-9a-f]{64}",row["original_sha256"]) is not None,"DECLARED_HASH")
    require(type(row["payload"]) is str and 0<len(row["payload"])<=MAX_BYTES,"PAYLOAD_BOUND")
    checkpoint()
    try:compressed=base64.b64decode(row["payload"],validate=True)
    except (ValueError,binascii.Error):raise ValueError("RECEIPT_XZ_INVALID_BASE64") from None
    require(bool(compressed),"NONEMPTY_COMPRESSED_INPUT")
    checkpoint();decoder=lzma.LZMADecompressor(format=lzma.FORMAT_XZ,memlimit=DECODE_MEMORY_LIMIT)
    output=bytearray()
    try:
        for offset in range(0,len(compressed),CHUNK_BYTES):
            require(not decoder.eof,"TRAILING_OR_CONCATENATED_STREAM")
            pending=compressed[offset:offset+CHUNK_BYTES]
            while True:
                checkpoint();limit=min(CHUNK_BYTES,size-len(output)+1)
                chunk=decoder.decompress(pending,max_length=limit);pending=b""
                require(len(output)+len(chunk)<=size,"EXPANSION_EXCEEDS_DECLARED_SIZE")
                output.extend(chunk)
                require(not decoder.unused_data,"TRAILING_OR_CONCATENATED_STREAM")
                if decoder.eof or decoder.needs_input:break
                require(bool(chunk),"NO_DECOMPRESS_PROGRESS")
        require(decoder.eof,"TRUNCATED_STREAM")
    except lzma.LZMAError:raise ValueError("RECEIPT_XZ_INVALID_OR_OVER_MEMORY_STREAM") from None
    checkpoint()
    require(len(output)==size and hashlib.sha256(output).hexdigest()==row["original_sha256"],"EXACT_ORIGINAL_BYTES_AND_HASH")
    result=bytes(output);checkpoint();return result
