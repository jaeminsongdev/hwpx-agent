import unittest
from types import SimpleNamespace
from contextlib import nullcontext
import sync_current_stop_compound_documents as p


class DocumentTests(unittest.TestCase):
    def setUp(self):
        self.before=b'old\r\nexact bytes\r\n'
        text='> 2026-10-09 P234~P237 runtime-r98 runtime 수용72/249 잔여177(일반171+corpus6) 미closing후보0 다음index79 whole재조정대기69 P09·A12·A13 OPEN 원 STOP/FAILED 보존 CPU 보호 중단 시 자동 재시도 금지 PC 프리즈 원인·해결 미확정 후속 실행 caller NOT_RUN 원 P230 caller 자체는 78 FAILED로 차단\n\n'
        self.prefix=text.encode('utf-8');self.after=self.prefix+self.before
    def reject(self):
        with self.assertRaises(ValueError):p.prefix(self.before,self.after)
    def test_exact_suffix_and_scope(self):self.assertEqual(p.prefix(self.before,self.after).encode('utf-8'),self.prefix)
    def test_normalized_newlines_not_original_bytes(self):self.after=self.prefix+self.before.replace(b'\r\n',b'\n');self.reject()
    def test_changed_original_bytes(self):self.after=self.prefix+self.before+b'x';self.reject()
    def test_no_status_prefix(self):self.after=self.before;self.reject()
    def test_wrong_count(self):self.after=self.after.replace(b'72/249',b'73/249');self.reject()
    def test_wrong_next_index(self):self.after=self.after.replace(b'index79',b'index80');self.reject()
    def test_unimplemented_caller_not_ready(self):self.after=self.after.replace(b'caller NOT_RUN',b'caller READY');self.reject()
    def test_one_byte_read_provides_buffer_and_hash(self):
        calls=[];buffer=bytearray(b'fixture');pin=dict(path='fixture',bytes=7,sha256='literal');snapshots={}
        def read(name,parse):calls.append((name,parse));return pin,buffer
        q=SimpleNamespace(context=SimpleNamespace(scope=lambda tag:nullcontext()),name=lambda name:name,
            reader=SimpleNamespace(_read=read,_bind=lambda name,row:snapshots.update({name:row})))
        self.assertIs(p.bound_bytes(q,'fixture'),buffer);self.assertEqual(calls,[('fixture',True)])
        self.assertEqual(snapshots,{'fixture':pin})
