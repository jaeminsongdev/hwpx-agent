"""Mutation controls against retained failed evidence; no HWP or Native worker."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import block_selection_recovery666 as m
import run_prepared_bookmark_native631 as p

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=p.codec.unpack(json.loads((p.r.c.ROOT/m.RECEIPT).read_text(encoding='utf-8')))
        cls.trace=json.loads((p.r.c.ROOT/m.TRACE).read_text(encoding='utf-8'))
    def setUp(self):self.r=copy.deepcopy(self.original);self.t=copy.deepcopy(self.trace)
    def denied(self):
        with self.assertRaises((ValueError,KeyError)):m.validate(self.r,self.t)
    def test_retained_stop_only(self):
        v=m.validate(self.r,self.t);self.assertEqual(v['observations_recorded'],8)
        self.assertFalse(any(v[k]for k in('Native_replayed','source_capture_executed','selection_API_qualified','P09_complete','historical_final_hashes_claimed')))
    def test_worker_cleanup_missing(self):self.r['capture_worker']['cleanup']=False;self.denied()
    def test_unexpected_error(self):self.t['error_code']='UNEXPECTED';self.denied()
    def test_truncated_observations(self):self.t['selection_probe'].pop();self.denied()
    def test_raw_error_message(self):self.t['selection_probe'][3]['message']='PRIVATE';self.denied()
    def test_owner_birth_changed(self):self.t['dual_identity_evidence'][0]['observation']['kernel_creation_filetime_100ns']='0';self.denied()
    def test_historical_closure_fabricated(self):self.r['partial_case_source_boundary']['closed']=True;self.denied()
    def test_source_artifact_promoted(self):self.t['artifacts']={'created.hwpx':{}};self.denied()
    def test_conflicting_pins(self):
        self.r['partial_case_source_boundary']['readers']['source']['pins'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):m.original_pins(self.r)
    def test_original_pins_deduplicated(self):
        rows=m.original_pins(self.r);self.assertEqual({k:len(v)for k,v in rows.items()},dict(source=261,native=1,shell=1,runtime=2))

if __name__=='__main__':
    result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),
        failed_tests=[t.id()for t,_ in result.errors+result.failures],actual_native_started=False)))
    raise SystemExit(0 if result.wasSuccessful()else 2)
