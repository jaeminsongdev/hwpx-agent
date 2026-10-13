"""재사용 문서 전이: 이전 Gate/원문/STOP/IO 경계 강제."""
import unittest
import sync_current_queue_document_delta as m
import test_current_queue_documents as old

def fixture():
    row=old.fixture()
    row.update(schema_version='hwpx-agent.p09-current-queue-document-delta/v1',
        state=m.prior_driver.PASS,document_revision=94,current_queue_runtime_contract_tests_passed=156,
        document_contract_tests_passed=16)
    row['runtime_plan'].update(runtime_source_qualified_individual_cases=56,next_runtime_index=63,
        runtime_successful_candidates_requiring_closing=0)
    return row

class Transition(unittest.TestCase):
    def test_valid(self):self.assertEqual(len(m.previous(fixture(),95)),2)
    def deny(self,key,value):
        row=fixture();row[key]=value
        with self.assertRaises(ValueError):m.previous(row,95)
    def test_failed(self):self.deny('state','FAILED_NOT_ACCEPTED')
    def test_revision(self):self.deny('document_revision',93)
    def test_stop(self):self.deny('resource_stop_reason','STOP_SUSTAINED_SYSTEM_CPU')
    def test_old_bytes(self):self.deny('exact_prior_document_bytes_preserved',False)
    def test_gate(self):self.deny('P09_gate','PASS')
    def test_partial_IO(self):
        row=fixture();row['IO']['final_fresh_hashes']=0
        with self.assertRaises(ValueError):m.previous(row,95)
    def test_next_revision(self):
        row=fixture();row.update(schema_version='hwpx-agent.p09-current-queue-reusable-document-delta/v1',
            state=m.PASS,document_revision=95,document_contract_tests_passed=24)
        self.assertEqual(len(m.previous(row,96)),2)
        row['document_contract_tests_passed']=16
        with self.assertRaises(ValueError):m.previous(row,96)

if __name__=='__main__':unittest.main()
