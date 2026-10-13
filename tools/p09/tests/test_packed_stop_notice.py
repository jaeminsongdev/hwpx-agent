"""STOP notice가 지원 검증을 실제 재개/제품 완료로 승격하지 않는 계약."""
import unittest
import sync_packed_stop_notice as m


def fixture():
    return dict(state='PASS_BOUNDED_STOP_REVIEW_AND_FAILURE_WRITER_SUPPORT_NOT_RUNTIME_OR_GATE',
        error_code=None,resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,
        IO=dict(finished=True,bound_inputs=12,final_fresh_hashes=12),failure_writer_contract_tests_passed=16,
        peak_summary_contract_tests_passed=8,failure_writer_actual_connection=False,runtime_resume_authorized=False,
        original_failure_preserved=True,empty_body_semantic_or_job_result_established=False,
        product_body_reexecuted=False,runtime_plan=dict(runtime_source_qualified_individual_cases=53,
            runtime_remaining_individual_cases=196,next_runtime_index=60))


class Notice(unittest.TestCase):
    def reject(self,key,value):
        row=fixture();row[key]=value
        with self.assertRaises(ValueError):m.check_review(row)
    def test_support_only_valid(self):self.assertEqual(m.check_review(fixture())['next_runtime_index'],60)
    def test_actual_connection_denied(self):self.reject('failure_writer_actual_connection',True)
    def test_resume_denied(self):self.reject('runtime_resume_authorized',True)
    def test_failure_not_preserved_denied(self):self.reject('original_failure_preserved',False)
    def test_unclosed_review_denied(self):self.reject('resource_watcher_cleanup_confirmed',False)
    def test_wrong_progress_denied(self):
        self.reject('runtime_plan',dict(runtime_source_qualified_individual_cases=54,
            runtime_remaining_individual_cases=195,next_runtime_index=61))


if __name__=='__main__':unittest.main()
