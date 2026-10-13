"""관측 hook의 제한 계약. hook 보안격리나 실제 native IO 검증으로 승격하지 않는다."""
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import audit_minimal_worker_inputs as a


class InputAuditTests(unittest.TestCase):
    def setUp(self):self.trace=a.Trace(a.ROOT/'implementation/p09/evidence/runtime-r07/mock-receipt.json')

    def test_child_events_denied(self):
        for event in ('subprocess.Popen','os.system','os.exec','os.spawn','_winapi.CreateProcess'):
            with self.assertRaises(PermissionError):self.trace.hook(event,())
        self.assertEqual(self.trace.blocked_child_events,5)

    def test_mutation_and_network_denied(self):
        for event in ('socket.connect','os.remove','os.rename','os.mkdir','os.link','os.symlink'):
            with self.assertRaises(PermissionError):self.trace.hook(event,())

    def test_write_denied_before_publish_and_wrong_path(self):
        with self.assertRaises(PermissionError):self.trace.hook('open',(str(self.trace.target),'w',os.O_WRONLY))
        self.trace.phase='publish'
        with self.assertRaises(PermissionError):self.trace.hook('open',(str(a.ROOT/'other.json'),'x',os.O_WRONLY|os.O_EXCL))

    def test_only_exclusive_named_receipt_publish_allowed(self):
        self.trace.phase='publish'
        self.trace.hook('open',(str(self.trace.target),'x',os.O_WRONLY|os.O_CREAT|os.O_EXCL))
        with self.assertRaisesRegex(ValueError,'EXCLUSIVE_RECEIPT_WRITE'):
            self.trace.hook('open',(str(self.trace.target),'w',os.O_WRONLY|os.O_CREAT))

    def test_repo_exe_and_bytecode_reads_denied(self):
        with patch.object(Path,'stat',return_value=SimpleNamespace(st_size=10)):
            for path in ('target/test.exe','tools/p09/__pycache__/test.pyc'):
                with self.assertRaisesRegex(ValueError,'REPO_EXE_OR_BYTECODE_READ_DENIED'):
                    self.trace.hook('open',(str(a.ROOT/path),'r',0))

    def test_outside_data_denied_and_code_names_not_retained(self):
        with patch.object(Path,'stat',return_value=SimpleNamespace(st_size=10)):
            with self.assertRaisesRegex(ValueError,'OUTSIDE_DATA_READ_DENIED'):
                self.trace.hook('open',(str(a.ROOT.parent/'private.json'),'r',0))
            self.trace.hook('open',(str(a.ROOT.parent/'runtime.py'),'r',0))
        self.assertEqual(self.trace.outside_code_reads,1);self.assertEqual(self.trace.code,set());self.assertEqual(self.trace.data,set())

    def test_event_byte_and_deadline_bounds(self):
        with patch.object(Path,'stat',return_value=SimpleNamespace(st_size=10)):
            self.trace.events=a.MAX_EVENTS
            with self.assertRaisesRegex(ValueError,'EVENT_BOUND'):self.trace.hook('open',(str(a.ROOT/'sample.py'),'r',0))
            self.setUp();self.trace.declared=a.MAX_DECLARED_BYTES
            with self.assertRaisesRegex(ValueError,'DECLARED_READ_BOUND'):self.trace.hook('open',(str(a.ROOT/'sample.py'),'r',0))
            self.setUp();self.trace.started-=61
            with self.assertRaisesRegex(ValueError,'TRACE_DEADLINE'):self.trace.hook('open',(str(a.ROOT/'sample.py'),'r',0))

    def test_repo_code_data_classification_and_flags_type(self):
        with patch.object(Path,'stat',return_value=SimpleNamespace(st_size=10)):
            self.trace.hook('open',(str(a.ROOT/'sample.py'),'r',0));self.trace.hook('open',(str(a.ROOT/'manifest.json'),'r',0))
        self.assertEqual(self.trace.code,{'sample.py'});self.assertEqual(self.trace.data,{'manifest.json'})
        with self.assertRaisesRegex(ValueError,'OPEN_FLAGS_TYPE'):self.trace.hook('open',('unused','r',None))


if __name__=='__main__':unittest.main()
