"""Bounded run002 graph: no history IO or relaxed reader limits."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import successor_bounded_graph_bootstrap_v3 as m
import flat_current_queue_envelope_runtime_v28 as controller

class Tests(unittest.TestCase):
    def test_actual_run002_25_pairs_and_exact_manifest(self):
        graph,proof=m.load(controller.M.old,lambda:None)
        self.assertEqual(len(graph.binding.descriptors()),25)
        self.assertEqual(graph.worker.TASK,"case160-current-r002-tests")
        self.assertEqual(dict(graph.binding.manifest_pin),m.MANIFEST)
        self.assertEqual(proof["historical_receipts_read_by_this_reader"],0)
    def test_original_read_function_code_is_retained(self):
        self.assertIs(m.Reader._read.__code__,m.original.Reader._read.__code__)
    def test_original_limits_remain(self):
        _,proof=m.load(controller.M.old,lambda:None)
        self.assertLessEqual(proof["bounded_reader_reads"],64)
        self.assertLessEqual(proof["bounded_reader_bytes"],262144)
        self.assertTrue(proof["original_reader_code_and_64_reads_262144_bytes_limits_retained"])
    def test_history_denied_before_open(self):
        r=m.Reader(controller.M.old,lambda:None)
        with patch.object(Path,"open") as opened:
            with self.assertRaises(ValueError):r.pin(m.partial.ROOT["path"])
        opened.assert_not_called()
    def test_unknown_source_denied_before_open(self):
        r=m.Reader(controller.M.old,lambda:None)
        with patch.object(Path,"open") as opened:
            with self.assertRaises(ValueError):r.pin("tools/p09/wrong.py")
        opened.assert_not_called()
    def test_same_parent_frame_worker_oracle_module(self):
        g,_=m.load(controller.M.old,lambda:None)
        self.assertIs(g.parent.access.source,g.binding_module)
        self.assertIs(g.parent.original.frames.binding_module,g.binding_module)
        self.assertIs(g.worker.raw_policy.source,g.binding_module)
        self.assertIs(g.full_oracle.binding_module,g.binding_module)
    def test_original_capsule_and_reader_default_namespaces_unchanged(self):
        allowed=m.original.MANIFEST
        m.load(controller.M.old,lambda:None)
        self.assertIs(m.original.MANIFEST,allowed)
        self.assertIn("case159",m.original.MANIFEST["path"])
