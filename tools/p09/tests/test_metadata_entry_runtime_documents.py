import unittest
import sync_metadata_entry_runtime_documents as m


class MetadataEntryDocTests(unittest.TestCase):
    def setUp(self):
        self.before=b'old exact\r\n'
        self.words='> 2026-10-09 P248~P251 runtime-r101 runtime 수용74/249 잔여175(일반169+corpus6) 미closing후보0 다음index81 whole재조정대기71 P09·A12·A13 OPEN 원 STOP/FAILED 보존 CPU 보호 중단 시 자동 재시도 금지 통과 본문 재실행 없음 PC 프리즈 원인·해결 미확정 P239 실제 pre-GO CPU STOP 경계 NOT_RUN 원600초·CPU/RAM 기준은 변경하지 않음\n\n'
        self.after=self.words.encode('utf-8')+self.before
    def reject(self):
        with self.assertRaises(ValueError):m.prefix(self.before,self.after)
    def test_exact_prefix_suffix(self):self.assertEqual(m.prefix(self.before,self.after),self.words)
    def test_old_bytes_normalization(self):self.after=self.after.replace(b'\r\n',b'\n');self.reject()
    def test_no_prefix(self):self.after=self.before;self.reject()
    def test_wrong_runtime_count(self):self.after=self.after.replace(b'74/249',b'75/249');self.reject()
    def test_wrong_next(self):self.after=self.after.replace(b'index81',b'index82');self.reject()
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
