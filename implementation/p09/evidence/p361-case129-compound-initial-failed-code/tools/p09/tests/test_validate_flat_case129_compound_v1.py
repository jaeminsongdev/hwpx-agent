"""Pure-contract fixtures only; synthetic PASS never represents actual source.

Actual failed129/source001/authority122 are injected by the guarded qualifier.
An immutable actual128 Native frame provides the original full-oracle shape.
The explicitly synthetic positive fixture is NEVER saved or accepted as runtime.
Negative mutations copy only the edited branches, not complete pin/resource trees.
"""
import ast
import copy
import json
import unittest
from unittest.mock import patch
from pathlib import Path

import validate_flat_case129_compound_v1 as subject

ORIGINAL = STOP_SOURCE = STOP_PIN = AUTHORITY = LISTING = QUALIFICATION = NATIVE128 = None
CHECKPOINT = lambda: None
CODE_TEXT = None
FIXTURE = None


def branch_copy(root, path, value):
    """Structural test projection: unchanged large branches remain shared/read-only."""
    CHECKPOINT()
    if not path:
        return value
    head, *tail = path
    clone = dict(root) if type(root) is dict else list(root)
    clone[head] = branch_copy(root[head], tail, value)
    return clone


def synthetic_fixture():
    """Explicit synthetic schema fixture, not actual Native evidence."""
    s = subject.source
    row = dict(STOP_SOURCE)
    required = s.scope.pins(row["required_source_pins"])
    n = len(required); total = sum(p["bytes"] for p in required.values())
    dirs = len({p.as_posix() for name in required for p in Path(name).parents})
    held = n + dirs; binary = sum(p["bytes"] for name, p in required.items()
        if name.lower().endswith(".exe"))
    frame = copy.deepcopy(NATIVE128["source_frame"])
    frame.update(input_count=n, input_bytes=total)
    frame["held_identity_after_owned_cleanup"].update(regular_file_count=n, directory_count=dirs)
    for bound in frame["actual_byte_boundaries"]:
        bound["actual_byte_pins"] = list(required.values())
        diag = bound["reader_diagnostics"]
        diag.update(read_passes=n, bytes_read=total,
            bytes_read_by_kind=dict(binary=binary, other=total-binary))
        diag["reusable_chunk_workspace"].update(leases=n, lease_returns=n, returned_bytes=total,
            readinto_attempts=n, readinto_completed=n)
    h = frame["handles"]
    h.update(input_lock_handles_opened=held, input_lock_handles_closed=held,
        handle_metadata_checks=2*held+2*n, byte_stream_identity_checks=2*n)
    h["borrowed_byte_streams"].update(duplicate_handles_opened=n, duplicate_handles_closed=n,
        shared_offset_resets=2*n, new_duplicate_open_reservations=n,
        reused_stream_pressure_checkpoints=n, logical_read_leases=2*n, logical_read_lease_returns=2*n)
    h["native_open_pacing"].update(open_reservations=held+n)
    h["acquisition_phase_pressure"].update(acquisition_reservations=held)
    h["acquisition_source_warning_fail_fast"].update(checks=held)
    guards = copy.deepcopy(NATIVE128["source_path_guard_diagnostics"])
    for guard in guards:
        guard.update(native_metadata_queries_attempted=n, fresh_held_metadata_queries=n,
            original_path_guard_predicates=3*n)
    samples = NATIVE128["samples"]
    row.update(state=s.PASS, source_frame=frame, source_path_guard_diagnostics=guards,
        independent_source_frame_qualified=True, elapsed_seconds=550.0,
        Rust_inventory_observations=NATIVE128["current_Rust_inventory_observations"],
        resource_samples=samples, CPU_max=max(x["system_cpu_percent"] for x in samples),
        RAM_min=min(x["available_ram_percent"] for x in samples))
    row.pop("error_code", None)
    row["validation"] = s.validate_frame(frame, required, guards, CHECKPOINT)
    return row


