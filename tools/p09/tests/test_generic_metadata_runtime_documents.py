import unittest
import sync_generic_metadata_runtime_documents as m


class GenericMetadataDocTests(unittest.TestCase):
    def setUp(self):
        self.before=b'old exact\r\n'
        self.words='> 2026-10-09 P252~P254 runtime-r102 '+' '.join(m.WORDS)+'\n\n'
        self.after=self.words.encode('utf-8')+self.before
    def reject(self):
        with self.assertRaises(ValueError):m.prefix(self.before,self.after)
    def test_exact_prefix_suffix(self):self.assertEqual(m.prefix(self.before,self.after),self.words)
    def test_old_bytes_normalization(self):self.after=self.after.replace(b'\r\n',b'\n');self.reject()
    def test_no_prefix(self):self.after=self.before;self.reject()
    def test_wrong_runtime_count(self):self.after=self.after.replace(b'75/249',b'76/249');self.reject()
    def test_wrong_next(self):self.after=self.after.replace(b'index82',b'index83');self.reject()
    def test_gate_open_not_removed(self):
        self.after=self.after.replace('P09·A12·A13 OPEN'.encode(),b'GATE PASS');self.reject()
    def test_preGO_branch_not_promoted(self):
        self.after=self.after.replace('P239 실제 pre-GO CPU STOP 경계 NOT_RUN'.encode(),b'preGO PASS');self.reject()
    def test_CPU_retry_prohibition_not_removed(self):
        self.after=self.after.replace('CPU 보호 중단 시 자동 재시도 금지'.encode(),b'');self.reject()
    def test_original_failure_preserved(self):
        self.after=self.after.replace('원 STOP/FAILED 보존'.encode(),b'');self.reject()
    def test_original_resource_limits_not_extended(self):
        self.after=self.after.replace('원600초·CPU/RAM 기준은 변경하지 않음'.encode(),b'');self.reject()
    def test_next_not_run_not_promoted(self):self.after=self.after.replace(b'index82 NOT_RUN',b'index82 PASS');self.reject()
    def test_next_optimization_boundary_required(self):
        self.after=self.after.replace('중복 호출 검토·최적화 후 재개'.encode(),b'');self.reject()
    def test_projection_does_not_raise_cap_or_execute(self):
        d=m.next_read_projection(715)
        self.assertEqual(d['projected_actual82_shared_reads'],721)
        self.assertEqual(d['unchanged_shared_read_limit'],720)
        self.assertFalse(d['next_fits_current_controller']);self.assertFalse(d['actual82_executed'])
    def test_projection_requires_actual_measurement(self):
        with self.assertRaises(ValueError):m.next_read_projection(714)
