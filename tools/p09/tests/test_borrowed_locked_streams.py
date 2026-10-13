"""새 pathname open 없이 원 guard/identity/byte 읽기/소유권 유지 계약."""
import copy
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import borrowed_locked_streams as b
import test_locked_runtime_inputs as old


class Stream(io.BytesIO):
    def __init__(self,handle):super().__init__(b'abc');self.native_handle=handle;self.seek(3)


class API:
    def __init__(self,native):self.native=native;self.calls=[];self.fail=None;self.streams=[]
    def duplicate(self,source):
        self.calls.append(('duplicate',source))
        if self.fail=='duplicate':raise OSError('MOCK_DUPLICATE')
        self.native.counter+=1;handle=self.native.counter
        self.native.handles[handle]=copy.deepcopy(self.native.handles[source]);return handle
    def descriptor(self,handle):
        self.calls.append(('descriptor',handle))
        if self.fail=='descriptor':raise OSError('MOCK_DESCRIPTOR')
        return handle
    def stream(self,fd):
        self.calls.append(('stream',fd))
        if self.fail=='stream':raise OSError('MOCK_STREAM')
        result=Stream(fd);self.streams.append(result)
        if self.fail=='seek':result.seek=lambda offset:1
        return result
    def close_handle(self,handle):
        self.calls.append(('close_handle',handle))
        if self.fail=='close':return False
        return self.native.close(handle)
    def close_fd(self,fd):self.calls.append(('close_fd',fd));return self.native.close(fd)
    def close_stream(self,stream):
        self.calls.append(('close_stream',stream.native_handle))
        if self.fail=='close':return False
        stream.close();return self.native.close(stream.native_handle)


