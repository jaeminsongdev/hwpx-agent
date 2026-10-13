"""No compiler/SQL/native child starts in these build-admission contracts."""
import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import build_signed_durable_probe as s


class DurableProbeBuildTests(unittest.TestCase):
    def output(self, **changes):
        artifact = dict(reason='compiler-artifact', target=dict(name='formula_issuer_product_postgres_probe'),
            profile=dict(opt_level='1', debuginfo='line-tables-only', debug_assertions=True, overflow_checks=True, test=False),
            executable=str(s.c.ROOT/s.executable_name(1)))
        artifact.update(changes)
        return json.dumps(artifact)+'\n'+json.dumps(dict(reason='build-finished', success=True))+'\n'

    def test_fresh_variant_closed_non_bool_run(self):
        self.assertEqual(s.run_for(s.task_for(1)), 1)
        for wrong in (0, True, 100, -1, '1'):
            with self.assertRaises(ValueError): s.task_for(wrong)
        for wrong in ('p150-durable-probe-build-r00', 'p150-durable-probe-build-r001', 'other'):
            with self.assertRaises(ValueError): s.run_for(wrong)

    def test_current_no_libtest_build_exact(self):
        parsed = s.parse_build(self.output(), 1)
        self.assertFalse(parsed['catalog_profile']['test'])
        self.assertEqual(parsed['executable_path'], s.executable_name(1))

    def test_assertion_or_test_profile_change_denied(self):
        profile = dict(opt_level='1', debuginfo='line-tables-only', debug_assertions=True, overflow_checks=True, test=False)
        for key, value in (('opt_level', '0'), ('debug_assertions', False), ('overflow_checks', False),
                           ('test', True), ('debuginfo', 0)):
            with self.assertRaises(ValueError): s.parse_build(self.output(profile=dict(profile, **{key: value})), 1)

    def test_missing_duplicate_or_failed_finish_denied(self):
        valid = self.output()
        for wrong in ('', valid+valid, valid.replace('"success": true', '"success": false'),
                      valid.splitlines()[0], json.dumps(dict(reason='unexpected'))):
            with self.assertRaises(ValueError): s.parse_build(wrong, 1)

    def test_warning_and_error_deny_clean_build(self):
        for level in ('warning', 'error'):
            line = json.dumps(dict(reason='compiler-message', message=dict(level=level, code=dict(code='E0001'))))
            with self.assertRaises(ValueError): s.parse_build(line+'\n'+self.output(), 1)

    def test_wrong_old_or_test_executable_denied(self):
        for path in ('C:\\outside.exe', str(s.c.ROOT/s.original.BINARY), str(s.c.ROOT/s.executable_name(2))):
            with self.assertRaises(ValueError): s.parse_build(self.output(executable=path), 1)
        with self.assertRaises(ValueError):s.parse_build(self.output(executable=None),1)

    def test_canonical_name_maps_only_fresh_fixed_suffix_with_stream_proof(self):
        canonical=str(s.TARGET/'debug/examples/formula_issuer_product_postgres_probe.exe')
        with self.assertRaises(ValueError):s.parse_build(self.output(executable=canonical),1)
        cargo=s.stream.CargoStream();raw=self.output(executable=canonical).encode()
        for index in range(0,len(raw),4096):cargo.feed(raw[index:index+4096])
        payload=cargo.finish(0)
        with patch.object(s,'scoped_path',return_value=SimpleNamespace(is_file=lambda:True)) as scoped:
            result=s.parse_build(payload,1,require_stream=True)
            self.assertEqual(result['executable_path'],s.executable_name(1))
            self.assertEqual(result['Cargo_announcement_kind'],'canonical_name_with_frozen_driver_suffix')
            scoped.assert_called_once_with(s.executable_name(1))
        with patch.object(s,'scoped_path',return_value=SimpleNamespace(is_file=lambda:False)):
            with self.assertRaises(ValueError):s.parse_build(payload,1,require_stream=True)

    def test_output_budget_and_invalid_json_denied(self):
        for wrong in ('x'*32769, 'not json', '{}'):
            with self.assertRaises(ValueError): s.parse_build(wrong, 1)

    def worker(self, go='P149_GO\n', member=True, override=None):
        class Kernel:
            def GetCurrentProcess(self): return 1
            def IsProcessInJob(self, p, j, out): out._obj.value=member; return True
        calls=[]
        clean={k:'' for k in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET')}
        clean.update(P150_BLOB_MODE='untrusted', P150_BLOB_ROOT='untrusted', P150_BLOB_RUN_ID='untrusted')
        if override: clean[override]='untrusted'
        with patch.object(s.c, 'Windows', return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.c.sys, 'stdin', io.StringIO(go)), patch.object(s.c.shutil, 'which', return_value='cargo'), \
                patch.dict(s.c.os.environ, clean), patch.object(s.stream, 'run_command', side_effect=lambda a, kw, validator:calls.append((a,kw)) or 0):
            result=s.worker(s.task_for(1))
        return result,calls

    def test_worker_GO_and_membership_before_cargo(self):
        for go, member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError): self.worker(go, member)

    def test_exact81_assertions_job1_offline_new_suffix(self):
        _,calls=self.worker(); self.assertEqual(len(calls),1); args,kw=calls[0]
        self.assertEqual(len(s.DEV_CONFIG),81)
        self.assertEqual(s.DEV_CONFIG,tuple(e.replace('profile.test.','profile.dev.',1) for e in s.original.base.CONFIG))
        self.assertEqual(args[1:1+2*len(s.DEV_CONFIG)], [v for e in s.DEV_CONFIG for v in ('--config',e)])
        self.assertEqual(args[-4:], ['--message-format=json','--','-C','extra-filename=-p150-r01'])
        for option in ('--locked','--offline','--jobs','--profile'): self.assertIn(option,args)
        self.assertNotIn('--test',args); self.assertNotIn('--release',args)
        self.assertEqual(kw['cwd'],s.c.ROOT); self.assertEqual(kw['env']['CARGO_PROFILE_DEV_OPT_LEVEL'],'0')
        self.assertEqual(kw['env']['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS'],'true')
        self.assertEqual(kw['env']['CARGO_PROFILE_TEST_OVERFLOW_CHECKS'],'true')
        for key in ('P150_BLOB_MODE','P150_BLOB_ROOT','P150_BLOB_RUN_ID'): self.assertNotIn(key,kw['env'])

    def test_ambient_overrides_denied(self):
        for name in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET'):
            with self.assertRaises(ValueError): self.worker(override=name)

    def test_global_policy_and_original_helpers_not_modified(self):
        before=copy.deepcopy(s.c.POLICY); self.worker(); self.assertEqual(before,s.c.POLICY)
        self.assertEqual(s.c.POLICY['job_memory_limit_percent'],8)
        self.assertEqual(s.c.POLICY['job_memory_stop_percent'],7)
        self.assertEqual(s.c.POLICY['output_limit_bytes_per_stream'],32768)


if __name__=='__main__': unittest.main()
