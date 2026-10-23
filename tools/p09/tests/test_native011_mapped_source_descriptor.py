"""Mapping API models; real Win32 and source hashes need separate evidence."""
import hashlib
import time
import unittest
import native011_inherited_source_probe_child as child


class MappedDescriptorContracts(unittest.TestCase):
    def test_byte_pacer_uses_precise_monotone_clock_without_changing_deadline(self):
        pacer=child.BytePacer(lambda:None)
        self.assertIs(pacer.clock,time.perf_counter)
        self.assertTrue(time.get_clock_info('perf_counter').monotonic)
        self.assertLess(time.get_clock_info('perf_counter').resolution,0.001)

    def fixture(self):
        class API:
            def __init__(self):
                self.body=b'{"metadata":true}\n';self.handles={};self.events=[];self.fail=None
            def create_descriptor(self,raw):
                self.events.append('create');self.body=raw;self.handles[10]=0;return 10
            def duplicate_descriptor_reader(self,handle):
                self.events.append('duplicate')
                if self.fail=='duplicate':raise OSError('model')
                self.handles[20]=1;return 20
            def close(self,handle):
                self.events.append(('close',handle))
                if self.fail=='close':return False
                del self.handles[handle];return True
            def flags(self,handle):return self.handles[handle]
            def clear_inheritance(self,handle):self.handles[handle]=0
            def deny_descriptor_write(self,handle,size):
                self.events.append('deny_write')
                if self.fail=='write':raise ValueError('MODEL_WRITABLE_MAPPING')
            def read_descriptor(self,handle,size):self.events.append('read');return self.body
        api=API();reservations=[]
        descriptor=child.DescriptorMapping(api,lambda:reservations.append(1))
        return descriptor,api,reservations

    def test_writer_closed_before_restricted_reader_is_exposed(self):
        d,k,r=self.fixture();self.assertEqual(d.prepare(k.body),20)
        self.assertEqual(k.events[:4],['create','duplicate',('close',10),'deny_write'])
        self.assertEqual(k.handles,{20:1});self.assertEqual(len(r),2)
        self.assertTrue(d.close());self.assertEqual(k.handles,{})
        self.assertFalse(d.summary()['source_byte_or_hash_cache'])

    def test_no_second_prepare_or_oversized_or_empty_payload(self):
        d,k,_=self.fixture()
        for raw in (b'',b'x'*262145,'metadata'):
            with self.assertRaises(ValueError):d.prepare(raw)
        d.prepare(k.body)
        with self.assertRaises(ValueError):d.prepare(k.body)
        self.assertTrue(d.close())

    def test_duplicate_failure_retains_original_error_and_closes_writer(self):
        d,k,_=self.fixture();k.fail='duplicate'
        with self.assertRaises(OSError):d.prepare(k.body)
        self.assertTrue(d.failed);self.assertTrue(d.close());self.assertEqual(k.handles,{})

    def test_writable_descriptor_fails_closed_and_all_handles_cleaned(self):
        d,k,_=self.fixture();k.fail='write'
        with self.assertRaisesRegex(ValueError,'MODEL_WRITABLE_MAPPING'):d.prepare(k.body)
        self.assertTrue(d.failed);self.assertTrue(d.close());self.assertEqual(k.handles,{})

    def test_cleanup_failure_is_sticky_even_when_later_close_succeeds(self):
        d,k,_=self.fixture();d.prepare(k.body);k.fail='close'
        self.assertFalse(d.close());k.fail=None;self.assertFalse(d.close());self.assertTrue(d.failed)
        self.assertEqual(k.handles,{})

    def test_child_hashes_actual_mapping_and_closes_handle(self):
        d,k,_=self.fixture();handle=d.prepare(k.body);raw=k.body
        args=['--source-mapped-probe',str(handle),str(len(raw)),hashlib.sha256(raw).hexdigest()]
        self.assertEqual(child.mapped_descriptor(k,args,lambda:None),raw)
        self.assertEqual(k.handles,{});self.assertEqual(k.events.count('read'),1)

    def test_changed_descriptor_detected_and_owned_handle_closed(self):
        d,k,_=self.fixture();handle=d.prepare(k.body);raw=k.body;k.body=b'X'*len(raw)
        args=['--source-mapped-probe',str(handle),str(len(raw)),hashlib.sha256(raw).hexdigest()]
        with self.assertRaisesRegex(ValueError,'EXACT_DESCRIPTOR_LENGTH_AND_HASH'):
            child.mapped_descriptor(k,args,lambda:None)
        self.assertEqual(k.handles,{})

    def test_child_rejects_noninherited_handle_without_claiming_or_closing(self):
        d,k,_=self.fixture();handle=d.prepare(k.body);k.handles[handle]=0
        args=['--source-mapped-probe',str(handle),str(len(k.body)),hashlib.sha256(k.body).hexdigest()]
        with self.assertRaisesRegex(ValueError,'REAL_INHERITED_METADATA_READER'):
            child.mapped_descriptor(k,args,lambda:None)
        self.assertEqual(k.handles,{20:0});self.assertTrue(d.close())

    def test_invalid_argument_shapes_bounds_and_booleans_are_rejected(self):
        digest='0'*64
        for args in ([],['--source-mapped-probe','1','1'],['--source-mapped-probe','0','1',digest],
            ['--source-mapped-probe','1','262145',digest],['--source-mapped-probe',True,'1',digest],
            ['--source-mapped-probe',str(2**64),'1',digest],['--source-mapped-probe','1','1','X'*64]):
            with self.assertRaises(ValueError):child.descriptor_arguments(args)

    def test_checkpoint_failure_prevents_mapping_read_and_closes_claimed_handle(self):
        d,k,_=self.fixture();handle=d.prepare(k.body);calls=[]
        def checkpoint():
            calls.append(1)
            if len(calls)==2:raise ValueError('MODEL_RESOURCE_STOP')
        args=['--source-mapped-probe',str(handle),str(len(k.body)),hashlib.sha256(k.body).hexdigest()]
        with self.assertRaisesRegex(ValueError,'MODEL_RESOURCE_STOP'):
            child.mapped_descriptor(k,args,checkpoint)
        self.assertEqual(k.handles,{});self.assertNotIn('read',k.events)
