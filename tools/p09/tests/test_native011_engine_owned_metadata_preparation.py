import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_engine_owned_metadata_preparation as m
import native011_metadata_tail_probe as probe
import native011_current_epoch_audit as audit
import native011_metadata_epochs as epochs


class Tests(unittest.TestCase):
    def driver(self):
        class Base:
            def __init__(self,attempt,construct_only):
                self.attempt=attempt;self.construct_only=construct_only;self.bound=False
                self.closed=False;self.case_context=None;self.decoder_timing=None;self.native=None
            def bind(self,root,a,c,guards,loader,control):self.bound=True
            def factory(self,role):raise AssertionError('NO_REAL_RESOURCE_OR_PRODUCT_IN_MODEL')
        return m.driver_type(Base,probe,audit,epochs)()
    def bind(self,driver):
        controls=NS(admit=lambda *args,**kwargs:NS(control_names=tuple(str(i) for i in range(35))))
        driver.bind(None,None,None,None,None,controls);return controls
    def test_closed_entry_only_named_original_preparation_sources_and_no_product_calls(self):
        root=Path(__file__).resolve().parents[3];raw=(root/m.SELF).read_bytes();tree=ast.parse(raw)
        calls=[node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)]
        self.assertFalse(set(calls)&{'run_owned','Popen','NativePhase','send_GO','commit'})
        self.assertIn("require(sys.argv[1:]==[],'CLOSED_NO_GO_ENTRY')",raw.decode())
        for pin in (m.AUDIT,m.EPOCH):
            source=(root/pin['path']).read_bytes()
            self.assertEqual((len(source),hashlib.sha256(source).hexdigest()),(pin['bytes'],pin['sha256']))
    def test_exact51_controls_declared_once_without_observed_native_source_union(self):
        driver=self.driver();controls=self.bind(driver)
        options=dict(exact_read=True,decoder_timing=True,chunk_join=True)
        value=controls.admit(None,None,None,**options)
        self.assertEqual(len(value.control_names),51)
        self.assertEqual(value.control_names[-16:],probe.CONTROLS+probe.OWNED_CONTROLS+m.EXTRA)
        self.assertEqual(driver.output,m.OUTPUT);self.assertTrue(driver.construct_only)
        with self.assertRaises(ValueError):controls.admit(None,None,None,**options)
    def test_four_real_epochs_have_new_exclusive_checkpoints_not_native_deadline_rotation(self):
        driver=self.driver();self.bind(driver)
        self.assertIsInstance(driver.audit,audit.PreparationAudit);self.assertIsInstance(driver.audit.epochs,epochs.Epochs)
        self.assertEqual(driver.audit.module.STAGES,('construction','opening','metadata','closing'))
        paths=[driver.audit.checkpoint_path(phase) for phase in ('opening','metadata','closing')]
        self.assertEqual(len(set(paths)),3);self.assertTrue(all('engine-owned-metadata-preparation001.' in name for name in paths))
        self.assertIsNone(driver.audit.epochs.guard);self.assertIsNone(driver.native)
    def test_resource_check_and_cleanup_use_original_preparation_audit(self):
        driver=self.driver();self.bind(driver);events=[]
        class Guard:
            samples=[dict(system_cpu_percent=1,available_ram_percent=50,commit_used_percent=40)]
            preparation_CPU=NS(summary=lambda:{'model_only':True})
            preparation_limits={'model_only':True}
            def check(self,**kwargs):events.append(kwargs)
            def close(self):self.cleanup=True
        guard=Guard();driver.audit.epochs.guard=guard;driver.audit.epochs.stage='construction'
        driver.audit.epochs.started=driver.audit.epochs.clock()
        driver.check(force=True);self.assertEqual(events,[{'force':True}]);self.assertIs(driver.samples,guard.samples)
        driver.close();self.assertTrue(driver.cleanup);self.assertTrue(driver.closed)
        with self.assertRaises(ValueError):driver.check()
    def test_failed_or_partial_run_cannot_be_reported_as_native_or_product_acceptance(self):
        driver=self.driver();self.bind(driver);driver.close();row={}
        driver.finish(None,row,None,None)
        self.assertFalse(row['actual_Native_Frame_created']);self.assertFalse(row['actual_product_executed'])
        self.assertFalse(row['GO_authorized']);self.assertFalse(row['Native_clock_reset_or_extended'])
        self.assertIsNone(row['preparation_source_evidence']);self.assertNotIn('state',row)
        self.assertTrue(row['original_four600_preparation_epochs'])
