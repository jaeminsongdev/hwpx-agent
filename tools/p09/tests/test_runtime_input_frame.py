"""P208 scope/owner/전후2회 byte/cleanup 순수 계약. native/제품은 별도 실증."""
from contextlib import contextmanager
from types import SimpleNamespace
import unittest
import runtime_input_frame as f


class Held:
    def __init__(self):self.closed=False;self.close_fail=False;self.counts={};self.stop=False;self.closed_at=[]
    def check(self):
        if self.stop:raise ValueError('MOCK_RESOURCE_STOP')
    def acquire(self,inputs):f.require(isinstance(inputs,dict),'ACTUAL_NATIVE_INPUT_DICT');self.inputs=inputs
    @contextmanager
    def reader_sources(self,reader):yield
    def verify_two_byte_passes(self,inputs):f.require(self.counts=={n:2 for n in inputs},'TWO_MOCK_STREAM_PASSES')
    def verify_held_identities(self):return dict(held_identity_checks_complete=True)
    def close(self):self.closed_at.append(dict(self.counts));self.closed=not self.close_fail;return self.closed
    def summary(self):return dict(input_lock_cleanup_confirmed=self.closed)


class Reader:
    def __init__(self,held,checkpoint):self.held=held;self.checkpoint=checkpoint;self.read_passes=0;self.bytes_read=0;self.bad=False
    def fresh_pin(self,name):
        self.checkpoint();pin=dict(self.held.inputs[name]);self.read_passes+=1;self.bytes_read+=pin['bytes']
        self.held.counts[name]=self.held.counts.get(name,0)+1
        if self.bad:pin['sha256']='b'*64
        return pin
    def diagnostics(self):return dict(read_passes=self.read_passes,bytes_read=self.bytes_read)


