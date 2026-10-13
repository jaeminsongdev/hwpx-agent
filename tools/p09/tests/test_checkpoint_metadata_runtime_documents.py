import unittest
import sync_checkpoint_metadata_runtime_documents as m


class CheckpointMetadataDocTests(unittest.TestCase):
    def setUp(self):
        self.plan=dict(runtime_source_qualified_individual_cases=77,runtime_remaining_individual_cases=172,
            runtime_remaining_regular_cases=166,runtime_remaining_corpus_cases=6,
            runtime_successful_candidates_requiring_closing=0,next_runtime_index=84,
            all_successful_bodies_pending_whole_reconciliation=74)
        self.before=b'old exact\r\n';self.revision=103
        self.words='> P255~P256 runtime-r103 '+' '.join(m.words(self.plan))+'\n\n'
        self.after=self.words.encode('utf-8')+self.before
    def reject(self):
        with self.assertRaises(ValueError):m.prefix(self.before,self.after,self.plan,self.revision)
    def test_exact_prefix_suffix(self):self.assertEqual(m.prefix(self.before,self.after,self.plan,self.revision),self.words)
    def test_old_bytes_normalization(self):self.after=self.after.replace(b'\r\n',b'\n');self.reject()
    def test_no_prefix(self):self.after=self.before;self.reject()
    def test_wrong_runtime_count(self):self.after=self.after.replace(b'77/249',b'78/249');self.reject()
    def test_wrong_next(self):self.after=self.after.replace(b'index84',b'index85');self.reject()
    def test_gate_open_required(self):self.after=self.after.replace('P09·A12·A13 OPEN'.encode(),b'GATE PASS');self.reject()
    def test_preGO_not_promoted(self):self.after=self.after.replace('P239 실제 pre-GO CPU STOP 경계 NOT_RUN'.encode(),b'PASS');self.reject()
    def test_CPU_retry_prohibition(self):self.after=self.after.replace('CPU 보호 중단 시 자동 재시도 금지'.encode(),b'');self.reject()
    def test_original_failure_preserved(self):self.after=self.after.replace('원 STOP/FAILED 보존'.encode(),b'');self.reject()
    def test_original_limits_not_extended(self):self.after=self.after.replace('원600초·CPU/RAM 기준은 변경하지 않음'.encode(),b'');self.reject()
    def test_wrong_revision(self):self.revision=104;self.reject()
    def test_plan_values_are_dynamic_not_fixed77(self):
        self.plan.update(runtime_source_qualified_individual_cases=78,runtime_remaining_individual_cases=171,
            runtime_remaining_regular_cases=165,next_runtime_index=85,all_successful_bodies_pending_whole_reconciliation=75)
        words='> P255~P256 runtime-r104 '+' '.join(m.words(self.plan))+'\n\n'
        self.assertEqual(m.prefix(self.before,words.encode()+self.before,self.plan,104),words)
    def test_projection_preserves720_and_two_reads(self):
        d=m.next_read_projection(252);self.assertEqual(d['projected_next_shared_reads'],258)
        self.assertEqual(d['unchanged_shared_read_limit'],720);self.assertTrue(d['next_fits_current_controller'])
    def test_projection_does_not_hide_excess(self):
        self.assertFalse(m.next_read_projection(718)['next_fits_current_controller'])
        with self.assertRaises(ValueError):m.next_read_projection(719)
