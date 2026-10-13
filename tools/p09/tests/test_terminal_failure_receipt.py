"""작은 synthetic STOP으로 종료 실패 writer 계약만 검증. 제품 실행 없음."""
import copy
import io
import json
import unittest
from unittest.mock import patch
import terminal_failure_receipt as m


def fixture():
    doc = dict(state='STOPPED_NOT_ACCEPTED', stop_reason=m.STOP, resource_stop_reason=m.STOP,
        cleanup_confirmed=True, owned_tree_empty=True, job_final=dict(active_processes=0, owned_processes=[]),
        product_complete=False, full249_current_qualified=False, signed16_current_qualified=False,
        whole1470_current_fresh_qualified=False, PC_freeze_resolved=False,
        P09_gate='OPEN', A12_gate='OPEN', A13_gate='OPEN',
        tests_passed=1, terminal_summary=dict(passed=1), full_values=['원문', {'nested': [1, None]}])
    life = dict(owner_done=True, owner_cleanup_confirmed=True, frame_state='CLOSED',
        input_lock_cleanup_confirmed=True, original_stop_reason=m.STOP,
        input_lock_handles_remaining=0, duplicate_handles_remaining=0, active_byte_streams=0)
    return doc, life


class TerminalFailure(unittest.TestCase):
    def reject_doc(self, key, value):
        doc, life = fixture(); doc[key] = value
        with self.assertRaises(ValueError): m.dump(doc, io.StringIO(), lifecycle=life)

    def reject_life(self, key, value):
        doc, life = fixture(); life[key] = value
        with self.assertRaises(ValueError): m.dump(doc, io.StringIO(), lifecycle=life)

    def test_complete_values_and_original_unchanged(self):
        doc, life = fixture(); old = copy.deepcopy(doc); out = io.StringIO()
        result = m.dump(doc, out, lifecycle=life)
        self.assertEqual(json.loads(out.getvalue()), old); self.assertEqual(doc, old)
        self.assertFalse(result['runtime_accepted']); self.assertFalse(result['gzip_used'])

    def test_pass_denied(self): self.reject_doc('state', 'PASS_SCOPED_NOT_GATE')
    def test_missing_reason_denied(self): self.reject_doc('stop_reason', None)
    def test_wrong_resource_reason_denied(self): self.reject_doc('resource_stop_reason', 'OTHER')
    def test_parent_cleanup_denied(self): self.reject_doc('cleanup_confirmed', False)
    def test_parent_tree_denied(self): self.reject_doc('owned_tree_empty', False)
    def test_live_job_denied(self): self.reject_doc('job_final', dict(active_processes=1, owned_processes=[]))
    def test_boolean_job_zero_denied(self): self.reject_doc('job_final', dict(active_processes=False, owned_processes=[]))
    def test_gate_and_product_denied(self):
        for key, value in [('P09_gate', 'PASS'), ('product_complete', True)]: self.reject_doc(key, value)
    def test_owner_not_done_denied(self): self.reject_life('owner_done', False)
    def test_frame_not_closed_denied(self): self.reject_life('frame_state', 'BROKEN')
    def test_boolean_handle_zero_denied(self): self.reject_life('duplicate_handles_remaining', False)
    def test_max_bytes_no_retry(self):
        doc, life = fixture()
        with patch.object(m, 'MAX_BYTES', 10), self.assertRaises(ValueError):
            m.dump(doc, io.StringIO(), lifecycle=life)
    def test_short_write_no_retry(self):
        class Short:
            calls = 0
            def write(self, block): self.calls += 1; return len(block)-1
        doc, life = fixture(); stream = Short()
        with self.assertRaises(ValueError): m.dump(doc, stream, lifecycle=life)
        self.assertEqual(stream.calls, 1)
    def test_mutation_during_write_denied(self):
        doc, life = fixture()
        class Mutating:
            def write(self, block): doc['state']='PASS_SCOPED_NOT_GATE'; return len(block)
        with self.assertRaises(ValueError): m.dump(doc, Mutating(), lifecycle=life)
    def test_large_token_bounded(self):
        doc, life = fixture(); doc['large']='가' * 20000
        class Capture(io.StringIO):
            largest=0
            def write(self, block): self.largest=max(self.largest,len(block)); return super().write(block)
        out=Capture(); m.dump(doc,out,lifecycle=life)
        self.assertEqual(json.loads(out.getvalue()),doc); self.assertLessEqual(out.largest,32768)


if __name__ == '__main__': unittest.main()
