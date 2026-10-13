"""Validate EVERY Cargo JSON record with bounded memory, then emit a closed proof.

No raw output truncation/filter-to-success. Raw stdout is processed completely
(16 MiB IO budget, 32 KiB maximum record); raw stderr and outer worker streams
retain the original 32 KiB TOTAL limit. Any malformed/warning/error/overflow fails.
"""
import hashlib
import json
import re
import subprocess
import sys
import threading
import time

LIMIT = 32768
TOTAL_JSON_BYTES = 16*1024*1024
MAX_MESSAGES = 2048


def require(ok, code):
    if not ok: raise ValueError('DURABLE_STREAM_'+code)


def unique_object(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'DUPLICATE_JSON_KEY'); out[key] = value
    return out


class CargoStream:
    def __init__(self):
        self.pending = bytearray(); self.digest = hashlib.sha256()
        self.bytes = self.messages = self.maximum_record_bytes = 0
        self.artifact = None; self.finished = []

    def accept(self, raw):
        self.maximum_record_bytes = max(self.maximum_record_bytes, len(raw))
        if not raw.strip(): return
        self.messages += 1; require(self.messages <= MAX_MESSAGES, 'MESSAGE_BUDGET')
        try: item = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
        except (UnicodeDecodeError, json.JSONDecodeError): raise ValueError('DURABLE_STREAM_JSON_INVALID') from None
        require(isinstance(item, dict) and item.get('reason') in
                {'build-finished', 'compiler-artifact', 'compiler-message', 'build-script-executed'}, 'MESSAGE_SCOPE')
        if item['reason'] == 'build-finished':
            require(type(item.get('success')) is bool, 'FINISH_SCOPE')
            self.finished.append(item['success']); require(len(self.finished) == 1, 'DUPLICATE_FINISH')
        elif item['reason'] == 'compiler-message':
            require(isinstance(item.get('message'), dict), 'DIAGNOSTIC_SCOPE')
            require(item['message'].get('level') not in {'warning', 'error'}, 'WARNING_OR_ERROR')
        elif item['reason'] == 'compiler-artifact' and item.get('target', {}).get('name') == 'formula_issuer_product_postgres_probe':
            require(self.artifact is None, 'DUPLICATE_TARGET')
            # Same fields consumed by the original parse_build, not arbitrary logs/paths.
            profile=item.get('profile');require(isinstance(profile,dict),'PROFILE_SCOPE')
            self.artifact = dict(reason='compiler-artifact', target=dict(name='formula_issuer_product_postgres_probe'),
                profile={k:profile.get(k) for k in ('opt_level','debuginfo','debug_assertions','overflow_checks','test')},
                executable=item.get('executable'))

    def feed(self, chunk):
        require(isinstance(chunk, bytes) and len(chunk) <= 4096, 'CHUNK_SCOPE')
        self.bytes += len(chunk); require(self.bytes <= TOTAL_JSON_BYTES, 'RAW_JSON_IO_BUDGET')
        self.digest.update(chunk)
        parts = chunk.split(b'\n')
        for index, part in enumerate(parts):
            require(len(self.pending)+len(part) <= LIMIT, 'RECORD_BUFFER_LIMIT')
            self.pending.extend(part)
            if index != len(parts)-1:
                self.accept(bytes(self.pending)); self.pending.clear()

    def finish(self, stderr_bytes):
        if self.pending: self.accept(bytes(self.pending)); self.pending.clear()
        require(self.finished == [True] and self.artifact is not None, 'COMPLETE_CLEAN_BUILD_REQUIRED')
        require(type(stderr_bytes) is int and 0 <= stderr_bytes <= LIMIT, 'STDERR_TOTAL_LIMIT')
        summary = dict(reason='p150-validated-stream', all_records_validated=True,
            raw_stdout_bytes=self.bytes, raw_stdout_sha256=self.digest.hexdigest(), messages=self.messages,
            maximum_record_bytes=self.maximum_record_bytes, raw_stderr_bytes=stderr_bytes,
            stdout_record_buffer_limit=LIMIT, stdout_total_JSON_IO_budget=TOTAL_JSON_BYTES,
            stderr_total_limit=LIMIT, raw_output_truncated=False, raw_logs_included=False)
        payload = '\n'.join(json.dumps(row, separators=(',', ':')) for row in
                            (self.artifact, dict(reason='build-finished', success=True), summary))+'\n'
        require(len(payload.encode()) <= LIMIT, 'OUTER_TOTAL_LIMIT')
        return payload


