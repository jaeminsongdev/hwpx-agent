"""r93 수용/OPEN/STOP 보존과 r94 원문 증분 전이 계약."""
import unittest
import sync_current_queue_documents as m

def fixture():
    row=dict(schema_version='hwpx-agent.p09-deferred-runtime-document-delta/v1',
        state='PASS_DEFERRED_RUNTIME_DOCUMENT_DELTA_NOT_WHOLE_OR_GATE',document_revision=93,
        error_code=None,resource_stop_reason=None,resource_watcher_cleanup_confirmed=True,
        IO=dict(finished=True,bound_inputs=167,final_fresh_hashes=167),
        deferred_runtime_contract_tests_passed=144,document_contract_tests_passed=12,
        new_product_or_full_source_frame_executed=False,exact_prior_document_bytes_preserved=True,
        original_STOP_and_zero_body_preserved=True,
        runtime_plan=dict(runtime_source_qualified_individual_cases=54,next_runtime_index=61),
        bound_input_pins=[dict(path=name,bytes=1,sha256='0'*64) for name in m.documents.ROOT_DOCS])
    row.update({key:'OPEN' for key in ('P09_gate','A12_gate','A13_gate')})
    row.update({key:False for key in ('product_complete','PC_freeze_resolved',
        'whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
        'full249_current_qualified','signed16_current_qualified')})
    return row

class Transition(unittest.TestCase):
    def test_valid(self): self.assertEqual(len(m.previous(fixture())),2)
    def deny(self,key,value):
        row=fixture();row[key]=value
        with self.assertRaises(ValueError):m.previous(row)
    def test_failed(self):self.deny('state','FAILED_NOT_ACCEPTED')
    def test_revision(self):self.deny('document_revision',92)
    def test_old_bytes(self):self.deny('exact_prior_document_bytes_preserved',False)
    def test_STOP(self):self.deny('original_STOP_and_zero_body_preserved',False)
    def test_gate(self):self.deny('P09_gate','PASS')
    def test_product(self):self.deny('product_complete',True)
    def test_partial_IO(self):
        row=fixture();row['IO']['final_fresh_hashes']=166
        with self.assertRaises(ValueError):m.previous(row)

if __name__=='__main__':unittest.main()
