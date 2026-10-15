import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import scheduled_binding_resources as binding
import run_scheduled_signed_tests as subject
from sql_runtime_supervision import SQLRuntimeResources,finish_watcher

BODY = '''def checkpoint():
    nonlocal hot
    hot, reason = maintenance.decision(observed_sample(windows), hot)
    maintenance.require(reason is None, reason)
'''


class ScheduledSignedTests(unittest.TestCase):
    def grammar(self,text=BODY):
        return binding.pressure_body_only(text,{"maintenance":binding.maintenance,"observed_sample":binding.observed_sample})

    def resources(self,rows):
        class Kernel:
            def GetCurrentProcess(self): return 1
        class Windows:
            mask=1;k=Kernel()
            def sample(self): return rows.pop(0)
        return SQLRuntimeResources(windows=Windows())

    def row(self,cpu=20,ram=50,commit=35):
        return {"system_cpu_percent":cpu,"available_ram_percent":ram,"commit_used_percent":commit}

    def real_callback(self,windows):
        callbacks=[]
        def capture(reader,root,callback,maximum_parse_bytes=binding.MAX_PARSE_BYTES):
            callbacks.append(callback)
            raise RuntimeError('capture_original_pressure_callback')
        with patch.object(subject.previous.previous,'load_binding',return_value=({},[],[])), \
                patch.object(binding.AuditEvidenceReader,'__init__',capture):
            with self.assertRaisesRegex(RuntimeError,'capture_original_pressure_callback'):
                subject.previous.load_binding(windows,subject.previous.INVENTORY,1)
        self.assertEqual(len(callbacks),1)
        binding.validate_pressure_callback(callbacks[0],windows)
        return callbacks[0]

    def test_exact_resource_only_ast_is_admitted(self):
        self.assertTrue(self.grammar())

    def test_input_auth_hash_extra_call_cannot_be_silently_scheduled(self):
        for line in ("source_check()","verify_signature()","digest(source)","authority.require()"):
            with self.assertRaises(ValueError): self.grammar(BODY+'    '+line+'\n')

    def test_changed_cpu_function_or_reason_predicate_is_denied(self):
        for text in (BODY.replace("maintenance.decision","maintenance.require"),BODY.replace("reason is None","reason is not None"),BODY.replace("observed_sample(windows)","observed_sample()"),BODY.replace("nonlocal hot","nonlocal other"),BODY.replace('checkpoint():','checkpoint(unreviewed, /):')):
            with self.assertRaises(ValueError): self.grammar(text)

    def test_foreign_callback_module_or_closure_is_denied(self):
        def callback(): pass
        with self.assertRaises(ValueError):binding.validate_pressure_callback(callback,object())

    def test_thousands_of_io_checkpoints_do_not_duplicate_cpu_sample_streak(self):
        now=[10.0];resources=self.resources([self.row(),self.row(99)])
        try:
            with patch.object(binding.time,"monotonic",side_effect=lambda:now[0]):
                resources.sample();guard=binding.ScheduledBinding(object(),resources,clock=lambda:now[0])
                for _ in range(1000):guard.checkpoint()
                self.assertEqual(len(resources.samples),1);self.assertEqual(resources.hot,0)
                now[0]+=.5;guard.checkpoint();self.assertEqual(len(resources.samples),2);self.assertEqual(resources.hot,1)
        finally:finish_watcher(resources,{})

    def test_four_real_half_second_saturation_windows_still_stop(self):
        now=[10.0];resources=self.resources([self.row(),*[self.row(99) for _ in range(4)]])
        try:
            with patch.object(binding.time,"monotonic",side_effect=lambda:now[0]):
                resources.sample();guard=binding.ScheduledBinding(object(),resources,clock=lambda:now[0])
                for _ in range(3):now[0]+=.5;guard.checkpoint()
                now[0]+=.5
                with self.assertRaisesRegex(ValueError,"STOP_SUSTAINED_SYSTEM_CPU"):guard.checkpoint()
                self.assertEqual(resources.hot,4)
        finally:finish_watcher(resources,{})

    def test_memory_and_commit_pressure_keep_original_thresholds(self):
        for row,code in ((self.row(ram=4.99),"STOP_LOW_AVAILABLE_RAM"),(self.row(commit=95),"STOP_SYSTEM_COMMIT_PRESSURE")):
            now=[10.0];resources=self.resources([self.row(),row])
            try:
                with patch.object(binding.time,"monotonic",side_effect=lambda:now[0]):
                    resources.sample();guard=binding.ScheduledBinding(object(),resources,clock=lambda:now[0]);now[0]+=.5
                    with self.assertRaisesRegex(ValueError,code):guard.checkpoint()
            finally:finish_watcher(resources,{})

    def test_clock_regression_nonfinite_and_scope_overrun_fail_closed(self):
        for bad in (9.0,float("nan"),True,611.0):
            now=[10.0];resources=SimpleNamespace(checkpoint_io=lambda:None)
            guard=binding.ScheduledBinding(object(),resources,clock=lambda:now[0]);now[0]=bad
            with self.assertRaises(ValueError):guard.checkpoint()

    def test_reader_root_or_parse_budget_cannot_be_relaxed(self):
        guard=binding.ScheduledBinding(object(),SimpleNamespace(checkpoint_io=lambda:None))
        for root,budget in (("foreign",binding.MAX_PARSE_BYTES),(binding.maintenance.ROOT,binding.MAX_PARSE_BYTES+1)):
            with self.assertRaises(ValueError):guard.init_reader(object(),root,lambda:None,budget)

    def test_full_current_inventory_checks_remain_inherited_not_observation_only(self):
        row={"source_variant":subject.VARIANT,"task":subject.INVENTORY,
            "binding_resource_schedule":{"all_legacy_readers_final_fresh_hash_inventory_exact":True,"cleanup_confirmed":True}}
        with patch.object(subject.previous,"accept_inventory") as accept:subject.accept_inventory(row,{},[],[])
        accept.assert_called_once()
        for flag in row['binding_resource_schedule']:
            wrong=copy.deepcopy(row);wrong['binding_resource_schedule'][flag]=False
            with self.assertRaises(ValueError):subject.accept_inventory(wrong,{},[],[])

    def test_budget_keeps600_compile180_runtime_without_full249_extension(self):
        for task,maximum in ((subject.INVENTORY,600),(subject.PROFILE,180)):
            subject.require_duration(task,maximum)
            for bad in (True,29,maximum+1,1200):
                with self.assertRaises(ValueError):subject.require_duration(task,bad)

    def test_worker_uses_original_two_package_overrides_exact_filter_GO_and_job_gate(self):
        from tests.test_stored_signed_continuation import StoredSignedContinuationTests
        helper=StoredSignedContinuationTests()
        saved=subject.previous.previous.original.run_worker
        captured=[]
        def boundary(task):
            args=["cargo.exe",*subject.previous.previous.original.ARGS,"--locked","--offline","--jobs","1","--color=never","--target-dir",str(subject.maintenance.TARGET),"--",subject.previous.previous.original.NAME,"--exact","--nocapture","--test-threads=1"]
            from tests.test_optimized_signed_tests import OptimizedSignedTests
            return subject.subprocess.call(args,cwd=subject.maintenance.ROOT,stdin=subject.subprocess.DEVNULL,env=OptimizedSignedTests().env())
        with patch.object(subject.previous.previous,"run_worker",boundary),patch.object(subject.subprocess,"call",side_effect=lambda a,**k:captured.append(a) or 0):
            self.assertEqual(subject.run_worker(subject.PROFILE),0)
        self.assertEqual(captured[0][-5:],["--",subject.previous.previous.original.NAME,"--exact","--nocapture","--test-threads=1"])
        self.assertEqual(captured[0][1:23],[x for entry in subject.previous.CONFIG for x in ("--config",entry)])
        self.assertIs(subject.previous.previous.original.run_worker,saved)
        self.assertEqual(helper.worker(subject.previous.previous.original.CHANGED)[0],0)
        for go,in_job in (("wrong\n",True),("P149_GO\n",False)):
            with self.assertRaises(ValueError):helper.worker(subject.previous.previous.original.CHANGED,go=go,in_job=in_job)

    def test_scheduler_context_and_original_constructor_restore_on_exception(self):
        class Resources:
            reason=None;samples=[]
            def admit(self):pass
        before=binding.AuditEvidenceReader.__init__
        with patch.object(binding,"finish_watcher",return_value=True):
            with self.assertRaises(RuntimeError):
                with binding.ScheduledBinding(object(),Resources()):raise RuntimeError("bounded")
        self.assertIs(binding.AuditEvidenceReader.__init__,before)

    def test_partial_reader_cannot_claim_whole_closing_inventory(self):
        resources=SimpleNamespace(reason=None,samples=[])
        guard=binding.ScheduledBinding(object(),resources)
        guard.readers=[SimpleNamespace(final_fresh_hashes=0,snapshots={"x":{}},read_passes=1,bytes_read=1)]
        self.assertFalse(guard.summary()['all_legacy_readers_final_fresh_hash_inventory_exact'])

    def test_empty_reader_inventory_is_not_full_binding_proof(self):
        guard=binding.ScheduledBinding(object(),SimpleNamespace(reason=None,samples=[]))
        self.assertFalse(guard.summary()['all_legacy_readers_final_fresh_hash_inventory_exact'])

    def test_real_reader_constructor_and_full_byte_closing_under_context(self):
        resources=self.resources([self.row()])
        windows=object();callback=self.real_callback(windows)
        before=binding.AuditEvidenceReader.__init__
        try:
            with patch.object(resources,'admit',side_effect=resources.sample):
                with binding.ScheduledBinding(windows,resources) as guard:
                    reader=binding.AuditEvidenceReader(binding.maintenance.ROOT,callback)
                    pin=reader.pin(subject.SELF);reader.finish()
                    self.assertEqual(pin['path'],subject.SELF)
                    self.assertEqual(reader.final_fresh_hashes,1)
                    self.assertEqual(reader.read_passes,2)
            self.assertIs(binding.AuditEvidenceReader.__init__,before)
            self.assertTrue(guard.summary()['all_legacy_readers_final_fresh_hash_inventory_exact'])
            self.assertTrue(guard.summary()['cleanup_confirmed'])
        finally:finish_watcher(resources,{})

    def test_original_callback_fresh_samples_share_cadence_across_readers(self):
        now=[10.0];resources=self.resources([self.row(),self.row(),self.row()])
        sampled=[]
        class Windows:
            def sample(inner):sampled.append(now[0]);return self.row()
        windows=Windows();callback=self.real_callback(windows)
        try:
            with patch.object(binding.time,'monotonic',side_effect=lambda:now[0]):
                resources.sample()
                guard=binding.ScheduledBinding(windows,resources,clock=lambda:now[0])
                readers=[binding.AuditEvidenceReader.__new__(binding.AuditEvidenceReader) for _ in range(2)]
                for reader in readers:guard.init_reader(reader,binding.maintenance.ROOT,callback)
                for _ in range(1000):readers[0].checkpoint();readers[1].checkpoint()
                self.assertEqual(sampled,[])
                now[0]+=.5;readers[0].checkpoint();readers[1].checkpoint()
                now[0]+=.5;readers[1].checkpoint();readers[0].checkpoint()
                self.assertEqual(sampled,[10.5,11.0])
                self.assertEqual(guard.original_pressure_calls,2)
                self.assertEqual(len(resources.samples),3)
        finally:finish_watcher(resources,{})
