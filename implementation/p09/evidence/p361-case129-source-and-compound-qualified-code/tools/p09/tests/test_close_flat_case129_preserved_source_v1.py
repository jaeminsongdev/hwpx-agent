"""Native-source oracle/cleanup contracts, with immutable real128 frame injection."""
import ast
import copy
import unittest
import close_flat_case129_preserved_source_v1 as subject

FRAME = REQUIRED = PATH_GUARDS = CODE_TEXT = None
CHECKPOINT = lambda: None


class PreservedSourceContracts(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()
        self.assertIsInstance(FRAME,dict)
        self.assertIsInstance(REQUIRED,dict)

    def validate(self,frame):
        return subject.validate_frame(frame,REQUIRED,PATH_GUARDS,CHECKPOINT)

    def test_complete_original_frame_still_passes_all_native_predicates(self):
        result=self.validate(FRAME)
        self.assertTrue(result["two_complete_actual_byte_boundaries"])
        self.assertFalse(result["source_scope_or_rates_or_deadlines_reduced"])
        self.assertEqual(result["inputs"],len(REQUIRED))

    def test_scope_preserves_every_original_and_adds_disjoint_controller(self):
        extra=dict(path="tools/p09/test-new-preserved-source-controller.py",bytes=1,sha256="a"*64)
        result=subject.expected_scope(list(REQUIRED.values()),[extra])
        self.assertEqual(len(result),len(REQUIRED)+1)
        self.assertTrue(all(result[k]==v for k,v in REQUIRED.items()))

    def test_conflicting_source_is_not_silently_rebased(self):
        row=copy.deepcopy(next(iter(REQUIRED.values())))
        row["sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"CONFLICT_NOT_SILENT_REBASE"):
            subject.expected_scope(list(REQUIRED.values()),[row])

    def test_source_budget_keeps_all_original_rates_deadline_and_margins(self):
        model=subject.source_budget(REQUIRED)
        self.assertEqual(model["unchanged_lock_deadline_seconds"],600)
        self.assertEqual(model["unallocated_margin_seconds"],60)
        self.assertEqual(model["selected_acquisition_rate_per_second"],14)
        self.assertEqual(model["unchanged_byte_native_ceiling_per_second"],20)
        self.assertEqual(model["additional_serial_PDH_maximum_sample_budget_seconds"],2.05)
        self.assertEqual(model["final_postcleanup_distinct_sample_wait_allowance_seconds"],.5)
        self.assertFalse(model["byte_or_native_costs_assumed_overlapped"])
        self.assertLess(model["predicted_runtime_combined_seconds"],600)

    def test_producer_never_starts_a_product_subprocess(self):
        tree=ast.parse(CODE_TEXT)
        forbidden={"Popen","call","run_command","run_owned","worker","StartProcess","startfile"}
        for n in ast.walk(tree):
            if isinstance(n,ast.Call):
                name=n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else None
                self.assertNotIn(name,forbidden)

    def test_commit_uses_unchanged_original_stop_not_fabricated_owned_pass(self):
        tree=ast.parse(CODE_TEXT)
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and
            isinstance(n.func,ast.Attribute) and n.func.attr=="commit"]
        self.assertEqual(len(calls),1)
        self.assertEqual(ast.dump(calls[0].args[0]),"Name(id='original', ctx=Load())")

    def test_cleanup_still_reports_close_failure_and_does_not_retry(self):
        class F:
            calls=0
            def close(self):
                self.calls+=1
                raise ValueError("ORIGINAL_CLOSE_FAILURE")
            def summary(self):
                return {"remaining":1}
        f=F();summary,closed=subject.close_frame_once(f)
        self.assertEqual(summary,{"remaining":1});self.assertFalse(closed);self.assertEqual(f.calls,1)

    def test_cleanup_summary_failure_is_not_qualified(self):
        class F:
            def close(self):return True
            def summary(self):raise ValueError("NO_COMPLETE_SUMMARY")
        summary,closed=subject.close_frame_once(F())
        self.assertIsNone(summary);self.assertFalse(closed)

    def test_no_frame_does_not_fabricate_native_observation(self):
        self.assertEqual(subject.close_frame_once(None),(None,True))


def reject(name,change):
    def test(self):
        frame=copy.deepcopy(FRAME);change(frame);CHECKPOINT()
        try:
            self.validate(frame)
        except ValueError as exc:
            code=str(exc)
            if "STOP_" in code or "TIMEOUT" in code:
                raise
            self.assertTrue(code.startswith(("CURRENT_EPOCH_ACCEPT_","PRESERVED129_SOURCE_","CURRENT_STORED_RUNTIME_SCOPE_")))
        else:
            self.fail("MALFORMED_NATIVE_FRAME_NOT_REJECTED")
    test.__name__="test_reject_"+name
    setattr(PreservedSourceContracts,test.__name__,test)


reject("partial_after",lambda f:f["actual_byte_boundaries"].pop())
reject("wrong_whole_input",lambda f:f["actual_byte_boundaries"][1]["actual_byte_pins"].pop())
reject("wrong_byte_count",lambda f:f["actual_byte_boundaries"][1]["reader_diagnostics"].update(bytes_read=0))
reject("wrong_rate",lambda f:f["actual_byte_boundaries"][0]["reader_diagnostics"]["read_rates_by_kind"].update(binary=99999999))
reject("synthetic_workspace",lambda f:f["actual_byte_boundaries"][1]["reader_diagnostics"]["reusable_chunk_workspace"].update(workspace_used=False))
reject("incomplete_readinto",lambda f:f["actual_byte_boundaries"][1]["reader_diagnostics"]["reusable_chunk_workspace"].update(readinto_completed=0))
reject("unread_tail",lambda f:f["actual_byte_boundaries"][1]["reader_diagnostics"]["reusable_chunk_workspace"].update(unread_tail_exposed=True))
reject("hash_cache",lambda f:f["actual_byte_boundaries"][1]["reader_diagnostics"]["reusable_chunk_workspace"].update(file_bytes_or_hash_or_JSON_cache=True))
reject("remaining_handle",lambda f:f["handles"].update(input_lock_handles_remaining=1))
reject("extended_deadline",lambda f:f["handles"].update(maximum_lock_seconds=601))
reject("missing_identities",lambda f:f["handles"].update(byte_stream_identity_checks=0))
reject("active_borrow",lambda f:f["handles"]["borrowed_byte_streams"].update(active_borrow_binding=True))
reject("remaining_duplicate",lambda f:f["handles"]["borrowed_byte_streams"].update(duplicate_handles_remaining=1))
reject("second_path_open",lambda f:f["handles"]["borrowed_byte_streams"].update(byte_stream_pathname_reopens=1))
reject("missing_reuse_guard",lambda f:f["handles"]["borrowed_byte_streams"].update(reused_stream_pressure_checkpoints=0))
reject("raised_native_rate",lambda f:f["handles"]["native_open_pacing"].update(maximum_opens_per_second=21))
reject("raised_acquisition_rate",lambda f:f["handles"]["acquisition_phase_pressure"].update(acquisition_maximum_reservations_per_second=15))
reject("source_exclusion",lambda f:f.update(input_exclusions_added=True))
reject("saturation_restart",lambda f:f["handles"]["one_way_native_saturation_circuit_breaker"].update(saturation_seen=True))
reject("live_final_frame",lambda f:f.update(registered_live_frame=True))
