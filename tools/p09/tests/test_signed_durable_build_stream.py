import hashlib
import io
import json
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import signed_durable_build_stream as s
import build_signed_durable_probe as build


class DurableBuildStreamTests(unittest.TestCase):
    def raw(self, records=0):
        dependency = dict(reason='compiler-artifact', target=dict(name='dependency'), profile=dict(test=False), padding='x'*500)
        target = dict(reason='compiler-artifact', target=dict(name='formula_issuer_product_postgres_probe'),
            profile=dict(opt_level='1', debuginfo='line-tables-only', debug_assertions=True, overflow_checks=True, test=False),
            executable=str(build.c.ROOT/build.executable_name(2)))
        return ('\n'.join(json.dumps(row) for row in [*[dependency]*records,target,dict(reason='build-finished',success=True)])+'\n').encode()

    def consume(self, raw):
        stream=s.CargoStream()
        for index in range(0,len(raw),4096):stream.feed(raw[index:index+4096])
        return stream

    def test_over32KiB_all_records_full_hash_no_truncation(self):
        raw=self.raw(100);self.assertGreater(len(raw),32768)
        stream=self.consume(raw);payload=stream.finish(0)
        parsed=build.parse_build(payload,2,require_stream=True)['validated_stream']
        self.assertEqual(parsed['raw_stdout_bytes'],len(raw));self.assertEqual(parsed['messages'],102)
        self.assertEqual(parsed['raw_stdout_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertFalse(parsed['raw_output_truncated']);self.assertLess(len(payload.encode()),32768)

    def test_every_chunk_boundary_and_final_no_newline(self):
        raw=self.raw().rstrip(b'\n');stream=s.CargoStream()
        for byte in raw:stream.feed(bytes([byte]))
        build.parse_build(stream.finish(32768),2,require_stream=True)

    def test_warning_even_dependency_or_after_finish_denies(self):
        warning=json.dumps(dict(reason='compiler-message',message=dict(level='warning'))).encode()+b'\n'
        for raw in (warning+self.raw(),self.raw()+warning):
            with self.assertRaises(ValueError):self.consume(raw)

    def test_invalid_JSON_UTF_duplicate_key_reason_denies(self):
        for raw in (b'not json\n',b'\xff\n',b'{"reason":"build-finished","reason":"other"}\n',b'{"reason":"other"}\n'):
            with self.assertRaises(ValueError):self.consume(raw)

    def test_record_buffer_budget_enforced_before_growth(self):
        stream=s.CargoStream()
        for _ in range(8):stream.feed(b'x'*4096)
        self.assertEqual(len(stream.pending),32768)
        with self.assertRaises(ValueError):stream.feed(b'x')
        self.assertEqual(len(stream.pending),32768)

    def test_total_IO_and_message_budget_fail_not_skip(self):
        stream=s.CargoStream();stream.bytes=s.TOTAL_JSON_BYTES
        with self.assertRaises(ValueError):stream.feed(b'\n')
        stream=s.CargoStream();stream.messages=s.MAX_MESSAGES
        with self.assertRaises(ValueError):stream.feed(b'{"reason":"build-script-executed"}\n')

    def test_duplicate_target_or_finish_denied(self):
        for raw in (self.raw()+self.raw(),self.raw()+b'{"reason":"build-finished","success":true}\n'):
            with self.assertRaises(ValueError):self.consume(raw)

    def test_missing_failed_finish_and_stderr_total_denied(self):
        for raw in (b'',self.raw().replace(b'"success": true',b'"success": false')):
            with self.assertRaises(ValueError):self.consume(raw).finish(0)
        with self.assertRaises(ValueError):self.consume(self.raw()).finish(32769)

    def test_outer_summary_must_exist_once_and_be_exact(self):
        payload=self.consume(self.raw()).finish(0)
        for wrong in (payload.splitlines()[0]+'\n'+payload.splitlines()[1]+'\n',payload+payload.splitlines()[2]+'\n',
                      payload.replace('"all_records_validated":true','"all_records_validated":false'),
                      payload.replace('"stdout_record_buffer_limit":32768','"stdout_record_buffer_limit":65536')):
            with self.assertRaises(ValueError):build.parse_build(wrong,2,require_stream=True)

    def test_in_process_fake_child_cleanup_and_validator(self):
        prior={t.ident for t in threading.enumerate()};checks=[]
        fake=SimpleNamespace(stdout=io.BytesIO(self.raw(100)),stderr=io.BytesIO(b''),returncode=0,
            poll=lambda:0,wait=lambda **kw:0,kill=lambda:None)
        with patch('sys.stdout',io.StringIO()):
            result=s.run_command(['fixture'],{},lambda payload:checks.append(build.parse_build(payload,2,require_stream=True)),
                                 process_factory=lambda *a,**kw:fake)
        self.assertEqual(result,0);self.assertEqual(len(checks),1)
        self.assertTrue(fake.stdout.closed and fake.stderr.closed)
        self.assertEqual({t.ident for t in threading.enumerate()},prior)


if __name__=='__main__':unittest.main()
