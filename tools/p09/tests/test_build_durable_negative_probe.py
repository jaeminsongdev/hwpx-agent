"""P151 cache/suffix/profile contracts. No actual child or reader thread."""
import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import build_durable_negative_probe as s


class CurrentDurableBuildTests(unittest.TestCase):
    def output(self,**changes):
        artifact=dict(reason='compiler-artifact',target=dict(name='formula_issuer_product_postgres_probe'),
            profile=dict(opt_level='1',debuginfo='line-tables-only',debug_assertions=True,overflow_checks=True,test=False),
            executable=str(s.c.ROOT/s.executable_name(1)))
        artifact.update(changes)
        return json.dumps(artifact)+'\n'+json.dumps(dict(reason='build-finished',success=True))+'\n'

    def worker(self,go='P149_GO\n',member=True,override=None):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=member;return True
        calls=[];clean={k:'' for k in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER',
            'RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET')}
        clean.update(P150_BLOB_MODE='untrusted',P150_BLOB_ROOT='untrusted',P150_BLOB_RUN_ID='untrusted')
        if override:clean[override]='untrusted'
        with patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.c.sys,'stdin',io.StringIO(go)),patch.object(s.c.shutil,'which',return_value='cargo'), \
                patch.dict(s.c.os.environ,clean),patch.object(s.legacy.stream,'run_command',
                    side_effect=lambda a,kw,v:calls.append((a,kw)) or 0):result=s.worker(s.task_for(1))
        return result,calls

    def test_run_and_generation_closed(self):
        self.assertEqual(s.run_for(s.task_for(1)),1)
        for run in (0,True,100,-1,'1'):
            with self.assertRaises(ValueError):s.task_for(run)
        for task in ('p150-durable-probe-build-r01','p151-durable-negative-probe-build-r00','other'):
            with self.assertRaises(ValueError):s.run_for(task)

    def test_runtime_profile_not_libtest(self):
        self.assertFalse(s.parse_build(self.output(),1)['catalog_profile']['test'])

    def test_assertions_and_profile_changes_denied(self):
        profile=dict(opt_level='1',debuginfo='line-tables-only',debug_assertions=True,overflow_checks=True,test=False)
        for key,value in (('opt_level','0'),('test',True),('debug_assertions',False),('overflow_checks',False),('debuginfo',0)):
            with self.assertRaises(ValueError):s.parse_build(self.output(profile=dict(profile,**{key:value})),1)

    def test_old_unit_runtime_other_run_denied(self):
        for name in (str(s.TARGET/'debug/examples/formula_issuer_product_postgres_probe-05e8ead2b3796168.exe'),
                str(s.c.ROOT/s.legacy.executable_name(5)),str(s.c.ROOT/s.executable_name(2))):
            with self.assertRaises(ValueError):s.parse_build(self.output(executable=name),1)

    def test_canonical_needs_all_stream_and_fresh_suffix(self):
        payload=self.output(executable=str(s.TARGET/'debug/examples/formula_issuer_product_postgres_probe.exe'))
        with self.assertRaises(ValueError):s.parse_build(payload,1)
        stream=s.legacy.stream.CargoStream();stream.feed(payload.encode());closed=stream.finish(0)
        with patch.object(s.legacy,'scoped_path',return_value=SimpleNamespace(is_file=lambda:False)):
            with self.assertRaises(ValueError):s.parse_build(closed,1,require_stream=True)
        with patch.object(s.legacy,'scoped_path',return_value=SimpleNamespace(is_file=lambda:True)):
            self.assertEqual(s.parse_build(closed,1,require_stream=True)['executable_path'],s.executable_name(1))

    def test_incomplete_duplicate_warning_fail(self):
        valid=self.output()
        warning=json.dumps(dict(reason='compiler-message',message=dict(level='warning')))+'\n'
        for output in ('',valid+valid,valid.replace('"success": true','"success": false'),warning+valid,'x'*32769):
            with self.assertRaises(ValueError):s.parse_build(output,1)

    def test_GO_membership_required(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.worker(go,member)

    def test_command_cache_profile81_and_distinct_suffix(self):
        _,calls=self.worker();self.assertEqual(len(calls),1);args,kw=calls[0]
        self.assertEqual(s.TARGET,s.parent.TARGET)
        self.assertEqual(len(s.DEV_CONFIG),81)
        self.assertEqual(args[-4:],['--message-format=json','--','-C','extra-filename=-p151-r01'])
        self.assertEqual(args[1:163],[v for e in s.DEV_CONFIG for v in ('--config',e)])
        self.assertEqual(s.DEV_CONFIG,tuple(e.replace('profile.test.','profile.dev.',1) for e in s.parent.original.base.CONFIG))
        for option in ('--locked','--offline','--jobs','--profile'):self.assertIn(option,args)
        self.assertNotIn('--release',args);self.assertEqual(kw['cwd'],s.c.ROOT)

    def test_ambient_compiler_overrides_denied(self):
        for name in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET'):
            with self.assertRaises(ValueError):self.worker(override=name)

    def test_untrusted_durable_env_scrubbed(self):
        _,calls=self.worker()
        for name in ('P150_BLOB_MODE','P150_BLOB_ROOT','P150_BLOB_RUN_ID'):self.assertNotIn(name,calls[0][1]['env'])

    def test_original_policy_unchanged(self):
        before=copy.deepcopy(s.c.POLICY);self.worker();self.assertEqual(before,s.c.POLICY)
        self.assertEqual(s.c.POLICY['job_memory_limit_percent'],8)
        self.assertEqual(s.c.POLICY['job_memory_stop_percent'],7)
        self.assertEqual(s.c.POLICY['output_limit_bytes_per_stream'],32768)

    def test_immutable_generation_parent_and_no_unit_execution(self):
        self.assertEqual(s.AUDIT_PIN['sha256'],'d3006b6b871b390d32593c81079aef04d01e0404dcbf04b25b39c9a9bdb5c307')
        self.assertIn('terminal-audit-run02',s.AUDIT_PIN['path'])
        self.assertEqual(s.executable_name(1).rsplit('/',1)[-1],'formula_issuer_product_postgres_probe-p151-r01.exe')
        _,calls=self.worker();self.assertEqual(calls[0][0][0],'cargo')
        self.assertEqual(s.ARGS,['rustc','-p','hwpx-agent-cli','--example','formula_issuer_product_postgres_probe','--profile','dev'])


if __name__=='__main__':unittest.main()
