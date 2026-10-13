import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review_p340_post_product_stop as p


def fixture():
    source = [dict(path=f"src/{i}.rs", bytes=10, sha256="a" * 64) for i in range(1658)]
    diagnostic = dict(read_passes=1658, bytes_read=16580,
                      original_owned_read_operations_preserved=True,
                      read_rates_by_kind=dict(binary=1048576, other=2097152))
    partial = dict(diagnostic, read_passes=727, bytes_read=7270)
    frame = dict(frame_state="CLOSED", registered_live_frame=False, input_count=1658,
                 input_bytes=16580, actual_byte_boundaries=[dict(role="before",
                 actual_byte_pins=source, reader_diagnostics=diagnostic)])
    flags = dict(P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN",
                 product_complete=False, PC_freeze_resolved=False)
    root = dict(schema_version="hwpx-agent.p09-preserved106-fixed-runtime-queue/v24",
                state="FAILED_NOT_ACCEPTED", error_code=p.STOP, resource_stop_reason=p.STOP,
                selected_test_index=111, source_attempted=True, source_qualified=False,
                binding={"fixture": "p340"},
                actual_product_child_executed=False, source_frame=None,
                case_receipt_path=p.CASE_RECEIPT,
                terminal_parent_failure_sidecar_pin=dict(path=p.SIDECAR_RECEIPT, bytes=1, sha256="b" * 64),
                terminal_source_frame=frame, **flags)
    body = dict(schema_version="hwpx-agent.p09-locked-r07-parent-candidate/v1",
                state="STOPPED_NOT_ACCEPTED", operation_phase="final_source_freeze",
                resource_stop_reason=p.STOP, stop_reason=p.STOP, actual_product_child_executed=True,
                exit_code=0, selected_test_names=[p.TEST_NAME], passed_test_names=[p.TEST_NAME],
                terminal_summary=dict(passed=1, failed=0, ignored=0, measured=0, filtered_out=248),
                test_arguments=[p.TEST_NAME, "--exact", "--test-threads=1",
                                "--format=pretty", "--color=never"],
                binding={"fixture": "p340"}, task="p204-r07-case-111-tests",
                minimal_worker_task="p204-r07-case-111-tests",
                minimal_owned_worker_path="tools/p09/minimal_r07_worker.py",
                capture=dict(error_code=None, per_stream_limit_bytes=32768,
                             complete_streams=True, raw_logs_saved=False),
                writer_authorized=True, owned_limits_verified=True,
                actual_job_membership_checked=True,
                owned_limits_readback=dict(verified=True, cpu_hard_cap_machine_percent=6.25,
                    affinity_mask=1, priority_class=16384, active_process_limit=16,
                    kill_on_close=True, breakaway_disabled=True),
                job_final=dict(active_processes=0, owned_processes=[]),
                cleanup_confirmed=True, owned_tree_empty=True, worker_created=True, job_assigned=True,
                source_freeze=source, owned_source_reader_passes=[diagnostic, partial], **flags)
    return root, body


class ReviewTests(unittest.TestCase):
    def setUp(self): self.root, self.body = fixture()
    def reject(self):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            p.validate(self.root, self.body)
    def test_distinguishes_child_pass_from_outer_stop_without_acceptance(self):
        result = p.validate(self.root, self.body,
                            dict(path=p.SIDECAR_RECEIPT, bytes=1, sha256="b" * 64))
        self.assertTrue(result["embedded_parent_actual_product_child_executed"])
        self.assertFalse(result["outer_frame_product_child_flag"])
        self.assertFalse(result["runtime_accepted"])
    def test_partial_final_reader_required(self):
        self.body["owned_source_reader_passes"][1]["read_passes"] = 1658; self.reject()
    def test_wrong_child_result_rejected(self):
        self.body["exit_code"] = 1; self.reject()
    def test_gate_promotion_rejected(self):
        self.root["P09_gate"] = "PASS"; self.reject()
    def test_source_pin_set_mismatch_rejected(self):
        self.root["terminal_source_frame"]["actual_byte_boundaries"][0]["actual_byte_pins"].pop(); self.reject()
    def test_owned_tree_must_be_empty(self):
        self.body["owned_tree_empty"] = False; self.reject()
    def test_semantic_test_arguments_are_bound_to_the_named_child(self):
        self.body["test_arguments"][0] = "some-other-test"; self.reject()
    def test_semantic_job_limits_are_verified(self):
        self.body["owned_limits_readback"]["kill_on_close"] = False; self.reject()
    def test_sidecar_receipt_pin_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            p.validate(self.root, self.body,
                       dict(path=p.SIDECAR_RECEIPT, bytes=1, sha256="c" * 64))


if __name__ == "__main__": unittest.main()
