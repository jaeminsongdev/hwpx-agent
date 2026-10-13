"""원16계약 외 시작 전 STOP의 정확한 상태·미실행·Job 유무 계약."""
import io
import json
import unittest
import terminal_failure_receipt_r2 as m
from test_terminal_failure_receipt import fixture


def deferred():
    row,life=fixture();row.update(state='DEFERRED_NOT_STARTED',heavy_work_started=False,
        actual_product_child_executed=False,worker_created=False,job_assigned=False,writer_authorized=False)
    row.pop('job_final');return row,life


class BeforeGo(unittest.TestCase):
    def test_absent_job_preserves_no_job(self):
        row,life=deferred();out=io.StringIO();m.dump(row,out,lifecycle=life)
        saved=json.loads(out.getvalue());self.assertEqual(saved,row);self.assertNotIn('job_final',saved)
    def test_already_assigned_empty_job_deferred(self):
        row,life=deferred();row.update(worker_created=True,job_assigned=True,
            job_final=dict(active_processes=0,owned_processes=[]))
        out=io.StringIO();m.dump(row,out,lifecycle=life);self.assertEqual(json.loads(out.getvalue()),row)
    def test_absent_job_after_worker_setup_denied(self):
        row,life=deferred();row['worker_created']=True
        with self.assertRaises(ValueError):m.dump(row,io.StringIO(),lifecycle=life)
    def test_deferred_execution_contradiction_denied(self):
        for key in ('heavy_work_started','actual_product_child_executed'):
            row,life=deferred();row[key]=True
            with self.assertRaises(ValueError):m.dump(row,io.StringIO(),lifecycle=life)
    def test_stopped_missing_job_is_unknown_not_empty(self):
        row,life=fixture();row.pop('job_final')
        with self.assertRaises(ValueError):m.dump(row,io.StringIO(),lifecycle=life)
    def test_missing_deferred_flag_denied(self):
        row,life=deferred();row.pop('heavy_work_started')
        with self.assertRaises(ValueError):m.dump(row,io.StringIO(),lifecycle=life)


if __name__=='__main__':unittest.main()
