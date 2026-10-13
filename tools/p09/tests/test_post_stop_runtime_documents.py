import unittest
import sync_post_stop_runtime_documents as m


class PostStopDocumentTests(unittest.TestCase):
    def setUp(self):
        self.before=b'old\r\nexact bytes\r\n'
        text='> 2026-10-09 P238~P240 runtime-r99 runtime 수용73/249 잔여176(일반170+corpus6) 미closing후보0 다음index80 whole재조정대기70 P09·A12·A13 OPEN 원 STOP/FAILED 보존 CPU 보호 중단 시 자동 재시도 금지 PC 프리즈 원인·해결 미확정 P239 실제 실행기 연결 NOT_RUN\n\n'
        self.prefix=text.encode('utf-8');self.after=self.prefix+self.before
    def reject(self):
        with self.assertRaises(ValueError):m.prefix(self.before,self.after)
    def test_exact_suffix_scope(self):self.assertEqual(m.prefix(self.before,self.after).encode('utf-8'),self.prefix)
    def test_normalized_old_bytes_rejected(self):self.after=self.prefix+self.before.replace(b'\r\n',b'\n');self.reject()
    def test_changed_old_suffix(self):self.after+=b'x';self.reject()
    def test_no_prefix(self):self.after=self.before;self.reject()
    def test_wrong_runtime_count(self):self.after=self.after.replace(b'73/249',b'74/249');self.reject()
    def test_wrong_next_index(self):self.after=self.after.replace(b'index80',b'index81');self.reject()
    def test_support_cannot_be_actual_PASS(self):self.after=self.after.replace(b'NOT_RUN',b'PASS');self.reject()
    def test_CPU_retry_rule_not_removed(self):
        self.after=self.after.replace('CPU 보호 중단 시 자동 재시도 금지'.encode('utf-8'),b'');self.reject()