class BorrowTests(unittest.TestCase):
    def setUp(self):
        self.pin=dict(path='tools/p09/mock.py',bytes=1,sha256='a'*64)
        self.native=old.FakeNative();self.api=API(self.native)
        self.held=b.BorrowedInputLocks(b.locks.ROOT,lambda:None,api=self.native,borrow_api=self.api)
        self.held.acquire({self.pin['path']:self.pin})
        self.reader=SimpleNamespace(_source=lambda name:b.locks.ROOT/name)
    def tearDown(self):
        self.api.fail=None;self.held.checkpoint=lambda:None
        if self.held.borrower:self.held.borrower.identity=lambda:self.held.borrower.owner
        self.held.close()
    def read(self):
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin['path']).open('rb') as stream:return stream.read()
    def test_two_reads_reset_shared_position_and_keep_original_handles(self):
        original=set(self.native.handles)
        self.assertEqual(self.read(),b'abc');self.assertEqual(self.read(),b'abc')
        self.assertEqual(set(self.native.handles),original)
        self.held.verify_two_byte_passes({self.pin['path']:self.pin})
        result=self.held.borrower.summary()
        self.assertEqual((result['duplicate_handles_opened'],result['duplicate_handles_closed'],result['shared_offset_resets']),(2,2,2))
    def test_pathname_open_is_never_called_for_byte_stream(self):
        with patch.object(Path,'open',side_effect=AssertionError('NO_PATH_OPEN')):self.assertEqual(self.read(),b'abc')
    def test_original_source_guard_runs_before_duplicate(self):
        def stopped(name):raise ValueError('MOCK_ORIGINAL_PATH_GUARD')
        self.reader._source=stopped
        with self.assertRaisesRegex(ValueError,'MOCK_ORIGINAL_PATH_GUARD'):self.read()
        self.assertEqual(self.api.calls,[])
    def test_original_resource_guard_stops_before_duplicate(self):
        self.held.checkpoint=lambda:(_ for _ in ()).throw(ValueError('MOCK_CPU_STOP'))
        with self.assertRaisesRegex(ValueError,'MOCK_CPU_STOP'):self.read()
        self.assertEqual(self.api.calls,[])
    def test_original_stream_identity_and_open_pacing_retained(self):
        self.read();self.assertEqual(self.held.stream_identity_checks,1);self.assertEqual(self.native.pacer.opens,1)
    def test_duplicate_failure_leaves_no_new_owned_loan(self):
        self.api.fail='duplicate'
        with self.assertRaises(OSError):self.read()
        self.assertIsNone(self.held.borrower.loan);self.assertEqual(len(self.native.handles),4)
    def test_descriptor_failure_closes_only_duplicate_native_handle(self):
        self.api.fail='descriptor'
        with self.assertRaises(OSError):self.read()
        self.assertEqual(self.api.calls[-1][0],'close_handle');self.assertEqual(len(self.native.handles),4)
    def test_fdopen_failure_closes_fd_not_win32_handle_twice(self):
        self.api.fail='stream'
        with self.assertRaises(OSError):self.read()
        self.assertEqual(self.api.calls[-1][0],'close_fd');self.assertEqual(len(self.native.handles),4)
    def test_seek_failure_closes_stream_and_duplicate(self):
        self.api.fail='seek'
        with self.assertRaisesRegex(ValueError,'SHARED_OFFSET_RESET'):self.read()
        self.assertEqual(self.api.calls[-1][0],'close_stream');self.assertEqual(len(self.native.handles),4)
    def test_read_exception_closes_duplicate_and_restores_adapter(self):
        original=self.reader._source
        with self.assertRaises(RuntimeError):
            with self.held.reader_sources(self.reader):
                with self.reader._source(self.pin['path']).open('rb'):raise RuntimeError('MOCK_READ')
        self.assertIs(self.reader._source,original);self.assertEqual(len(self.native.handles),4)
    def test_close_failure_retained_and_blocks_reuse_even_after_cleanup_retry(self):
        self.api.fail='close'
        with self.assertRaisesRegex(ValueError,'DUPLICATE_CLEANUP_FAILED'):self.read()
        self.assertIsNotNone(self.held.borrower.loan)
        self.api.fail=None;self.assertTrue(self.held.borrower.release())
        with self.assertRaisesRegex(ValueError,'NO_FAILED_CLEANUP'):self.read()
        self.assertFalse(self.held.summary()['input_lock_cleanup_confirmed'])
    def test_identity_mismatch_rejected_and_duplicate_closed(self):
        duplicate=self.api.duplicate
        def wrong(source):
            handle=duplicate(source);self.native.handles[handle]['identity']=[9,9];return handle
        self.api.duplicate=wrong
        with self.assertRaisesRegex(ValueError,'BYTE_STREAM_IDENTITY_DRIFT'):self.read()
        self.assertEqual(len(self.native.handles),4)
    def test_inheritable_duplicate_rejected(self):
        duplicate=self.api.duplicate
        def wrong(source):
            handle=duplicate(source);self.native.handles[handle]['inheritable']=True;return handle
        self.api.duplicate=wrong
        with self.assertRaisesRegex(ValueError,'BYTE_STREAM_IDENTITY_DRIFT'):self.read()
        self.assertEqual(len(self.native.handles),4)
    def test_nested_bindings_rejected(self):
        with self.held.reader_sources(self.reader):
            with self.assertRaisesRegex(ValueError,'ONE_SERIAL_READER'):
                with self.held.reader_sources(SimpleNamespace(_source=self.reader._source)):pass
    def test_nested_streams_rejected(self):
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin['path']).open('rb'):
                with self.assertRaisesRegex(ValueError,'ONE_SERIAL_STREAM'):
                    with self.reader._source(self.pin['path']).open('rb'):pass
    def test_stale_facade_rejected_after_and_during_new_binding(self):
        with self.held.reader_sources(self.reader):source=self.reader._source(self.pin['path'])
        for active in (False,True):
            def attempt():
                with self.assertRaisesRegex(ValueError,'BINDING_TOKEN|STREAM_READER_BINDING_REQUIRED'):
                    with source.open('rb'):pass
            if active:
                with self.held.reader_sources(self.reader):attempt()
            else:attempt()
    def test_wrong_thread_owner_rejected_before_new_stream(self):
        self.read();self.held.borrower.identity=lambda:(-1,-1)
        with self.assertRaisesRegex(ValueError,'OWNER_PROCESS_THREAD'):self.read()
    def test_close_during_binding_rejected(self):
        with self.held.reader_sources(self.reader):
            with self.assertRaisesRegex(ValueError,'READER_STILL_BOUND'):self.held.close()
    def test_write_mode_rejected_before_duplicate(self):
        with self.held.reader_sources(self.reader):
            with self.assertRaisesRegex(ValueError,'READ_BINARY_ONLY'):
                with self.reader._source(self.pin['path']).open('wb'):pass
        self.assertEqual(self.api.calls,[])
    def test_class_source_restored_without_instance_shadow(self):
        class Reader:
            def _source(self,name):return b.locks.ROOT/name
        reader=Reader()
        with self.held.reader_sources(reader):pass
        self.assertNotIn('_source',vars(reader))
    def test_cleanup_original_handles_attempted_after_duplicate_close_failure(self):
        self.api.fail='close'
        with self.assertRaises(ValueError):self.read()
        self.assertFalse(self.held.close());self.assertEqual(len(self.held.owned),0)
        self.assertEqual(len(self.native.handles),1)
    def test_native_duplicate_options_never_close_source_or_inherit(self):
        calls=[]
        class Function:
            def __init__(self,call):self.call=call
            def __call__(self,*args):return self.call(*args)
        def duplicate(*args):calls.append(args);args[3]._obj.value=123;return True
        native=SimpleNamespace(k=SimpleNamespace(GetCurrentProcess=Function(lambda:99),DuplicateHandle=Function(duplicate)))
        api=b.NativeBorrow(native);self.assertEqual(api.duplicate(7),123)
        self.assertEqual(calls[0][:3],(99,7,99));self.assertEqual(calls[0][4:],(0,False,2))
    def test_native_descriptor_flags_are_binary_read_only_noninheritable(self):
        api=b.NativeBorrow.__new__(b.NativeBorrow);api.crt=SimpleNamespace(open_osfhandle=lambda handle,flags:flags)
        flags=api.descriptor(7)
        self.assertEqual(flags,b.os.O_RDONLY|b.os.O_BINARY|b.os.O_NOINHERIT)
    def test_original_frame_two_boundaries_commit_using_borrowed_streams(self):
        import hashlib
        import runtime_input_frame as frames
        import audit_evidence_io as audit
        pin=dict(self.pin,bytes=3,sha256=hashlib.sha256(b'abc').hexdigest())
        self.native.handles[4]['size']=3
        self.held.files[str(b.locks.ROOT/self.pin['path'])]['size']=3
        # 기존 acquire를 대체하지 않고 이미 확보한 테스트 lock만 frame에 주입.
        frame=frames.Frame(frames.Registry(),{pin['path']:pin},lambda:None,held=self.held)
        frame.registry.claim(frame);frame.registered=True;frame.state='HELD'
        def reader(checkpoint):
            result=audit.AuditEvidenceReader(b.locks.ROOT,checkpoint)
            result._source=lambda name:b.locks.ROOT/name
            return result
        # 기존 frame이 요구하는 diagnostics 계약을 실제 byte reader에 연결.
        def factory(checkpoint):
            result=reader(checkpoint)
            result.diagnostics=lambda:dict(read_passes=result.read_passes,bytes_read=result.bytes_read)
            return result
        for _ in range(2):self.assertEqual(frame.read_boundary(factory,lambda:None),[pin])
        result=frame.commit(dict(cleanup_confirmed=True,owned_tree_empty=True,
            job_final=dict(active_processes=0,owned_processes=[])))
        self.assertEqual(result['frame_state'],'COMMITTED')
        self.assertEqual(result['handles']['borrowed_byte_streams']['duplicate_handles_closed'],2)