class FrameTests(unittest.TestCase):
    def setUp(self):
        self.owner=[(1,2)];self.registry=f.Registry(identity=lambda:self.owner[0]);self.held=Held()
        self.pin=dict(path='tools/p09/probe.txt',bytes=1,sha256='a'*64);self.inputs={self.pin['path']:self.pin}
        self.frame=f.Frame(self.registry,self.inputs,lambda:None,self.held)
        self.owned=dict(cleanup_confirmed=True,owned_tree_empty=True,job_final=dict(active_processes=0,owned_processes=[]))
    def factory(self,checkpoint):return Reader(self.held,checkpoint)
    def read(self):return self.frame.read_boundary(self.factory,lambda:None)
    def complete(self):self.frame.acquire();self.read();self.read();return self.frame.commit(self.owned)
    def test_scope_copied_and_nested_pins_immutable(self):
        self.pin['sha256']='b'*64;self.assertEqual(self.frame.inputs[self.pin['path']]['sha256'],'a'*64)
        with self.assertRaises(TypeError):self.frame.inputs[self.pin['path']]['bytes']=2
    def test_one_live_registry_frame_only(self):
        self.frame.acquire();other=f.Frame(self.registry,self.inputs,lambda:None,Held())
        with self.assertRaises(ValueError):other.acquire()
        self.assertIs(self.registry.active,self.frame);self.frame.close()
    def test_process_or_thread_change_rejected(self):
        self.frame.acquire()
        for owner in ((2,2),(1,3)):
            self.owner[0]=owner
            with self.assertRaises(ValueError):self.frame.check()
        self.owner[0]=(1,2);self.frame.close()
    def test_stale_reference_rejected_after_release(self):
        self.frame.acquire();self.frame.close()
        with self.assertRaises(ValueError):self.frame.check()
    def test_two_real_boundary_reads_required_before_commit(self):
        self.frame.acquire();self.read()
        with self.assertRaises(ValueError):self.frame.commit(self.owned)
        self.frame.close()
    def test_success_has_two_ordered_byte_passes_and_unregistered_closed_handles(self):
        out=self.complete();self.assertEqual(out['frame_state'],'COMMITTED');self.assertFalse(out['registered_live_frame'])
        self.assertEqual([row['role'] for row in out['actual_byte_boundaries']],['before','after'])
        self.assertTrue(out['original_owned_cleanup_confirmed_before_release']);self.assertIsNone(self.registry.active)
    def test_third_byte_boundary_rejected(self):
        self.frame.acquire();self.read();self.read()
        with self.assertRaises(ValueError):self.read()
        self.frame.close()
    def test_original_parent_checkpoint_runs_in_byte_read(self):
        self.frame.acquire();calls=[]
        self.frame.read_boundary(self.factory,lambda:calls.append(True));self.assertTrue(calls);self.frame.close()
    def test_checkpoint_stop_aborts_without_committed_frame(self):
        self.frame.acquire()
        def stopped():raise ValueError('MOCK_RESOURCE_STOP')
        with self.assertRaises(ValueError):self.frame.read_boundary(self.factory,stopped)
        self.assertEqual(self.frame.state,'BROKEN');self.assertTrue(self.frame.close())
    def test_hash_mismatch_aborts(self):
        self.frame.acquire()
        def bad(checkpoint):reader=self.factory(checkpoint);reader.bad=True;return reader
        with self.assertRaises(ValueError):self.frame.read_boundary(bad,lambda:None)
        self.assertEqual(self.frame.state,'BROKEN');self.frame.close()
    def test_reused_reader_counter_rejected(self):
        self.frame.acquire();reader=self.factory(lambda:None);reader.read_passes=1
        with self.assertRaises(ValueError):self.frame.read_boundary(lambda checkpoint:reader,lambda:None)
        self.frame.close()
    def test_byte_counter_omission_rejected(self):
        self.frame.acquire()
        def bad(checkpoint):
            reader=self.factory(checkpoint);reader.diagnostics=lambda:dict(read_passes=0,bytes_read=0);return reader
        with self.assertRaises(ValueError):self.frame.read_boundary(bad,lambda:None)
        self.frame.close()
    def test_reentrant_read_rejected(self):
        self.frame.acquire();self.frame.reading=True
        with self.assertRaises(ValueError):self.read()
        self.frame.reading=False;self.frame.close()
    def test_cleanup_failure_or_live_job_prevents_release_commit(self):
        self.frame.acquire();self.read();self.read()
        for owned in (dict(self.owned,cleanup_confirmed=False),dict(self.owned,owned_tree_empty=False),
                dict(self.owned,job_final=dict(active_processes=1,owned_processes=[2]))):
            with self.assertRaises(ValueError):self.frame.commit(owned)
        self.assertFalse(self.held.closed);self.frame.close()
    def test_native_two_stream_pass_failure_prevents_commit(self):
        self.frame.acquire();self.read();self.read();self.held.counts[self.pin['path']]=1
        with self.assertRaises(ValueError):self.frame.commit(self.owned)
        self.frame.close()
    def test_close_failure_retains_registry_and_is_retryable_without_success_claim(self):
        self.frame.acquire();self.read();self.read();self.held.close_fail=True
        with self.assertRaises(ValueError):self.frame.commit(self.owned)
        self.assertTrue(self.frame.registered);self.assertNotEqual(self.frame.state,'COMMITTED')
        self.held.close_fail=False;self.assertTrue(self.frame.close());self.assertIsNone(self.registry.active)
    def test_close_while_reading_rejected(self):
        self.frame.acquire();self.frame.reading=True
        with self.assertRaises(ValueError):self.frame.close()
        self.frame.reading=False;self.frame.close()
    def test_acquisition_failure_releases_registry(self):
        def stopped(inputs):raise ValueError('MOCK_ACQUIRE_FAILURE')
        self.held.acquire=stopped
        with self.assertRaises(ValueError):self.frame.acquire()
        self.assertIsNone(self.registry.active);self.assertTrue(self.held.closed)
    def test_double_acquisition_and_read_before_acquire_rejected(self):
        with self.assertRaises(ValueError):self.read()
        self.frame.acquire()
        with self.assertRaises(ValueError):self.frame.acquire()
        self.frame.close()
    def test_observation_counters_aggregate_without_reset(self):
        initial=SimpleNamespace(bytes_read=10,read_passes=2);readers=[];out=f.Counters(initial,readers)
        self.assertEqual(out.bytes_read,10);readers.append(SimpleNamespace(bytes_read=3,read_passes=1))
        out.metadata.append(SimpleNamespace(bytes_read=5,read_passes=2))
        self.assertEqual(out.bytes_read,18);self.assertEqual(out.read_passes,5)


if __name__=='__main__':unittest.main()
