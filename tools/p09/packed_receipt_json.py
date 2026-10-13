"""P221: 전체 JSON 값을 gzip/base64 carrier로 무손실 저장. 원 파일 재작성 없음.

원 compact writer/checkpoint를 재사용한다. carrier/해제 JSON 각각16MiB 이내,
inflate 호출64KiB 이내다. SHA/EOF/추가 데이터/원 compact 표현까지 확인한다.
인증·보안 sandbox·CPU 개선 증거가 아니며 실패를 숨기거나 재시도하지 않는다.
"""
import base64
import hashlib
import json
import re
import zlib
import receipt_compact_json as compact

SELF = 'tools/p09/packed_receipt_json.py'
TEST = 'tools/p09/tests/test_packed_receipt_json.py'
SCHEMA = 'hwpx-agent.p09-lossless-gzip-json-carrier/v1'
MAX_BYTES = 16 * 1024 * 1024
INFLATE_BYTES = 65536
LEVEL = 1
KEYS = {'schema_version', 'codec', 'compression_level', 'raw_json_bytes', 'raw_json_sha256', 'gzip_bytes', 'payload_base64'}


def require(ok, code):
    if not ok:
        raise ValueError('PACKED_RECEIPT_' + code)


def pack(document, checkpoint):
    require(callable(checkpoint), 'ORIGINAL_CHECKPOINT')
    checkpoint()
    compressor = zlib.compressobj(LEVEL, zlib.DEFLATED, 31)
    digest = hashlib.sha256()
    raw_size = compressed_size = 0
    parts = []
    def append(data):
        nonlocal compressed_size
        compressed_size += len(data)
        require(compressed_size <= MAX_BYTES, 'COMPRESSED_BUDGET')
        if data:
            parts.append(data)
    class Sink:
        def write(self, text):
            nonlocal raw_size
            checkpoint()
            data = text.encode('ascii')
            raw_size += len(data)
            require(0 < raw_size <= MAX_BYTES, 'RAW_JSON_BUDGET')
            digest.update(data)
            append(compressor.compress(data))
            checkpoint()
            return len(text)
    try:
        raw_stats = compact.dump(document, Sink(), checkpoint=checkpoint, indent=2)
        checkpoint()
        append(compressor.flush())
        payload = base64.b64encode(b''.join(parts)).decode('ascii')
        require(len(payload) + 1024 <= MAX_BYTES, 'CARRIER_PARSE_BUDGET')
        checkpoint()
    except zlib.error:
        raise ValueError('PACKED_RECEIPT_COMPRESS_FAILURE') from None
    carrier = dict(schema_version=SCHEMA, codec='gzip-base64-canonical-ascii-json',
        compression_level=LEVEL, raw_json_bytes=raw_size, raw_json_sha256=digest.hexdigest(),
        gzip_bytes=compressed_size, payload_base64=payload)
    return carrier, raw_stats


def unpack(carrier, checkpoint):
    require(callable(checkpoint) and isinstance(carrier, dict) and set(carrier) == KEYS, 'EXACT_CARRIER_KEYS')
    require(carrier['schema_version'] == SCHEMA and carrier['codec'] == 'gzip-base64-canonical-ascii-json'
        and type(carrier['compression_level']) is int and carrier['compression_level'] == LEVEL, 'EXACT_CODEC')
    size = carrier['raw_json_bytes']
    compressed_size = carrier['gzip_bytes']
    sha = carrier['raw_json_sha256']
    payload = carrier['payload_base64']
    require(type(size) is int and 0 < size <= MAX_BYTES
        and type(compressed_size) is int and 0 < compressed_size <= MAX_BYTES
        and isinstance(sha, str) and re.fullmatch('[0-9a-f]{64}', sha) is not None
        and isinstance(payload, str) and payload.isascii() and len(payload) + 1024 <= MAX_BYTES, 'DECLARED_BUDGETS')
    checkpoint()
    try:
        pending = base64.b64decode(payload, validate=True)
    except ValueError:
        raise ValueError('PACKED_RECEIPT_INVALID_BASE64') from None
    require(len(pending) == compressed_size
        and base64.b64encode(pending).decode('ascii') == payload, 'CANONICAL_BASE64_AND_SIZE')
    decoder = zlib.decompressobj(31)
    raw = bytearray()
    digest = hashlib.sha256()
    try:
        while True:
            checkpoint()
            before = len(pending)
            # +1 detects a false declared size without unbounded inflate.
            chunk = decoder.decompress(pending, min(INFLATE_BYTES, size - len(raw) + 1))
            require(len(raw) + len(chunk) <= size and chunk.isascii(), 'INFLATE_LENGTH_AND_ASCII')
            raw.extend(chunk)
            digest.update(chunk)
            pending = decoder.unconsumed_tail
            checkpoint()
            if decoder.eof:
                require(not decoder.unused_data and not pending, 'NO_TRAILING_OR_CONCATENATED_GZIP')
                break
            require(bool(chunk) or len(pending) < before, 'INCOMPLETE_OR_NONPROGRESS_GZIP')
    except zlib.error:
        raise ValueError('PACKED_RECEIPT_INVALID_GZIP') from None
    require(len(raw) == size and digest.hexdigest() == sha, 'FULL_RAW_SIZE_AND_SHA')
    checkpoint()
    try:
        document = json.loads(raw.decode('ascii'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError('PACKED_RECEIPT_INVALID_JSON') from None
    checkpoint()
    canonical = hashlib.sha256()
    class Sink:
        def write(self, text):
            canonical.update(text.encode('ascii'))
            return len(text)
    stats = compact.dump(document, Sink(), checkpoint=checkpoint, indent=2)
    require(stats['characters_written'] == size and canonical.hexdigest() == sha, 'EXACT_CANONICAL_INNER_JSON')
    return document


def dump(document, stream, *, checkpoint, **keywords):
    require(not keywords or keywords == {'indent': 2}, 'ORIGINAL_INDENT_ONLY')
    carrier, raw_stats = pack(document, checkpoint)
    write_stats = compact.dump(carrier, stream, checkpoint=checkpoint, indent=2)
    require(write_stats['characters_written'] <= MAX_BYTES, 'FINAL_CARRIER_BUDGET')
    return dict(raw_json_bytes=carrier['raw_json_bytes'], raw_json_sha256=carrier['raw_json_sha256'],
        gzip_bytes=carrier['gzip_bytes'], carrier_bytes=write_stats['characters_written'],
        raw_encode_statistics=raw_stats, carrier_write_statistics=write_stats,
        semantic_fields_removed=0, original_files_rewritten=False,
        new_sampler_or_native_query_started=False, CPU_or_PC_freeze_improvement_claimed=False)
