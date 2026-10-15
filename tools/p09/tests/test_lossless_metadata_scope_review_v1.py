"""Scope correction must not weaken other original v4 accounting checks."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import current_queue_successor_lossless_runtime_v4 as old
import lossless_metadata_scope_review_v1 as m
from tests import test_current_queue_successor_lossless_runtime_v4 as fixtures


class Tests(unittest.TestCase):
    def setUp(self):
        fixture=fixtures.Tests();fixture.setUp()
        self.row=fixture.row;self.api=fixture.api
        self.descriptors=[dict(semantic_original_pin=dict(path="s",bytes=10),physical_envelope_pin=dict(bytes=4)),
            dict(semantic_original_pin=dict(path="other",bytes=20),physical_envelope_pin=dict(bytes=6))]
        self.binding=NS(descriptors=lambda:self.descriptors)
        self.pref=dict(current_source_pins=[dict(path="s",bytes=10)])
        self.qual=dict(source_pins=[dict(path="s",bytes=10)])
        self.row["bootstrap_metadata"]["early_pressure"]["explicit_fresh_lossless_metadata"]["mapping_count"]=2
        self.row["source_frame"]["shared_metadata_frame_decoder"]["Frame_completed"]=4
        self.raw=(Path(__file__).resolve().parents[3]/m.V4["path"]).read_bytes()
    def validate(self,row=None):
        names=m.declared_metadata(self.binding,self.pref,self.qual,self.api)
        return m.project_accounting(self.raw,old.validate_accounting.__globals__,names)(row or self.row,self.binding,self.api)
    def test_two_sealed_declarations_distinguish_metadata_and_frame(self):
        self.assertEqual(m.declared_metadata(self.binding,self.pref,self.qual,self.api),frozenset({"s"}))
        self.assertTrue(self.validate())
    def test_full_frame_count_still_required(self):
        self.row["source_frame"]["shared_metadata_frame_decoder"]["Frame_completed"]=2
        with self.assertRaises(ValueError):self.validate()
    def test_missing_and_extra_metadata_mapping_rejected(self):
        for counts in ({},{"s":2,"other":1}):
            row=copy.deepcopy(self.row);row["bootstrap_metadata"]["early_pressure"]["explicit_fresh_lossless_metadata"]["semantic_read_counts"]=counts
            with self.assertRaises(ValueError):self.validate(row)
    def test_different_sealed_declarations_rejected(self):
        self.qual["source_pins"].append(dict(path="other",bytes=20))
        with self.assertRaises(ValueError):self.validate()
    def test_duplicate_and_wrong_semantic_pin_rejected(self):
        for pins in ([dict(path="s",bytes=11)],[dict(path="s",bytes=10)]*2):
            self.pref["current_source_pins"]=pins
            with self.assertRaises(ValueError):self.validate()
    def test_original_byte_counts_and_cache_prohibitions_retained(self):
        for change in (dict(mapped_physical_bytes_read=20),dict(mapped_semantic_bytes_restored=8),dict(byte_hash_or_JSON_cache=True)):
            row=copy.deepcopy(self.row);row["bootstrap_metadata"]["early_pressure"]["explicit_fresh_lossless_metadata"].update(change)
            with self.assertRaises(ValueError):self.validate(row)
    def test_shared_budget_and_owner_checks_retained(self):
        for change in (dict(Frame_registered=False),dict(original_resource_and_owner_checks_first=False),dict(total_decoder_work_seconds=6.0)):
            row=copy.deepcopy(self.row);row["source_frame"]["shared_metadata_frame_decoder"].update(change)
            with self.assertRaises(ValueError):self.validate(row)
    def test_source_drift_rejected_and_original_namespace_unchanged(self):
        original=old.validate_accounting
        with self.assertRaises(ValueError):m.project_accounting(self.raw+b"\n",original.__globals__,{"s"})
        self.assertTrue(self.validate());self.assertIs(old.validate_accounting,original)
    def test_candidate_cannot_seed_expected_scope(self):
        self.pref["current_source_pins"]=[];self.qual["source_pins"]=[]
        with self.assertRaises(ValueError):self.validate()


if __name__=="__main__":unittest.main()
