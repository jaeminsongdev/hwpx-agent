"""Independent expected accounting and private import-map contracts."""
import copy
from types import FunctionType,SimpleNamespace as NS
import unittest
import current_queue_successor_lossless_runtime_v4 as m

CHECKPOINT=lambda:None


def require(ok,label):
    if not ok:raise ValueError(label)
def exact(left,right,label):
    require(type(left) is type(right) and left==right,label)
def fields(row,expected,label):
    for key,value in expected.items():exact(row.get(key),value,label)


class Tests(unittest.TestCase):
    def setUp(self):
        CHECKPOINT();self.api=NS(fields=fields,exact=exact)
        self.binding=NS(descriptors=lambda:[dict(semantic_original_pin=dict(path="s",bytes=10),physical_envelope_pin=dict(bytes=4))])
        explicit=dict(mapping_count=1,semantic_read_counts={"s":2},mapped_read_attempts=2,mapped_read_completed=2,
            mapped_physical_bytes_read=8,mapped_semantic_bytes_restored=20,decoded_bytes_not_added_to_physical_counter=True,
            byte_hash_or_JSON_cache=False,fresh_physical_read_and_decode_per_request=True,original_unmapped_reader_retained=True,
            decoder=dict(limit_seconds=5.0,attempted=2,completed=2,active=False,error_seen=False,elapsed_work_seconds=1.0))
        shared=dict(shared_limit_seconds=5.0,metadata_registered=True,Frame_registered=True,metadata_completed=2,Frame_completed=2,
            terminal_error_seen=False,original_budget_classes_run_methods_and_counters_retained=True,original_resource_and_owner_checks_first=True,
            Frame_evidence_not_relabelled_as_combined=True,new_sampler_thread_or_process=False,metadata_decoder_work_seconds=1.0,
            Frame_decoder_work_seconds=2.0,total_decoder_work_seconds=3.0,checks=10)
        self.row=dict(bootstrap_metadata=dict(bytes_read=8,early_pressure=dict(explicit_fresh_lossless_metadata=explicit)),
            source_frame=dict(shared_metadata_frame_decoder=shared,aggregate_envelope_decoder=dict(elapsed_decoder_work_seconds=2.0)))
    def tearDown(self):CHECKPOINT()
    def test_exact_independent_mapping_accounting(self):
        self.assertTrue(m.validate_accounting(self.row,self.binding,self.api))
    def test_semantic_bytes_not_physical_or_missing_mapping(self):
        for change in (dict(mapped_physical_bytes_read=20),dict(semantic_read_counts={}),dict(byte_hash_or_JSON_cache=True)):
            row=copy.deepcopy(self.row);row["bootstrap_metadata"]["early_pressure"]["explicit_fresh_lossless_metadata"].update(change)
            with self.assertRaises(ValueError):m.validate_accounting(row,self.binding,self.api)
    def test_frame_metadata_work_mismatch_rejected(self):
        row=copy.deepcopy(self.row);row["source_frame"]["shared_metadata_frame_decoder"]["metadata_decoder_work_seconds"]=2.0
        with self.assertRaises(ValueError):m.validate_accounting(row,self.binding,self.api)
    def test_sum_over_five_even_individual_budget_under_five(self):
        row=copy.deepcopy(self.row);row["bootstrap_metadata"]["early_pressure"]["explicit_fresh_lossless_metadata"]["decoder"]["elapsed_work_seconds"]=3.0
        row["source_frame"]["aggregate_envelope_decoder"]["elapsed_decoder_work_seconds"]=3.0
        row["source_frame"]["shared_metadata_frame_decoder"].update(metadata_decoder_work_seconds=3.0,Frame_decoder_work_seconds=3.0,total_decoder_work_seconds=6.0)
        with self.assertRaises(ValueError):m.validate_accounting(row,self.binding,self.api)
    def test_frame_not_registered_or_false_counts_rejected(self):
        for change in (dict(Frame_registered=False),dict(Frame_completed=3),dict(metadata_completed=True)):
            row=copy.deepcopy(self.row);row["source_frame"]["shared_metadata_frame_decoder"].update(change)
            with self.assertRaises(ValueError):m.validate_accounting(row,self.binding,self.api)
    def test_private_import_override_keeps_original_code_and_other_dependencies(self):
        def original():
            import fixture_v4_dependency
            import math
            return fixture_v4_dependency,math.sqrt(4)
        env=dict(original.__globals__,__name__="p09_exact_fixture");fn=FunctionType(original.__code__,env);ns=NS(original=fn);value=object()
        m.override_import(ns,"fixture_v4_dependency",value)
        self.assertIs(ns.original.__code__,fn.__code__)
        self.assertEqual(ns.original(),(value,2.0))
        def helper(q,ctx,a,bridge):return q,ctx,a,bridge
        def closed(q,ctx,a):return previous_stops(q,ctx,a,"bridge")
        alias_env=dict(closed.__globals__,__name__="p09_exact_alias",previous_stops=helper)
        alias=FunctionType(closed.__code__,alias_env);namespace=NS(previous_stops=alias)
        m.override_import(namespace,"fixture_v4_dependency",value)
        self.assertIs(alias_env["previous_stops"],helper)
        self.assertEqual(namespace.previous_stops(1,2,3),(1,2,3,"bridge"))


if __name__=="__main__":unittest.main()
