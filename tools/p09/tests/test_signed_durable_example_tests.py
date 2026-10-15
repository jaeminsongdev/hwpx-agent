"""Closed driver contracts; no compiler, SQL, native app or process is started."""
import base64
import contextlib
import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import run_signed_durable_example_tests as s


class SignedDurableExampleTests(unittest.TestCase):
    def output(self, count=19):
        return (f'running {count} tests\n'
                f'test result: ok. {count} passed; 0 failed; 0 ignored; '
                '0 measured; 0 filtered out; finished in 1s\n')

    def test_original11_plus_new8_requires_complete19(self):
        self.assertEqual(s.ORIGINAL_TEST_COUNT, 11)
        self.assertEqual(len(set(s.TEST_NAMES)), 8)
        self.assertEqual(s.TOTAL_TEST_COUNT, 19)
        s.validate_output(self.output())
        for count in (0, 8, 11, 18, 20, 249):
            with self.assertRaises(ValueError): s.validate_output(self.output(count))

    def test_fail_ignored_measured_filtered_and_duplicate_denied(self):
        valid = self.output()
        for wrong in (valid.replace('0 failed', '1 failed'),
                      valid.replace('0 ignored', '1 ignored'),
                      valid.replace('0 measured', '1 measured'),
                      valid.replace('0 filtered', '1 filtered'),
                      valid + valid, valid.replace('running 19', 'running 18')):
            with self.assertRaises(ValueError): s.validate_output(wrong)

    def test_declared_delta_restores_whole_original_bodies(self):
        archive = json.loads((s.c.ROOT/s.ARCHIVE).read_text(encoding='utf-8'))
        self.assertEqual({p['path'] for p in archive['files']}, {s.ROOT_SOURCE, s.PROVIDER_SOURCE})
        for p in archive['files']:
            original = base64.b64decode(p['base64'], validate=True)
            current = (s.c.ROOT/p['path']).read_text(encoding='utf-8')
            restored = s.restore_original(p['path'], current)
            restored = restored.replace('\n', '\r\n').encode() if b'\r\n' in original else restored.encode()
            self.assertEqual(restored, original)

    def test_missing_or_duplicate_extension_denied(self):
        text = (s.c.ROOT/s.PROVIDER_SOURCE).read_text(encoding='utf-8')
        marker = '// P150 owned-local extension: retain original fresh signed authority checks.'
        for wrong in (text.replace(marker, '// removed'), text + text):
            with self.assertRaises(ValueError): s.restore_original(s.PROVIDER_SOURCE, wrong)

    def worker(self, *, task=None, go='P149_GO\n', member=True, errors=None, exit_code=0, override=None):
        task = task or s.TASK
        artifact = s.c.ROOT/s.BINARY
        errors = errors if errors is not None else f'  Executable unittests fixture ({artifact})\n'
        class Kernel:
            def GetCurrentProcess(self): return 1
            def IsProcessInJob(self, p, j, out): out._obj.value = member; return True
        process = SimpleNamespace(returncode=exit_code)
        bounded = SimpleNamespace(communicate=lambda **kw: ('', errors), close=lambda: None)
        class Reader:
            def __init__(self, *args): pass
            def fresh_pin(self, name): return dict(path=name, bytes=1, sha256='a'*64)
            def finish(self): pass
        calls, compiles = [], []
        def compile_only(args, **kw): compiles.append((args, kw)); return process
        clean_env = {k: '' for k in ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER')}
        clean_env.update(P150_BLOB_MODE='untrusted', P150_BLOB_ROOT='untrusted', P150_BLOB_RUN_ID='untrusted', RUST_TEST_NOCAPTURE='1')
        if override: clean_env[override] = 'untrusted'
        with patch.object(s.c, 'Windows', return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.c.sys, 'stdin', io.StringIO(go)), \
                patch.object(s.c.shutil, 'which', return_value='cargo'), \
                patch.dict(s.c.os.environ, clean_env), \
                patch.object(s.subprocess, 'call', side_effect=lambda a, **kw: calls.append((a, kw)) or 0), \
                patch.object(s.subprocess, 'Popen', side_effect=compile_only), \
                patch.object(s.base.signed.bounded, 'BoundedProcessCapture', return_value=bounded), \
                patch('audit_evidence_io.AuditEvidenceReader', Reader), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = s.worker(task)
        return result, calls, compiles

    def test_GO_and_job_required_before_any_compile(self):
        for go, member in (('wrong\n', True), ('P149_GO\n', False)):
            with self.assertRaises(ValueError): self.worker(go=go, member=member)

    def test_compile_no_run_exact81_then_reported_binary_at_repo(self):
        result, calls, compiles = self.worker()
        self.assertEqual(result, 0); self.assertEqual(len(compiles), 1); self.assertEqual(len(calls), 1)
        args, kw = compiles[0]
        self.assertEqual(args[1:1+2*len(s.base.CONFIG)], [v for e in s.base.CONFIG for v in ('--config', e)])
        self.assertEqual(args[-1], '--no-run')
        for required in ('--locked', '--offline', '--jobs'): self.assertIn(required, args)
        for denied in ('--skip', '--ignored', '--exact', '--nocapture'): self.assertNotIn(denied, args)
        self.assertEqual(calls[0][0], [str(s.c.ROOT/s.BINARY), '--test-threads=1', '--format=terse'])
        self.assertEqual(calls[0][1]['cwd'], s.c.ROOT)
        self.assertEqual(kw['env']['RUST_TEST_NOCAPTURE'], '0')
        self.assertEqual(kw['env']['CARGO_BUILD_JOBS'], '1')
        for name in ('P150_BLOB_MODE', 'P150_BLOB_ROOT', 'P150_BLOB_RUN_ID'): self.assertNotIn(name, kw['env'])

    def test_ambient_compiler_override_denied(self):
        for name in ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER'):
            with self.assertRaises(ValueError): self.worker(override=name)

    def test_missing_duplicate_or_outside_reported_artifact_denied(self):
        line = f'Executable unittests fixture ({s.c.ROOT/s.BINARY})\n'
        for errors in ('', line + line, 'Executable unittests fixture (C:\\outside\\x.exe)\n',
                       'Executable unittests fixture ('+str(s.c.ROOT/'Cargo.toml')+')\n'):
            with self.assertRaises(ValueError): self.worker(errors=errors)

    def test_compile_failure_cannot_be_runtime_pass(self):
        with self.assertRaisesRegex(ValueError, 'SIGNED_DURABLE_COMPILE_ONLY_FAILED'):
            self.worker(exit_code=101)

    def test_CWD_diagnostic_stays_no_compile(self):
        for task, cwd in ((s.DIRECT_ROOT, s.c.ROOT), (s.DIRECT_CRATE, s.c.ROOT/'crates/product-cli')):
            _, calls, compiles = self.worker(task=task)
            self.assertEqual(compiles, []); self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][1]['cwd'], cwd)

    def test_post_hash_fresh_admission_precedes_worker_and_policy_restores(self):
        events = []; policy = copy.deepcopy(s.c.POLICY)
        class Resources:
            stop = SimpleNamespace(is_set=lambda: False); reason = None
            def admit(self): events.append('admit')
            def sample(self): events.append('sample'); return dict(available_ram_percent=20, system_cpu_percent=0, commit_used_percent=20)
        def original_pins(checkpoint=None): events.append('hash'); return []
        def owned(*args):
            s.c.pins(); events.append('worker'); s.c.pins(); return 0
        def finish(*args): events.append('cleanup'); return True
        with patch.object(s.c, 'pins', side_effect=original_pins), patch.object(s.c, 'run', side_effect=owned), \
                patch.object(s, 'SQLRuntimeResources', Resources), patch.object(s, 'finish_watcher', side_effect=finish), \
                patch.object(s.time, 'sleep'):
            s.run_owned(None, {}, [])
        self.assertEqual(events, ['hash', 'admit', 'sample', 'sample', 'cleanup', 'worker', 'hash'])
        self.assertEqual(s.c.POLICY, policy)

    def test_post_hash_compile15_runtime10_not_a_global_cap_change(self):
        source = (s.c.ROOT/s.SELF).read_text(encoding='utf-8')
        self.assertIn('minimum=15 if task==TASK else 10', source)
        self.assertIn('before worker creation', source.lower())
        self.assertEqual(s.c.POLICY['job_memory_limit_percent'], 8)
        self.assertEqual(s.c.POLICY['job_memory_stop_percent'], 7)
        self.assertEqual(s.c.POLICY['stop_ram_min_percent'], 5)
        self.assertEqual(s.c.POLICY['output_limit_bytes_per_stream'], 32768)


if __name__ == '__main__': unittest.main()
