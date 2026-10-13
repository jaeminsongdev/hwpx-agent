import unittest
import sync_density_control_documents as m


class DensityDocTests(unittest.TestCase):
    def setUp(self):
        self.before=b'old exact\r\n'
        self.words='> 2026-10-09 P241~P247 runtime-r100 runtime 수용73/249 잔여176(일반170+corpus6) 미closing후보0 다음index80 whole재조정대기70 P09·A12·A13 OPEN 원 STOP/FAILED 보존 CPU 보호 중단 시 자동 재시도 금지 통과 본문 재실행 없음 PC 프리즈 원인·해결 미확정 Native20 전체 실제 검증 NOT_RUN metadata32 전체 실행기 연결 NOT_RUN P239 실제 pre-GO CPU STOP 경계 NOT_RUN 실패한 P241/P244 caller 재실행 금지\n\n'
        self.after=self.words.encode('utf-8')+self.before
    def reject(self):
        with self.assertRaises(ValueError):m.prefix(self.before,self.after)
    def test_exact_prefix_suffix(self):self.assertEqual(m.prefix(self.before,self.after),self.words)
    def test_old_bytes_normalization(self):self.after=self.after.replace(b'\r\n',b'\n');self.reject()
    def test_no_prefix(self):self.after=self.before;self.reject()
    def test_wrong_runtime_count(self):self.after=self.after.replace(b'73/249',b'74/249');self.reject()
    def test_wrong_next(self):self.after=self.after.replace(b'index80',b'index81');self.reject()
    def test_native_support_not_full_PASS(self):
        self.after=self.after.replace('Native20 전체 실제 검증 NOT_RUN'.encode(),b'Native20 PASS');self.reject()
    def test_metadata_support_not_connected(self):
        self.after=self.after.replace('metadata32 전체 실행기 연결 NOT_RUN'.encode(),b'metadata32 PASS');self.reject()
    def test_preGO_branch_not_measured(self):
        self.after=self.after.replace('P239 실제 pre-GO CPU STOP 경계 NOT_RUN'.encode(),b'P239 PASS');self.reject()
    def test_CPU_retry_prohibition_not_removed(self):
        self.after=self.after.replace('CPU 보호 중단 시 자동 재시도 금지'.encode(),b'');self.reject()
    def test_original_failure_preserved(self):
        self.after=self.after.replace('원 STOP/FAILED 보존'.encode(),b'');self.reject()
