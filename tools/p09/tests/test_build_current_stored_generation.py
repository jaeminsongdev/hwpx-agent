"""Current test build binding, original full stream and owned worker contracts."""
import copy
import hashlib
import io
import json
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import build_current_stored_generation as s


class CurrentStoredBuildTests(unittest.TestCase):
    def raw(self, dependencies=0, **changes):
        item = dict(reason='compiler-artifact', target=dict(name='form_stored_provider', kind=['test']),
            profile=dict(s.EXPECTED_PROFILE), executable=str(s.c.ROOT/s.executable_name(1)))
        item.update(changes)
        dep = dict(reason='compiler-artifact', target=dict(name='dependency'), padding='x'*500)
        return ('\n'.join(json.dumps(i) for i in [*[dep]*dependencies, item, dict(reason='build-finished', success=True)])+'\n').encode()

    def stream(self, raw):
        stream = s.CargoStream()
        for i in range(0, len(raw), 4096): stream.feed(raw[i:i+4096])
        return stream

    def parse(self, raw):
        with patch.object(s.prepared, 'scoped_path', return_value=SimpleNamespace(is_file=lambda:True)):
            return s.parse_build(self.stream(raw).finish(0), 1, require_stream=True)

    def worker(self, go='P149_GO\n', member=True, override=None):
        class Kernel:
            def GetCurrentProcess(self): return 1
            def IsProcessInJob(self, p, j, out): out._obj.value=member; return True
        clean = {k:'' for k in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET')}
        if override: clean[override]='untrusted'
        calls=[]
        with patch.object(s.c, 'Windows', return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.c.sys, 'stdin', io.StringIO(go)), patch.object(s.c.shutil, 'which', return_value='cargo'), \
                patch.dict(s.c.os.environ, clean), patch.object(s.legacy.stream, 'run_command',
                    side_effect=lambda a, kw, validator:calls.append((a,kw)) or 0): result=s.worker(s.task_for(1))
        return result,calls

    def test_generation_and_task_scope(self):
        self.assertEqual(s.run_for(s.task_for(1)),1)
        for value in (0,100,True,'1'):
            with self.assertRaises(ValueError):s.task_for(value)
        with self.assertRaises(ValueError):s.run_for('p150-durable-probe-build-r01')

    def test_actual_libtest_profile_remains_true(self):
        result=self.parse(self.raw());self.assertEqual(result['catalog_profile'],s.EXPECTED_PROFILE)
        self.assertTrue(result['actual_catalog_test_true_validated_before_legacy_protocol_adapter'])

    def test_bad_profile_and_target_kind_rejected(self):
        for key,value in (('test',False),('test',1),('overflow_checks',False),('debug_assertions',False),('opt_level','0')):
            with self.assertRaises(ValueError):self.parse(self.raw(profile=dict(s.EXPECTED_PROFILE,**{key:value})))
        with self.assertRaises(ValueError):self.parse(self.raw(target=dict(name='form_stored_provider',kind=['bin'])))

    def test_every_raw_record_hashed_over32KiB(self):
        raw=self.raw(100);result=self.parse(raw);p=result['validated_stream']
        self.assertGreater(len(raw),32768);self.assertEqual(p['raw_stdout_bytes'],len(raw))
        self.assertEqual(p['raw_stdout_sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(p['messages'],102)
        self.assertFalse(p['raw_output_truncated'])

    def test_unrelated_probe_cannot_bind(self):
        with self.assertRaises(ValueError):self.stream(self.raw(target=dict(name='formula_issuer_product_postgres_probe',kind=['example'])))

    def test_duplicate_target_or_finish_rejected(self):
        with self.assertRaises(ValueError):self.stream(self.raw()+self.raw())
        with self.assertRaises(ValueError):self.stream(self.raw()+b'{"reason":"build-finished","success":true}\n')

    def test_warning_after_finish_and_invalid_duplicate_JSON_rejected(self):
        for raw in (self.raw()+b'{"reason":"compiler-message","message":{"level":"warning"}}\n',
                b'{"reason":"other","reason":"build-finished"}\n',b'not JSON\n',b'\xff\n'):
            with self.assertRaises(ValueError):self.stream(raw)

    def test_stream_record_and_total_budgets_unchanged(self):
        stream=s.CargoStream()
        for _ in range(8):stream.feed(b'x'*4096)
        with self.assertRaises(ValueError):stream.feed(b'x')
        stream=s.CargoStream();stream.bytes=s.legacy.stream.TOTAL_JSON_BYTES
        with self.assertRaises(ValueError):stream.feed(b'\n')
        with self.assertRaises(ValueError):self.stream(self.raw()).finish(32769)

    def test_canonical_hashed_name_needs_fresh_suffix(self):
        canonical=str(s.TARGET/'debug/deps/form_stored_provider-123456789abcdef0.exe')
        payload=self.stream(self.raw(executable=canonical)).finish(0)
        with self.assertRaises(ValueError):s.parse_build(payload,1)
        with patch.object(s.prepared,'scoped_path',return_value=SimpleNamespace(is_file=lambda:False)):
            with self.assertRaises(ValueError):s.parse_build(payload,1,require_stream=True)
        with patch.object(s.prepared,'scoped_path',return_value=SimpleNamespace(is_file=lambda:True)):
            self.assertEqual(s.parse_build(payload,1,require_stream=True)['executable_path'],s.executable_name(1))

    def test_other_generation_path_or_old_example_denied(self):
        for name in (str(s.c.ROOT/s.executable_name(2)),str(s.TARGET/'debug/examples/form_stored_provider-123456789abcdef0.exe')):
            with self.assertRaises(ValueError):self.parse(self.raw(executable=name))

    def test_missing_or_modified_stream_proof_rejected(self):
        payload=self.stream(self.raw()).finish(0)
        with patch.object(s.prepared,'scoped_path',return_value=SimpleNamespace(is_file=lambda:True)):
            for wrong in ('\n'.join(payload.splitlines()[:2]),payload.replace('"all_records_validated":true','"all_records_validated":false')):
                with self.assertRaises(ValueError):s.parse_build(wrong,1,require_stream=True)

    def test_exact_recipe_job_and_GO_required(self):
        _,calls=self.worker();self.assertEqual(calls[0][0],['cargo',*s.prepared.recipe(1)['argv_without_cargo']])
        self.assertEqual(calls[0][1]['env']['CARGO_INCREMENTAL'],'0')
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.worker(go,member)

    def test_compiler_ambient_overrides_denied(self):
        for name in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET'):
            with self.assertRaises(ValueError):self.worker(override=name)

    def test_original_policy_no_mutation(self):
        before=copy.deepcopy(s.c.POLICY);self.worker();self.assertEqual(before,s.c.POLICY)
        self.assertEqual(s.c.POLICY['job_memory_limit_percent'],8);self.assertEqual(s.c.POLICY['job_memory_stop_percent'],7)

    def test_fragmented_and_no_final_newline(self):
        raw=self.raw().rstrip(b'\n');stream=s.CargoStream()
        for byte in raw:stream.feed(bytes([byte]))
        self.assertEqual(json.loads(stream.finish(0).splitlines()[2])['raw_stdout_sha256'],hashlib.sha256(raw).hexdigest())

    def test_fake_child_real_reader_cleanup_and_validator(self):
        prior={t.ident for t in threading.enumerate()};checked=[]
        fake=SimpleNamespace(stdout=io.BytesIO(self.raw(100)),stderr=io.BytesIO(b''),returncode=0,
            poll=lambda:0,wait=lambda **kw:0,kill=lambda:None)
        with patch.object(s.legacy.stream,'CargoStream',s.CargoStream),patch('sys.stdout',io.StringIO()), \
                patch.object(s.prepared,'scoped_path',return_value=SimpleNamespace(is_file=lambda:True)):
            code=s.legacy.stream.run_command(['fixture'],{},lambda p:checked.append(s.parse_build(p,1,require_stream=True)),
                process_factory=lambda *a,**kw:fake)
        self.assertEqual(code,0);self.assertEqual(len(checked),1)
        self.assertTrue(fake.stdout.closed and fake.stderr.closed);self.assertEqual(prior,{t.ident for t in threading.enumerate()})


if __name__=='__main__':unittest.main()
