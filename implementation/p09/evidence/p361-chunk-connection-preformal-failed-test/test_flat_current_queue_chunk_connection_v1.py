"""Bounded synthetic connection contracts, not product/Native acceptance."""
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flat_current_queue_chunk_runtime_v1 as r

CHECKPOINT = lambda: None
LEAF_BYTES = None
METADATA_BYTES = None


def pin(name):
    return dict(path=name, bytes=1, sha256="a"*64)


class Contracts(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()
        if r.base.CONFIG is None:
            raise ValueError("CURRENT_STEP_MUST_BE_CONFIGURED")
        self.step = r.base.CONFIG
        self.data = dict(schema_version="hwpx-agent.p09-flat-chunk-connection/v1",
            index=126, before=119, run=1, base_step_pin=copy.deepcopy(self.step.pin),
            prior_terminal_data_pin=pin(r.prior.data_path(126)), failed_preflight_pin=copy.deepcopy(r.FAILED126),
            scratch_qualification_pin=copy.deepcopy(r.QUALIFICATION), connection_code_pins=[pin(n) for n in r.FILES])

    def tearDown(self):
        CHECKPOINT()

    def workspace(self, passes=1, size=3):
        return dict(workspace_used=True, workspace_allocations=1, workspace_bytes=65536,
            active_lease=False, leases=passes, lease_returns=passes, returned_bytes=size,
            invalid_readinto_returns=0, fresh_stream_read_before_every_exposed_chunk=True,
            unread_tail_exposed=False, file_bytes_or_hash_or_JSON_cache=False,
            original_MRO_wrappers_preserved=True, original_stream_open_and_identity_binding_preserved=True,
            original_checkpoints_pacing_parse_budget_and_final_hashes_preserved=True,
            added_sampler_query_thread_or_process=False, PC_freeze_resolved=False,
            readinto_attempts=2, readinto_completed=2)

    def row(self):
        return dict(bootstrap_metadata=dict(early_pressure=dict(reusable_chunk_metadata_reader=self.workspace()),
            read_passes=1, bytes_read=3), source_frame=dict(actual_byte_boundaries=[
                dict(reader_diagnostics=dict(read_passes=1, bytes_read=3, reusable_chunk_workspace=self.workspace()))
                for _ in range(2)]))

    def test_DATA_exact_shape_cursor_and_all_four_code_pins(self):
        self.assertIs(r.validate_data(self.data, self.step), self.data)
        for key, value in (("run", True), ("before", 118), ("index", 125),
                           ("failed_preflight_pin", None), ("scratch_qualification_pin", pin("x"))):
            bad = copy.deepcopy(self.data); bad[key] = value
            with self.subTest(), self.assertRaises(ValueError):
                r.validate_data(bad, self.step)
        bad = copy.deepcopy(self.data); bad["connection_code_pins"].pop()
        with self.assertRaises(ValueError): r.validate_data(bad, self.step)

    def test_prior_terminal_DATA_path_and_unknown_fields_rejected(self):
        bad = copy.deepcopy(self.data); bad["prior_terminal_data_pin"] = pin("tools/p09/wrong.py")
        with self.assertRaises(ValueError): r.validate_data(bad, self.step)
        bad = copy.deepcopy(self.data); bad["automatic_retry"] = True
        with self.assertRaises(ValueError): r.validate_data(bad, self.step)

    def test_only_first_product_attempt_and_canonical_root(self):
        self.assertEqual(r.attempt(126), 1)
        self.assertTrue(r.root_path(self.step).endswith("case126-current-runtime-run001.v1.json"))
        for index in (125, 250, True):
            with self.subTest(), self.assertRaises(ValueError): r.attempt(index)
        for run in (2, 3, True):
            with self.subTest(), self.assertRaises(ValueError): r.run_owned(run)
        with self.assertRaises(ValueError): r.accept(pin("implementation/p09/evidence/wrong.json"))

    def test_template_inserts_both_factories_without_global_default_changes(self):
        original = r.base.stable.stable.prior.build.BuildReader
        audit = r.chunk.original.AuditEvidenceReader._read
        engine, proof = r.template()
        env = engine.run_owned.__globals__
        self.assertIs(r.base.stable.stable.prior.build.BuildReader, original)
        self.assertIs(r.chunk.original.AuditEvidenceReader._read, audit)
        self.assertIsNot(env["build"].BuildReader, original)
        self.assertTrue(proof["reusable_chunk_factory_connection"]["original_engine_bytecode_unchanged"])
        self.assertEqual((env["SELF"], env["TEST"]), (r.SELF, r.TEST))
        self.assertIn("ChunkLeaf", [c.__name__ for c in env["BoundaryReader"].__mro__])

    def test_build_reader_open_pacer_and_owned_rate_envelope_preserved(self):
        engine, _ = r.template()
        Reader = engine.run_owned.__globals__["build"].BuildReader
        reader = Reader(r.c.ROOT, CHECKPOINT)
        reader.pacer = r.a.pressure.OwnedPacer()
        reader._source = lambda _: NS(open=lambda mode: io.BytesIO(b"abc"))
        reader._read("x.exe")
        report = r.workspace_report(reader)
        self.assertEqual(report["returned_bytes"], 3)
        self.assertEqual(reader.pacer.rate, 1048576)
        self.assertEqual(reader.open_pacer.rate, 20)

    def test_boundary_reader_uses_same_owner_pressure_and_exposes_actual_counts(self):
        engine, _ = r.template(); Reader = engine.run_owned.__globals__["BoundaryReader"]
        class Pressure:
            def __init__(self, original, owner): self.original = original; self.owner = owner
            def __call__(self): self.original()
            def summary(self): return dict(synthetic_pressure_only=True)
        owner = NS()
        reader = Reader(r.c.ROOT, CHECKPOINT, owner=owner, api=NS(PressureCheckpoint=Pressure))
        reader._source = lambda _: NS(open=lambda mode: io.BytesIO(b"abc"))
        reader.fresh_pin("x")
        self.assertIs(reader.pressure.owner, owner)
        diag = reader.diagnostics()
        r.actual_workspace(diag["reusable_chunk_workspace"], diag["read_passes"], diag["bytes_read"])
        self.assertEqual(diag["read_rates_by_kind"], dict(binary=1048576, other=2097152))

    def test_preflight_only_destination_metadata_changes_and_local_factory(self):
        original_dump = json.dump
        function = r.preflight_projection(METADATA_BYTES, LEAF_BYTES)
        self.assertIn("-chunk-preflight001.v1.json", function.__code__.co_consts)
        self.assertNotIn("-budget-terminal-preflight001.v1.json", function.__code__.co_consts)
        self.assertIsNot(function.__globals__["a"], r.a)
        self.assertIs(function.__globals__["binding_attempt"], r.binding_attempt)
        self.assertIs(function.__globals__["template"], r.template)
        self.assertIs(json.dump, original_dump)
        self.assertIsNot(function.__globals__["json"], json)

    def test_exact_frozen_preflight_and_leaf_sources_required(self):
        for metadata, leaf in ((METADATA_BYTES+b"\n", LEAF_BYTES), (METADATA_BYTES, LEAF_BYTES+b"\n")):
            with self.subTest(), self.assertRaises(ValueError): r.preflight_projection(metadata, leaf)

    def test_actual_binding_requires_metadata_and_both_whole_boundaries(self):
        self.assertTrue(r.actual_chunk_binding(self.row()))
        for layer in ("metadata", "before", "after"):
            bad = self.row()
            diag = bad["bootstrap_metadata"]["early_pressure"]["reusable_chunk_metadata_reader"] if layer == "metadata" else \
                bad["source_frame"]["actual_byte_boundaries"][0 if layer == "before" else 1]["reader_diagnostics"]["reusable_chunk_workspace"]
            diag["returned_bytes"] = 2
            with self.subTest(), self.assertRaises(ValueError): r.actual_chunk_binding(bad)
        bad = self.row(); bad["source_frame"]["actual_byte_boundaries"].pop()
        with self.assertRaises(ValueError): r.actual_chunk_binding(bad)

    def test_import_only_live_cache_wrong_counts_and_incomplete_calls_rejected(self):
        for key, value in (("workspace_used", False), ("active_lease", True), ("readinto_attempts", 0),
            ("readinto_completed", 1), ("lease_returns", 0), ("file_bytes_or_hash_or_JSON_cache", True),
            ("unread_tail_exposed", True), ("invalid_readinto_returns", 1), ("workspace_bytes", 131072)):
            bad = self.workspace(); bad[key] = value
            with self.subTest(), self.assertRaises(ValueError): r.actual_workspace(bad, 1, 3)

    def test_full_validator_delegated_before_additional_actual_workspace_check(self):
        environment = {"events": []}
        exec("def full(q,row,listing,oldbody,fresh,ctx,flat=True):\n events.append('full')\n return {'whole_oracle':True},{}", environment)
        with patch.object(r.accepted, "validate_candidate", environment["full"]):
            evidence, proof = r.validate_candidate(None, self.row(), None, None, None, None)
        self.assertEqual(environment["events"], ["full"])
        self.assertTrue(evidence["whole_oracle"])
        self.assertTrue(proof["actual_metadata_and_two_whole_boundary_chunk_usage_checked"])
        bad = self.row(); bad["source_frame"]["actual_byte_boundaries"] = []
        with patch.object(r.accepted, "validate_candidate", environment["full"]), self.assertRaises(ValueError):
            r.validate_candidate(None, bad, None, None, None, None)

    def test_prebody_failure_still_rejected_before_capture_access(self):
        with self.assertRaises(ValueError):
            r.validate_candidate(None, dict(state="DEFERRED_NOT_STARTED"), None, None, None, None)

    def test_prepare_retains_original_counted_root_projection(self):
        raw = b"def prepare(q, root_pin):\n step=r.CONFIG\n require(root_pin['path']==f'implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run001.v1.json','ROOT')\n return 'whole-oracle'\n"
        self.assertTrue(callable(r.prepare_projection(raw)))
        with self.assertRaises(ValueError): r.prepare_projection(raw.replace(b"run001", b"run003"))

    def test_no_workspace_claim_before_actual_read(self):
        self.assertEqual(r.workspace_report(NS()), dict(workspace_used=False))


if __name__ == "__main__": unittest.main()
