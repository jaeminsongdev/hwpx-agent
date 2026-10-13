import copy
import json
import unittest
from pathlib import Path
import close_r07_compiler_output as d

class R07CompilerPostClosingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Existing redacted receipt is a fixture, not evidence of post-closing.
        cls.original=json.loads((d.b.c.ROOT/d.ACTUAL['path']).read_text(encoding='utf-8'))
    def test_clean_compiler_post_cpu_stop_metadata_only(self):
        before=copy.deepcopy(self.original);self.assertEqual(len(d.metadata_scope(before)),1418)
        self.assertEqual(before,self.original);self.assertFalse(before['source_freeze_exact_after'])
    def test_early_stop_or_failed_compiler_denied(self):
        for field,value in (('operation_phase','source_freeze'),('exit_code',1),('exit_code',False)):
            row=copy.deepcopy(self.original);row[field]=value
            with self.assertRaises(ValueError):d.metadata_scope(row)
    def test_retroactive_success_or_wrong_stop_denied(self):
        for field,value in (('state',d.b.PASS),('source_freeze_exact_after',True),('stop_reason','STOP_DURATION_LIMIT')):
            row=copy.deepcopy(self.original);row[field]=value
            with self.assertRaises(ValueError):d.metadata_scope(row)
    def test_disabled_assertions_or_unrelated_executable_denied(self):
        for key,value in (('debug_assertions',False),('test',False),('opt_level','0')):
            row=copy.deepcopy(self.original);row['build_result']['catalog_profile'][key]=value
            with self.assertRaises(ValueError):d.metadata_scope(row)
        row=copy.deepcopy(self.original);row['build_result']['executable_path']='target/stale.exe'
        with self.assertRaises(ValueError):d.metadata_scope(row)
    def test_truncated_or_partial_stream_never_eligible(self):
        row=copy.deepcopy(self.original);row['build_result']['validated_stream']['raw_output_truncated']=True
        with self.assertRaises(ValueError):d.metadata_scope(row)
        row=copy.deepcopy(self.original);row['capture_diagnostics']['validated_compiler_progress']['closing_observed']=False
        with self.assertRaises(ValueError):d.metadata_scope(row)
    def test_source_or_runtime_claim_tampering_denied(self):
        row=copy.deepcopy(self.original);row['source_freeze'].append(row['source_freeze'][0])
        with self.assertRaises(ValueError):d.metadata_scope(row)
        row=copy.deepcopy(self.original);row['full249_current_qualified']=True
        with self.assertRaises(ValueError):d.metadata_scope(row)

if __name__=='__main__':unittest.main()
