import copy
import io
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_compression_full_stored as s


class CompressionFullStoredTests(unittest.TestCase):
    def output(self): return 'running 249 tests\n'+'.'*249+'\ntest result: ok. 249 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.00s\n'
    def test_exact249_complete_terse_result(self): s.validate_output(self.output())
    def test_partial_failed_ignored_filtered_or_duplicate_result_denied(self):
        for wrong in (self.output().replace('249 passed','248 passed'), self.output().replace('0 failed','1 failed'),
                self.output().replace('0 ignored','1 ignored'), self.output().replace('0 filtered','1 filtered'),
                self.output().replace('running 249','running 248'), self.output()+self.output()):
            with self.assertRaises(ValueError): s.validate_output(wrong)
    def test_empty_or_unbounded_result_denied(self):
        for wrong in ('', ' '*32769):
            with self.assertRaises(ValueError): s.validate_output(wrong)
    def test_existing1200_fullsuite_limit_cannot_be_extended(self):
        before=copy.deepcopy(s.c.POLICY);s.require_scope(1200)
        for wrong in (True,180,600,1201):
            with self.assertRaises(ValueError): s.require_scope(wrong)
        self.assertEqual(before,s.c.POLICY)
    def worker(self,go='P149_GO\n',member=True):
        class Kernel:
            def GetCurrentProcess(self): return 1
            def IsProcessInJob(self,p,j,out): out._obj.value=member;return True
        calls=[]
        with patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())),patch.object(s.c.sys,'stdin',io.StringIO(go)), \
                patch.object(s.c.shutil,'which',return_value='cargo'),patch.object(s.subprocess,'call',side_effect=lambda a,**kw:calls.append((a,kw)) or 0):
            result=s.worker()
        return result,calls
    def test_original_worker_exact_current_config_and_full_target(self):
        result,calls=self.worker();self.assertEqual(result,0);self.assertEqual(len(calls),1)
        args,kw=calls[0];self.assertEqual(args[1:83],[v for e in s.candidate.CONFIG for v in ('--config',e)])
        self.assertEqual(args[83:83+len(s.ARGS)],s.ARGS)
        self.assertEqual(args[-3:],['--','--test-threads=1','--format=terse'])
        self.assertNotIn('--exact',args);self.assertNotIn('--ignored',args);self.assertNotIn('--skip',args)
        self.assertNotIn('--nocapture',args);self.assertNotIn('--no-capture',args);self.assertNotIn('--show-output',args)
        self.assertEqual(kw['env']['RUST_TEST_NOCAPTURE'],'0')
        self.assertEqual(kw['env']['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS'],'true')
        self.assertEqual(kw['env']['CARGO_PROFILE_TEST_OVERFLOW_CHECKS'],'true')
    def test_real_GO_and_Job_membership_gate_preserved(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError): self.worker(go,member)
    def test_signed_original_stage_observer_requires_whole16(self):
        self.assertEqual(s.cost.observe_cost('')['fully_observed_case_sequences'],0)
        with self.assertRaises(ValueError):s.cost.observe_cost('P149_SIGNED_COST:0:changed_consume:1\n')
    def test_candidate_profile_and_all249_original_name_selector_retained(self):
        s.candidate.config_contract(s.candidate.CONFIG);self.assertEqual(len(s.candidate.CONFIG),41)
        names=[s.cost.original.NAME,*[f'fixture::case_{i}' for i in range(248)]]
        s.cost.original.select_names(names)
        with self.assertRaises(ValueError):s.cost.original.select_names(names[:-1])

    def fixture(self, output=None, errors='', returncode=0):
        capture=s.FullCapture.__new__(s.FullCapture)
        capture.accepted=False;capture.lock=threading.Lock();capture.output_limit=32768
        capture.buffers={'stdout':bytearray((self.output() if output is None else output).encode()),'stderr':bytearray(errors.encode())}
        capture.received_bytes={n:len(b) for n,b in capture.buffers.items()}
        capture.parse_markers=False;capture.error=None;capture.markers=[];capture.observations=[]
        capture.threads=[];capture.process=SimpleNamespace(returncode=returncode,wait=lambda timeout:None)
        return capture

    def test_captured_current_complete_suite_qualifies_without_stage_markers(self):
        capture=self.fixture();capture.communicate(1)
        self.assertTrue(capture.accepted)
        self.assertEqual(capture.diagnostics()['error_code'],None)
        self.assertFalse(capture.diagnostics()['raw_log_content_included'])

    def test_nonzero_or_unfinished_suite_never_qualifies(self):
        capture=self.fixture(returncode=1);capture.communicate(1);self.assertFalse(capture.accepted)
        capture=self.fixture(output='running 249 tests\n')
        with self.assertRaises(ValueError):capture.communicate(1)
        self.assertFalse(capture.accepted)

    def test_uncaptured_success_receipts_or_stages_denied(self):
        for marker in ('P149_SIGNED_COST:', 'P120_ORIGINAL_CORPUS_RECEIPT:', 'P121_CHANGED_CORPUS_RECEIPT:'):
            capture=self.fixture(errors=marker+'fixture\n')
            with self.assertRaisesRegex(ValueError,'FULL_CAPTURE_SUCCESS_OUTPUT_NOT_CAPTURED'):capture.communicate(1)
            self.assertFalse(capture.accepted)

    def test_unchanged_output_limit_exposes_closed_error_without_raw_log(self):
        capture=self.fixture(output='');capture._accept('stderr',b'x'*32768)
        capture._accept('stderr',b'x')
        with self.assertRaisesRegex(ValueError,'FULL_CAPTURE_OUTPUT_LIMIT'):capture.progress()
        row=capture.diagnostics()
        self.assertEqual(row['buffered_bytes']['stderr'],32768)
        self.assertEqual(row['received_bytes']['stderr'],32769)
        self.assertEqual(row['per_stream_limit_bytes'],32768)
        self.assertEqual(row['error_code'],'FULL_CAPTURE_OUTPUT_LIMIT')
        self.assertFalse(row['raw_log_content_included'])

    def test_inherited_nocapture_cannot_override_worker(self):
        with patch.dict(s.c.os.environ,{'RUST_TEST_NOCAPTURE':'1'}):
            _,calls=self.worker()
        self.assertEqual(calls[0][1]['env']['RUST_TEST_NOCAPTURE'],'0')
        self.assertEqual(s.capture_code('private fixture text'),'FULL_CAPTURE_UNCLASSIFIED')
