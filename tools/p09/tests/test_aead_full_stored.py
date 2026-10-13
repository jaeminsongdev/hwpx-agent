import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_aead_full_stored as s


class AeadFullStoredTests(unittest.TestCase):
    def worker(self,go='P149_GO\n',member=True):
        class Kernel:
            def GetCurrentProcess(self): return 1
            def IsProcessInJob(self,p,j,out): out._obj.value=member; return True
        calls = []
        with patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(s.c.sys,'stdin',io.StringIO(go)), \
                patch.object(s.c.shutil,'which',return_value='cargo'), \
                patch.object(s.subprocess,'call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            result = s.worker()
        return result,calls

    def test_exact81_config_no_filter_worker(self):
        result,calls = self.worker(); self.assertEqual(result,0); self.assertEqual(len(calls),1)
        args,kw = calls[0]; offset = 1+2*len(s.candidate.CONFIG)
        self.assertEqual(args[1:offset],[v for e in s.candidate.CONFIG for v in ('--config',e)])
        self.assertEqual(args[offset:offset+len(s.captured.ARGS)],s.captured.ARGS)
        self.assertEqual(args[-3:],['--','--test-threads=1','--format=terse'])
        for option in ('--exact','--skip','--ignored','--nocapture','--no-capture','--show-output'):
            self.assertNotIn(option,args)
        self.assertEqual(kw['env']['RUST_TEST_NOCAPTURE'],'0')
        self.assertEqual(kw['env']['CARGO_PROFILE_TEST_OPT_LEVEL'],'0')
        self.assertEqual(kw['env']['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS'],'true')
        self.assertEqual(kw['env']['CARGO_PROFILE_TEST_OVERFLOW_CHECKS'],'true')

    def test_GO_and_real_job_gate_before_cargo(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError): self.worker(go,member)

    def test_inherited_nocapture_still_closed(self):
        with patch.dict(s.c.os.environ,{'RUST_TEST_NOCAPTURE':'1'}): _,calls = self.worker()
        self.assertEqual(calls[0][1]['env']['RUST_TEST_NOCAPTURE'],'0')

    def test_scoped_adapter_restored_without_policy_change(self):
        prior = (s.captured.candidate,s.captured.SELF,s.captured.TASK,s.captured.VARIANT)
        policy = copy.deepcopy(s.c.POLICY)
        with s.adapter():
            self.assertIs(s.captured.candidate,s.candidate)
            self.assertEqual((s.captured.SELF,s.captured.TASK,s.captured.VARIANT),(s.SELF,s.TASK,s.VARIANT))
        self.assertEqual(prior,(s.captured.candidate,s.captured.SELF,s.captured.TASK,s.captured.VARIANT))
        self.assertEqual(policy,s.c.POLICY)

    def test_original1200_scope_and_capture_limit(self):
        s.require_scope(1200)
        for wrong in (True,180,600,1201):
            with self.assertRaises(ValueError): s.require_scope(wrong)
        self.assertEqual(s.captured.bounded.LIMIT,32768)

    def test_binding_requires_current_aead_profile_inventory(self):
        with patch.object(s.candidate,'load_binding',side_effect=ValueError('FIXTURE_INVENTORY_DENIED')) as load:
            with self.assertRaisesRegex(ValueError,'FIXTURE_INVENTORY_DENIED'): s.load_binding(2)
        load.assert_called_once_with(s.candidate.PROFILE,2)

    def test_run_delegates_exact_inputs_and_restores(self):
        values = ({'fixture':'pin'},['names'],['modules']); destination = object(); seen = []
        def owned(*args):
            seen.append((args,s.captured.candidate,s.captured.SELF,s.captured.TASK)); return 7
        with patch.object(s.captured,'run_owned',side_effect=owned): self.assertEqual(s.run_owned(destination,*values),7)
        self.assertEqual(seen[0],((destination,*values),s.candidate,s.SELF,s.TASK))

    def test_capture_provenance_fails_closed_before_archive(self):
        class Reader:
            def pin(self,name): return {'path':name,'bytes':0,'sha256':'wrong'}
        with self.assertRaisesRegex(ValueError,'AEAD_FULL_CAPTURE_SOURCE_DRIFT'): s.capture_provenance(Reader(),{})

    def test_original_selector_and_complete_result_unchanged(self):
        names = [s.captured.cost.original.NAME,*[f'fixture::case_{i}' for i in range(248)]]
        s.captured.cost.original.select_names(names)
        with self.assertRaises(ValueError): s.captured.cost.original.select_names(names[:-1])
        valid = 'running 249 tests\ntest result: ok. 249 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n'
        s.captured.validate_output(valid)
        for wrong in (valid.replace('249 passed','248 passed'),valid.replace('0 filtered','1 filtered')):
            with self.assertRaises(ValueError): s.captured.validate_output(wrong)
