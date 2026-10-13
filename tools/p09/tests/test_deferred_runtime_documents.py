"""전 STOP notice를 새 실제 수용으로 승격하지 않는 문서 전이 계약."""
import unittest
import sync_deferred_runtime_documents as m


def fixture():
    return dict(schema_version='hwpx-agent.p09-packed-stop-document-notice/v1',
        state='PASS_PACKED_STOP_DOCUMENT_NOTICE_NOT_RUNTIME_RESUME_OR_GATE',document_revision=92,
        error_code=None,resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,
        IO=dict(finished=True,bound_inputs=22,final_fresh_hashes=22),runtime_resume_authorized=False,
        failure_writer_actual_connection=False,original_stop_preserved=True,
        runtime_plan=dict(runtime_source_qualified_individual_cases=53),
        bound_input_pins=[dict(path=name,bytes=1,sha256='0'*64) for name in m.documents.ROOT_DOCS])


class Transition(unittest.TestCase):
    def test_valid_stop_notice(self):self.assertEqual(len(m.previous(fixture())),2)
    def test_unknown_old_state_denied(self):
        row=fixture();row['state']='FAILED_NOT_ACCEPTED'
        with self.assertRaises(ValueError):m.previous(row)
    def test_old_resume_not_assumed(self):
        row=fixture();row['runtime_resume_authorized']=True
        with self.assertRaises(ValueError):m.previous(row)
    def test_old_STOP_not_preserved_denied(self):
        row=fixture();row['original_stop_preserved']=False
        with self.assertRaises(ValueError):m.previous(row)


if __name__=='__main__':unittest.main()
