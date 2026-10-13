"""Explicit connection contracts; not actual product/runtime acceptance."""
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flat_current_queue_source_stat_runtime_v2 as r
import stat

CHECKPOINT = lambda: None
LEAF_BYTES = METADATA_BYTES = FAILED_ROW = BUILD_BYTES = None


def pin(name):
    return dict(path=name, bytes=1, sha256="a"*64)


class Contracts(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()
        self.step = r.base.CONFIG
        if self.step is None or self.step.index != 127:
            raise ValueError("REVIEWED127_CONFIG_REQUIRED")
        self.data = dict(schema_version="hwpx-agent.p09-flat-source-stat-connection/v2",
            index=127, before=120, run=2, base_step_pin=copy.deepcopy(self.step.pin),
            prior_chunk_data_pin=pin(r.prior.data_path(127)), failed_runtime_pins=[copy.deepcopy(r.FAILED127)],
            source_qualification_pin=pin(r.QUALIFICATION_PATH),
            connection_qualification_pin=pin(r.CODE_QUALIFICATION_PATH),
            connection_code_pins=[pin(n) for n in r.FILES],
            prior_source_data_pin=pin(r.prior_source_data_path(127)),
            prior_source_code_pins=[pin(n) for n in r.PRIOR_SOURCE_FILES],
            failed_preflight_pin=copy.deepcopy(r.FAILED_PREFLIGHT))

    def tearDown(self):
        CHECKPOINT()

    def source(self):
        return dict(source_requests=1, fresh_no_follow_stat_attempts=1,
            ordinary_windows_snapshot_decisions=1, exact_original_fallback_requests=0,
            ordinary_nonfile_rejections=0, original_logical_source_predicates_retained=True,
            stat_result_cached_or_reused_between_source_requests=False, original_default_reader_mutated=False,
            held_Native_path_guard_replaced=False, extra_sampler_query_thread_or_process=False,
            complete_source_reads_rates_or_deadlines_reduced=False, PC_freeze_resolved=False)

    def ancestor(self):
        return dict(member_visits=2, fresh_stat_attempts=2, ordinary_snapshot_decisions=2, original_fallbacks=0,
            original_all_ancestors_and_file_required_check_retained=True,
            snapshot_cached_between_member_visits=False, original_reparse_or_error_fallback_retained=True,
            original_default_direct_path_mutated=False, extra_sampler_query_thread_or_process=False, PC_freeze_resolved=False)

    def row(self):
        return dict(bootstrap_metadata=dict(read_passes=1,
            early_pressure=dict(single_snapshot_metadata_source=self.source(),
                single_snapshot_ancestor_source=self.ancestor())))

    def test_DATA_exact_shape_and_strict_reviewed_cursor(self):
        self.assertIs(r.validate_data(self.data, self.step), self.data)
        for key, value in (("run", True), ("run", 1), ("before", 119), ("index", 126)):
            bad = copy.deepcopy(self.data); bad[key] = value
            with self.subTest(), self.assertRaises(ValueError): r.validate_data(bad, self.step)

    def test_DATA_all_code_and_qual_paths_no_unknown_keys(self):
        for key in ("source_qualification_pin", "connection_qualification_pin", "prior_chunk_data_pin"):
            bad = copy.deepcopy(self.data); bad[key] = pin("tools/p09/wrong.py")
            with self.subTest(), self.assertRaises(ValueError): r.validate_data(bad, self.step)
        bad = copy.deepcopy(self.data); bad["connection_code_pins"].pop()
        with self.assertRaises(ValueError): r.validate_data(bad, self.step)
        bad = copy.deepcopy(self.data); bad["automatic_retry"] = True
        with self.assertRaises(ValueError): r.validate_data(bad, self.step)

    def test_failed127_pin_is_mandatory_and_not_replaced(self):
        for value in ([], [pin(r.FAILED127["path"])], [r.FAILED127, r.FAILED127]):
            bad = copy.deepcopy(self.data); bad["failed_runtime_pins"] = value
            with self.subTest(), self.assertRaises(ValueError): r.validate_data(bad, self.step)

    def test_only_explicit127_run2_later_first_runs_and_no_run1_replay(self):
        self.assertEqual(r.attempt(127), 2)
        self.assertEqual(r.attempt(128), 1)
        self.assertEqual(r.attempt(249), 1)
        for index in (126, 250, True):
            with self.subTest(), self.assertRaises(ValueError): r.attempt(index)
        for run in (1, 3, True):
            with self.subTest(), self.assertRaises(ValueError): r.run_owned(run)
        self.assertTrue(r.root_path(self.step).endswith("case127-current-runtime-run002.v1.json"))
        with self.assertRaises(ValueError): r.accept(pin(r.FAILED127["path"]))

    def test_real_failed127_is_prebody_only_and_rejects_fabricated_success(self):
        self.assertTrue(r.review_failure(FAILED_ROW))
        for key, value in (("worker_created", True), ("product_body_observed", True),
                           ("cleanup_confirmed", False), ("source_freeze", [pin("x")]),
                           ("source_frame", {}), ("passed_test_names", [self.step.case])):
            bad = copy.deepcopy(FAILED_ROW); bad[key] = value
            with self.subTest(), self.assertRaises(ValueError): r.review_failure(bad)

    def test_template_local_metadata_factory_and_original_defaults_unchanged(self):
        default = r.base.stable.stable.prior.build.BuildReader
        source = r.snapshot.original.AuditEvidenceReader._source
        engine, proof = r.template(); env = engine.run_owned.__globals__
        self.assertIs(r.base.stable.stable.prior.build.BuildReader, default)
        self.assertIs(r.snapshot.original.AuditEvidenceReader._source, source)
        self.assertEqual((env["SELF"], env["TEST"]), (r.SELF, r.TEST))
        self.assertIn("SnapshotReader", [x.__name__ for x in env["build"].BuildReader.__mro__])
        self.assertIn("ChunkLeaf", [x.__name__ for x in env["build"].BuildReader.__mro__])
        self.assertTrue(proof["reusable_chunk_factory_connection"]["metadata_reader_only"])
        self.assertTrue(proof["reusable_chunk_factory_connection"]["source_stat_factory"]["original_build_source_pin_shape_and_ancestor_wrappers_retained"])
        # A malformed source name must still be denied by the original wrapper
        # before the fresh leaf stat can run. This is not a filesystem fixture.
        reader = env["build"].BuildReader(r.c.ROOT, CHECKPOINT)
        with patch.object(r.snapshot, "source", side_effect=AssertionError("LEAF_MUST_NOT_RUN")), self.assertRaises(ValueError):
            reader._source("../outside")

    def test_held_Native_boundary_factory_does_not_gain_snapshot_wrapper(self):
        engine, proof = r.template(); Reader = engine.run_owned.__globals__["BoundaryReader"]
        self.assertNotIn("SnapshotReader", [x.__name__ for x in Reader.__mro__])
        self.assertIn("ChunkLeaf", [x.__name__ for x in Reader.__mro__])
        self.assertFalse(proof["reusable_chunk_factory_connection"]["held_Native_boundary_source_adapter_changed"])

    def test_metadata_reader_retains_scratch_open_pacer_and_original_byte_rates(self):
        engine, _ = r.template(); Reader = engine.run_owned.__globals__["build"].BuildReader
        reader = Reader(r.c.ROOT, CHECKPOINT)
        reader.pacer = r.a.pressure.OwnedPacer()
        reader._source = lambda name: NS(open=lambda mode: io.BytesIO(b"abc"))
        reader._read("x.exe")
        self.assertEqual(reader.pacer.rate, 1048576)
        self.assertEqual(reader.open_pacer.summary()["request_limit_per_second"], 20)
        self.assertEqual(reader.open_pacer.summary()["requests"], 1)
        self.assertEqual(r.prior.workspace_report(reader)["returned_bytes"], 3)

    def test_preflight_only_fresh_destination_and_local_factory_changes(self):
        default_reader = r.a.AcceptanceReader; default_dump = json.dump
        function = r.preflight_projection(METADATA_BYTES, LEAF_BYTES)
        self.assertIn("-source-stat-ancestor-preflight001.v1.json", function.__code__.co_consts)
        self.assertNotIn("-chunk-preflight001.v1.json", function.__code__.co_consts)
        self.assertIs(function.__globals__["binding_attempt"], r.binding_attempt)
        self.assertIs(function.__globals__["template"], r.template)
        self.assertIsNot(function.__globals__["a"].AcceptanceReader, default_reader)
        self.assertIs(r.a.AcceptanceReader, default_reader)
        self.assertIs(json.dump, default_dump)

    def test_original_preflight_and_leaf_pins_cannot_drift(self):
        for raw, leaf in ((METADATA_BYTES+b"\n", LEAF_BYTES), (METADATA_BYTES, LEAF_BYTES+b"\n")):
            with self.subTest(), self.assertRaises(ValueError): r.preflight_projection(raw, leaf)

    def test_actual_usage_complete_counts_and_legal_original_fallbacks(self):
        self.assertTrue(r.actual_source_binding(self.row()))
        row = self.row(); row["bootstrap_metadata"]["read_passes"] = 2
        diag = row["bootstrap_metadata"]["early_pressure"]["single_snapshot_metadata_source"]
        diag.update(source_requests=2, fresh_no_follow_stat_attempts=2, exact_original_fallback_requests=1)
        self.assertTrue(r.actual_source_binding(row))

    def test_import_only_cached_wrong_or_boolean_counts_rejected(self):
        for key, value in (("source_requests", 0), ("source_requests", True),
            ("fresh_no_follow_stat_attempts", 2), ("ordinary_windows_snapshot_decisions", 0),
            ("exact_original_fallback_requests", 1), ("ordinary_nonfile_rejections", 1),
            ("stat_result_cached_or_reused_between_source_requests", True)):
            bad = self.row(); bad["bootstrap_metadata"]["early_pressure"]["single_snapshot_metadata_source"][key] = value
            with self.subTest(), self.assertRaises(ValueError): r.actual_source_binding(bad)

    def test_no_guard_scope_sampler_or_freeze_claim_changes_allowed(self):
        for key in ("held_Native_path_guard_replaced", "original_default_reader_mutated",
            "extra_sampler_query_thread_or_process", "complete_source_reads_rates_or_deadlines_reduced",
            "PC_freeze_resolved"):
            bad = self.row(); bad["bootstrap_metadata"]["early_pressure"]["single_snapshot_metadata_source"][key] = True
            with self.subTest(), self.assertRaises(ValueError): r.actual_source_binding(bad)

    def test_full_prior_validator_is_called_before_actual_source_check(self):
        environment = {"events": []}
        exec("def full(q,row,listing,oldbody,fresh,ctx,flat=True):\n events.append('full')\n return {'whole_oracle':True},{}", environment)
        with patch.object(r.prior, "validate_candidate", environment["full"]):
            evidence, proof = r.validate_candidate(None, self.row(), None, None, None, None)
        self.assertEqual(environment["events"], ["full"])
        self.assertTrue(evidence["whole_oracle"])
        self.assertTrue(proof["actual_metadata_source_snapshot_usage_checked"])
        bad = self.row(); bad["bootstrap_metadata"]["early_pressure"] = {}
        with patch.object(r.prior, "validate_candidate", environment["full"]), self.assertRaises(KeyError):
            r.validate_candidate(None, bad, None, None, None, None)

    def test_real_prebody_root_still_rejected_before_capture(self):
        with self.assertRaises(ValueError): r.validate_candidate(None, FAILED_ROW, None, None, None, None)

    def test_prepare_keeps_original_AST_except_canonical_root_metadata(self):
        raw = b"def prepare(q, root_pin):\n step=r.CONFIG\n require(root_pin['path']==f'implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run001.v1.json','ROOT')\n return 'whole-oracle'\n"
        self.assertTrue(callable(r.prepare_projection(raw)))
        with self.assertRaises(ValueError): r.prepare_projection(raw.replace(b"run001", b"run002"))


    def test_ancestor_normal_directory_and_file_one_fresh_query_per_visit(self):
        for mode, attrs in ((stat.S_IFDIR, 16), (stat.S_IFREG, 32)):
            counts = r.AncestorCounters(); calls = []
            def query(member, *, follow_symlinks):
                calls.append(follow_symlinks)
                return NS(st_mode=mode, st_file_attributes=attrs, st_reparse_tag=0)
            member = NS(is_symlink=lambda: self.fail("NO_REDUNDANT_LINK_QUERY"),
                is_junction=lambda: self.fail("NO_REDUNDANT_JUNCTION_QUERY"))
            self.assertTrue(r.ancestor_link_free(member, counts, query=query))
            self.assertEqual(calls, [False])
            self.assertEqual(counts.summary()["fresh_stat_attempts"], 1)

    def test_ancestor_reparse_missing_error_invalid_fields_exact_original_fallback(self):
        values = (NS(st_mode=stat.S_IFDIR, st_file_attributes=0x410, st_reparse_tag=0xa0000003),
            NS(st_mode=stat.S_IFREG, st_file_attributes=0x400, st_reparse_tag=0xa000000c),
            NS(st_mode=stat.S_IFREG, st_file_attributes=True, st_reparse_tag=0),
            NS(st_mode=stat.S_IFREG), PermissionError())
        for value in values:
            for symlink, junction in ((False, False), (True, False), (False, True)):
                counts = r.AncestorCounters(); calls = []
                def query(member, *, follow_symlinks):
                    if isinstance(value, Exception): raise value
                    return value
                member = NS(is_symlink=lambda: calls.append("symlink") or symlink,
                    is_junction=lambda: calls.append("junction") or junction)
                self.assertEqual(r.ancestor_link_free(member, counts, query=query), not symlink and not junction)
                self.assertEqual(calls, ["symlink"] if symlink else ["symlink", "junction"])
                self.assertEqual(counts.fallbacks, 1)

    def test_ancestor_same_member_twice_fresh_queries_and_no_hidden_snapshot_cache(self):
        counts = r.AncestorCounters(); calls = []
        member = NS(is_symlink=lambda: False, is_junction=lambda: True)
        def query(member, *, follow_symlinks):
            calls.append(member)
            return NS(st_mode=stat.S_IFDIR, st_file_attributes=16 if len(calls)==1 else 0x410,
                st_reparse_tag=0 if len(calls)==1 else 0xa0000003)
        self.assertTrue(r.ancestor_link_free(member, counts, query=query))
        self.assertFalse(r.ancestor_link_free(member, counts, query=query))
        self.assertEqual((counts.visits, counts.normal, counts.fallbacks), (2, 1, 1))

    def test_ancestor_projection_keeps_every_parent_root_and_final_file_check(self):
        events = []
        def predicate(member, counts):
            events.append(member); return True
        env = dict(r.base.stable.stable.prior.build.direct_path.__globals__)
        project, proof = r.ancestor_projection(BUILD_BYTES, env, r.AncestorCounters(), predicate=predicate)
        path = r.c.ROOT/"tools/p09/example.py"
        with patch.object(Path, "is_file", return_value=True) as checked:
            project(path, file_required=True)
        wanted = []
        for member in (path, *path.parents):
            wanted.append(member)
            if member == r.c.ROOT: break
        self.assertEqual(events, wanted)
        self.assertEqual(checked.call_count, 1)
        self.assertTrue(proof["original_direct_path_AST_restored_exactly"])
        events.clear()
        with self.assertRaises(ValueError): project(r.c.ROOT.parent/"outside")
        self.assertEqual(events, [])
        with patch.object(Path, "is_file", return_value=False), self.assertRaisesRegex(ValueError, "OUTPUT_MISSING"):
            project(path, file_required=True)
        with self.assertRaises(ValueError):
            r.ancestor_projection(BUILD_BYTES+b"\\n", env, r.AncestorCounters())

    def test_new_DATA_preserves_old_code_DATA_and_failed_preflight_exactly(self):
        for key, value in (("prior_source_data_pin", None), ("prior_source_data_pin", pin("wrong")),
            ("prior_source_code_pins", []), ("failed_preflight_pin", None)):
            bad = copy.deepcopy(self.data); bad[key] = value
            with self.subTest(), self.assertRaises(ValueError): r.validate_data(bad, self.step)

    def test_actual_ancestor_usage_no_import_only_missing_queries_or_cache_claim(self):
        for key, value in (("member_visits", 0), ("fresh_stat_attempts", 1), ("ordinary_snapshot_decisions", 0),
            ("original_fallbacks", 1), ("member_visits", True), ("snapshot_cached_between_member_visits", True),
            ("original_all_ancestors_and_file_required_check_retained", False)):
            bad = self.row()
            bad["bootstrap_metadata"]["early_pressure"]["single_snapshot_ancestor_source"][key] = value
            with self.subTest(), self.assertRaises(ValueError): r.actual_source_binding(bad)


if __name__ == "__main__": unittest.main()

