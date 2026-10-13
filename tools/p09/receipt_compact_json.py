"""P219 새 receipt의 공백만 줄이는 writer. 과거 파일/검증 결과는 변경하지 않는다.

아직 제품 진입점에 연결되지 않은 지원 코드다. 모든 JSON 필드/표본을 유지한다.
각 쓰기 batch는 bounded이며 caller의 원 guard를 실행한다. 예외 뒤 stream에는
부분 JSON이 남을 수 있다. caller는 이를 PASS로 publish하거나 자동 재시도하면 안 된다.
"""
import json

SELF = 'tools/p09/receipt_compact_json.py'
TEST = 'tools/p09/tests/test_receipt_compact_json.py'
WRITE_CHARS = 32768
GUARD_TOKEN_INTERVAL = 64


def require(ok, code):
    if not ok:
        raise ValueError('COMPACT_RECEIPT_' + code)


def dump(document, stream, *, checkpoint, **keywords):
    # 원 dump(indent=2)의 의미를 유지하되 공백만 제거한다. skipkeys/default/
    # float 대체 같은 의미 변경 옵션은 허용하지 않는다. NaN/Infinity도 거부한다.
    require(callable(checkpoint) and callable(getattr(stream, 'write', None)), 'WRITER_GUARD')
    require(not keywords or keywords == {'indent': 2}, 'ORIGINAL_INDENT_ONLY')
    encoder = json.JSONEncoder(ensure_ascii=True, allow_nan=False, check_circular=True,
        skipkeys=False, sort_keys=False, indent=None, separators=(',', ':'))
    pending = []
    buffered = written = writes = maximum = tokens = 0

    def flush():
        nonlocal buffered, written, writes, maximum
        if not buffered:
            return
        checkpoint()
        block = ''.join(pending)
        require(0 < len(block) <= WRITE_CHARS and block.isascii(), 'BOUNDED_ASCII_BLOCK')
        require(stream.write(block) == len(block), 'COMPLETE_SINGLE_WRITE_NO_RETRY')
        writes += 1
        written += len(block)
        maximum = max(maximum, len(block))
        pending.clear()
        buffered = 0
        checkpoint()

    checkpoint()
    for token in encoder.iterencode(document):
        tokens += 1
        if tokens % GUARD_TOKEN_INTERVAL == 0:
            checkpoint()
        offset = 0
        while offset < len(token):
            take = min(WRITE_CHARS - buffered, len(token) - offset)
            pending.append(token[offset:offset + take])
            buffered += take
            offset += take
            if buffered == WRITE_CHARS:
                flush()
    flush()
    checkpoint()
    return dict(characters_written=written, write_batches=writes,
        maximum_write_batch_chars=maximum, maximum_allowed_write_batch_chars=WRITE_CHARS,
        guard_token_interval=GUARD_TOKEN_INTERVAL, semantic_fields_intentionally_removed=0,
        extra_sampler_or_native_query_started=False, original_files_rewritten=False)