class CompoundContracts(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()

    def candidate(self, row=None, **overrides):
        args = dict(original=ORIGINAL, original_pin=subject.source.STOP_PIN,
            source_doc=FIXTURE if row is None else row, source_pin=STOP_PIN,
            authority=AUTHORITY, authority_pin=subject.source.AUTHORITY_PIN,
            listing=LISTING, qualification=QUALIFICATION, qualification_pin=subject.QUAL_PIN,
            checkpoint=CHECKPOINT)
        args.update(overrides)
        return subject.validate(**args)

    def test_explicit_synthetic_positive_only_document_contract_no_queue_claim(self):
        result = self.candidate()
        self.assertEqual(result["state"], subject.PASS)
        self.assertEqual(result["accepted_count_delta"], 0)
        self.assertFalse(result["independent_compound_acceptance_qualified"])
        self.assertFalse(result["current_receipt_bytes_rebound_by_this_contract"])
        self.assertFalse(result["live_authoritative_queue_scanned_by_this_contract"])
        self.assertFalse(result["successful_product_body_replayed"])

    def test_actual_failed_source_refused_before_checkpoint_or_large_oracle(self):
        def forbidden():
            raise AssertionError("FAILED_SOURCE_MUST_NOT_TRAVERSE")
        with patch.object(subject.source, "validate_frame", side_effect=forbidden):
            with self.assertRaisesRegex(ValueError, "COMPOUND_SOURCE_HEADER"):
                self.candidate(STOP_SOURCE, checkpoint=forbidden)

    def test_actual_stop_bounded_review_all_handles_and_all_resource_samples(self):
        result = subject.review_acquisition_stop(STOP_SOURCE, STOP_PIN, CHECKPOINT)
        self.assertEqual(result["opened_and_closed_handles"], 1386)
        self.assertEqual(result["resource_sample_count"], 236)
        self.assertEqual(result["peak_resource_sample"]["system_cpu_percent"], 91.67)
        self.assertEqual(result["peak_resource_sample"]["parent_cpu_machine_percent"], 0.0)
        self.assertFalse(result["independent_source_frame_qualified"])
        self.assertFalse(result["causal_trigger_or_CPU_freeze_fix_established"])

    def test_source_stop_closed_output_does_not_serialize_unknown_payload(self):
        opaque = "UNTRUSTED_" + "x"*10000
        row = branch_copy(STOP_SOURCE, ["resource_samples"], [
            dict(x, unknown_payload=opaque) for x in STOP_SOURCE["resource_samples"]])
        result = subject.review_acquisition_stop(row, STOP_PIN, CHECKPOINT)
        encoded = json.dumps(result)
        self.assertLessEqual(len(encoded.encode("utf-8")), 4096)
        self.assertNotIn("UNTRUSTED", encoded)

    def test_compact_review_invalid_middle_sample_is_not_hidden_by_tail(self):
        row = branch_copy(STOP_SOURCE, ["resource_samples", 100, "available_ram_percent"], float("nan"))
        with self.assertRaisesRegex(ValueError, "ALL_RESOURCE_VALUES"):
            subject.review_acquisition_stop(row, STOP_PIN, CHECKPOINT)

    def test_compact_review_does_not_print_command_string_in_numeric_field(self):
        row = branch_copy(STOP_SOURCE, ["resource_samples", 100, "parent_private_mib"], "UNTRUSTED_COMMAND")
        with self.assertRaisesRegex(ValueError, "CLOSED_NUMERIC_RESOURCE_FIELDS"):
            subject.review_acquisition_stop(row, STOP_PIN, CHECKPOINT)

    def test_contract_has_no_io_subprocess_native_or_mutation_runner(self):
        tree = ast.parse(CODE_TEXT)
        forbidden = {"open", "write", "read", "write_text", "write_bytes", "Popen",
            "run", "start", "startfile", "load", "commit", "acquire", "close", "sleep"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else None)
                self.assertNotIn(name, forbidden)

    def test_original_resource_guard_stop_is_not_accepted(self):
        bad = branch_copy(FIXTURE, ["resource_samples", 0, "available_ram_percent"], 0.0)
        with self.assertRaisesRegex(ValueError, "ORIGINAL_RESOURCE_STOP"):
            self.candidate(bad)

    def test_authority_bool_is_not_count122(self):
        bad = branch_copy(AUTHORITY, ["accepted_count_after"], True)
        with self.assertRaises(ValueError):
            self.candidate(authority=bad)

    def test_input_scope_original_pin_cannot_be_rebased(self):
        bad = branch_copy(FIXTURE, ["required_source_pins", 0, "sha256"], "a"*64)
        with self.assertRaisesRegex(ValueError, "EVERY_ORIGINAL_INPUT_RETAINED"):
            self.candidate(bad)

    def test_source_qualification_must_be_all_four_exact_controllers(self):
        bad = branch_copy(QUALIFICATION, ["source_controller_pins"], QUALIFICATION["source_controller_pins"][:-1])
        with self.assertRaises(ValueError):
            self.candidate(qualification=bad)

    def test_positive_validation_does_not_mutate_shared_original_frame_or_sample(self):
        before = (ORIGINAL["state"], STOP_SOURCE["state"],
            FIXTURE["source_frame"]["frame_state"], FIXTURE["resource_samples"][0]["available_ram_percent"])
        self.candidate()
        self.assertEqual(before, (ORIGINAL["state"], STOP_SOURCE["state"],
            FIXTURE["source_frame"]["frame_state"], FIXTURE["resource_samples"][0]["available_ram_percent"]))


def reject(name, path, value):
    def test(self):
        bad = branch_copy(FIXTURE, path, value)
        try:
            self.candidate(bad)
        except ValueError as exc:
            code = str(exc)
            if "STOP_" in code or "TIMEOUT" in code:
                raise
            self.assertTrue(code.startswith(("PRESERVED129_COMPOUND_", "CURRENT_EPOCH_ACCEPT_",
                "PRESERVED129_SOURCE_", "CURRENT_STORED_RUNTIME_SCOPE_")))
        else:
            self.fail("MALFORMED_COMPOUND_NOT_REJECTED")
    test.__name__ = "test_reject_" + name
    setattr(CompoundContracts, test.__name__, test)


reject("original_failed_root_promotion", ["original_failed_root_accepted"], True)
reject("child_replay", ["original_product_body_replayed"], True)
reject("source_queue_change", ["accepted_count_delta"], 1)
reject("partial_after", ["source_frame", "actual_byte_boundaries"], [])
reject("unclean_handle", ["source_frame", "handles", "input_lock_handles_remaining"], 1)
reject("wrong_byte_rate", ["source_frame", "actual_byte_boundaries", 1,
    "reader_diagnostics", "read_rates_by_kind", "binary"], 99999999)
reject("extended_deadline", ["elapsed_seconds"], 600.001)
reject("wrong_budget", ["source_budget", "unallocated_margin_seconds"], 0)
reject("new_runtime_claim", ["independent_compound_acceptance_qualified"], True)
reject("fake_cpu_peak", ["CPU_max"], 0.0)
reject("missing_import", ["imported_controller_paths"], ["tools/p09/not-qualified.py"])
reject("missing_rust_final", ["Rust_inventory_observations"], [])
reject("body_review_rebase", ["completed_child_review", "prior_accepted_count"], 123)
reject("gates_closed", ["P09_gate"], "PASS")
