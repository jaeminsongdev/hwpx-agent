import copy
import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import run_reconstruction_stage_profile as s


class ReconstructionStageTests(unittest.TestCase):
    def row(self):
        return {'schema_version':'hwpx-agent.p09-reconstruction-stage-timing/v1','qualification':s.QUAL,'originals':36,'whole_graph_receipts_equal':36,'tamper_denied':36,'formula_targets':16,'source_cell_bindings':128,'stages':{n:{'calls':36,'total_us':3600,'min_us':100,'max_us':100} for n in s.STAGES},'runtime_signed_consumer_qualified':False,'product_complete':False,'P09_gate':'OPEN'}
    def worker(self,go='P149_GO\n',member=True):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,process,job,out):out._obj.value=member;return True
        calls=[]
        with patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())),patch.object(s.c.sys,'stdin',io.StringIO(go)),patch.object(s.c.shutil,'which',return_value='cargo'),patch.object(s.subprocess,'call',side_effect=lambda args,**kwargs:calls.append((args,kwargs)) or 0):
            result=s.worker()
        return result,calls
    def test_exact_complete_numeric_profile(self):
        row=self.row();self.assertEqual(s.validate(json.dumps(row)),row)
    def test_partial_corpus_or_tamper_coverage_is_denied(self):
        for key in ('originals','whole_graph_receipts_equal','tamper_denied','formula_targets','source_cell_bindings'):
            row=self.row();row[key]-=1
            with self.assertRaises(ValueError):s.validate(json.dumps(row))
    def test_product_or_signed_qualification_is_denied(self):
        for key in ('product_complete','runtime_signed_consumer_qualified'):
            row=self.row();row[key]=True
            with self.assertRaises(ValueError):s.validate(json.dumps(row))
    def test_stage_coverage_and_bounds_cannot_be_relaxed(self):
        for key,value in (('calls',35),('min_us',-1),('total_us',1),('max_us',True)):
            row=self.row();row['stages']['source_import'][key]=value
            with self.assertRaises(ValueError):s.validate(json.dumps(row))
    def test_unknown_or_duplicate_json_keys_are_denied(self):
        row=self.row();row['extra']=1
        with self.assertRaises(ValueError):s.validate(json.dumps(row))
        with self.assertRaises(ValueError):s.validate('{"originals":36,"originals":36}')
    def test_original_default_body_is_exact_after_closed_extension_removal(self):
        old='fn main(){\n    ORIGINAL();\n}\n';current='fn main(){\n'+s.DISPATCH+'    ORIGINAL();\n}\n\n'+s.MARKER+'\nfn reconstruction_timing_probe() {}\n'
        s.default_body_exact(current,old)
        with self.assertRaises(ValueError):s.default_body_exact(current.replace('ORIGINAL();',''),old)
    def test_original_worker_has_exact_config_and_numeric_mode(self):
        result,calls=self.worker();self.assertEqual(result,0);self.assertEqual(len(calls),1)
        args,kwargs=calls[0];self.assertEqual(args[-2:],['--','--reconstruction-timing-only'])
        self.assertEqual(args[1:43],[v for e in s.profile.CONFIG for v in ('--config',e)])
        self.assertEqual(kwargs['env']['CARGO_PROFILE_TEST_DEBUG_ASSERTIONS'],'true')
        self.assertNotIn('--test-threads=1',args)
    def test_original_GO_and_Job_membership_gate_is_not_mocked_away(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.worker(go,member)
    def test_duration_remains_finite_without_cap_change(self):
        before=copy.deepcopy(s.c.POLICY);s.require_duration(180)
        for bad in (True,29,181,600):
            with self.assertRaises(ValueError):s.require_duration(bad)
        self.assertEqual(before,s.c.POLICY)
    def test_output_budget_is_not_unbounded(self):
        with self.assertRaises(ValueError):s.validate(' '*4097)