def run_command(args, kwargs, validator, process_factory=subprocess.Popen):
    options = dict(kwargs); options.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process = process_factory(args, **options); stream = CargoStream()
    stop = threading.Event(); failures = []; stderr_count = [0]
    def read_stdout():
        try:
            while not stop.is_set():
                chunk = process.stdout.read(4096)
                if not chunk: break
                stream.feed(chunk)
        except (ValueError, OSError, TypeError, AttributeError): failures.append('DURABLE_STREAM_STDOUT_NOT_ACCEPTED'); stop.set()
    def read_stderr():
        try:
            while not stop.is_set():
                chunk = process.stderr.read(4096)
                if not chunk: break
                stderr_count[0] += len(chunk)
                require(stderr_count[0] <= LIMIT, 'STDERR_TOTAL_LIMIT')
        except (ValueError, OSError, TypeError): failures.append('DURABLE_STREAM_STDERR_NOT_ACCEPTED'); stop.set()
    threads = [threading.Thread(target=read_stdout, daemon=True), threading.Thread(target=read_stderr, daemon=True)]
    try:
        for thread in threads: thread.start()
        deadline = time.monotonic()+600
        while process.poll() is None:
            require(not stop.wait(.1) and time.monotonic() < deadline, 'OPERATION_STOP_OR_TIMEOUT')
        for thread in threads: thread.join(timeout=3)
        require(not any(thread.is_alive() for thread in threads), 'READER_CLEANUP')
        require(not failures, 'READER_FAILED')
        require(process.returncode == 0, 'COMPILER_EXIT_FAILED')
        payload = stream.finish(stderr_count[0])
        try: validator(payload)
        except ValueError as error:
            code=str(error)
            if re.fullmatch(r'DURABLE_BUILD_[A-Z_]+',code):print('P150_BUILD_CLOSED_ERROR:'+code,file=sys.stderr,flush=True)
            artifact=stream.artifact or {};raw_profile=artifact.get('profile') or {}
            closed_profile={key:raw_profile.get(key) for key in ('opt_level','debuginfo','debug_assertions','overflow_checks','test')}
            allowed=(closed_profile['opt_level'] in ('0','1','2','3','s','z')
                and closed_profile['debuginfo'] in (0,1,2,'line-tables-only','limited','full')
                and all(type(closed_profile[k]) is bool for k in ('debug_assertions','overflow_checks','test')))
            if allowed:print('P150_BUILD_CLOSED_PROFILE:'+json.dumps(closed_profile,separators=(',',':')),file=sys.stderr,flush=True)
            name=(artifact.get('executable') or '').replace('\\','/').rsplit('/',1)[-1]
            if re.fullmatch(r'formula_issuer_product_postgres_probe(?:-p150-r[0-9]{2})?\.exe',name):
                print('P150_BUILD_CLOSED_BASENAME:'+name,file=sys.stderr,flush=True)
            raise
        print(payload, end='', flush=True); return 0
    finally:
        stop.set()
        if process.poll() is None: process.kill()
        process.wait(timeout=5)
        for thread in threads:
            if thread.ident is not None: thread.join(timeout=3)
        for pipe in (process.stdout, process.stderr): pipe.close()
        require(not any(thread.is_alive() for thread in threads), 'FINAL_READER_CLEANUP')
