"""Current004 host admission/source-boundary contracts; no Native/COM/process starts."""
import copy,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import crossref_runtime004_admission as admission
import crossref_external_batch_runtime as runtime
from test_crossref_generation004 import modeled_main

def model():
    loaded=dict(executable=str(admission.profile.fixed.PYTHON),core=str(admission.profile.fixed.PYTHON.parent/'python312.dll'),version='3.12.14',pointer_bits=64)
    pins=admission.profile.specifications()
    value=dict(state=admission.QUALIFICATION_STATE,cleanup=True,fresh_inputs=260,final_fresh_hashes=260,
        runtime_disk_image_final_fresh_hashes=2,same_live_kernel_before_after=True,native_constructor_trap_calls=0,
        actual_Hancom_ROT_COM_or_native_started=False,fixed_eight_executed=False,native_startup_qualified=False,public_entry_profile_applied=False,
        qualified_runtime_profile=dict(admission.PROFILE_PIN),runtime_current_image_pins=list(pins.values()),loaded_image_observation=loaded,
        current_runtime=admission.profile.validate(pins,loaded),steps=[dict(cleanup=True,exit_code=2,requests=1,io_threads_joined=True,
            handler_summary=dict(ready_denied_before_case_io=True),owned_job=dict(owned_tree_empty=True,forced_termination_invoked=False))])
    reader=NS(json=Mock(return_value=value),pin=Mock(return_value=dict(admission.PROFILE_PIN)),
        snapshots={admission.QUALIFICATION:dict(sha256=admission.QUALIFICATION_SHA)})
    return reader,value,loaded

class Current004Admission(unittest.TestCase):
    def test_01_fixed_closed_receipt_checked_once_and_grants_no_native_permission(self):
        reader,value,_=model()
        with patch.object(admission.r.compact,'unpack',side_effect=lambda v:v):result=admission.require_qualification(reader)
        reader.json.assert_called_once_with(admission.QUALIFICATION);reader.pin.assert_called_once_with(admission.PROFILE_PIN['path'])
        self.assertFalse(result['native_session_or_execution_authorized']);self.assertTrue(result['qualification_checked_at_bundle_boundary'])
    def test_02_receipt_hash_drift_denies_before_profile_or_native(self):
        reader,_,_=model();reader.snapshots[admission.QUALIFICATION]['sha256']='a'*64
        with patch.object(admission.r.compact,'unpack',side_effect=lambda v:v):
            with self.assertRaisesRegex(ValueError,'EXACT_QUALIFICATION_RECEIPT'):admission.require_qualification(reader)
        reader.pin.assert_not_called()
    def test_03_partial_cleanup_missing_final_or_native_claim_cannot_admit(self):
        for key,bad in [('cleanup',False),('final_fresh_hashes',259),('same_live_kernel_before_after',False),
            ('native_constructor_trap_calls',1),('actual_Hancom_ROT_COM_or_native_started',True),('fixed_eight_executed',True),
            ('native_startup_qualified',True),('public_entry_profile_applied',True),('runtime_disk_image_final_fresh_hashes',1)]:
            reader,value,_=model();value[key]=bad
            with patch.object(admission.r.compact,'unpack',side_effect=lambda v:v):
                with self.assertRaisesRegex(ValueError,'CLOSED_HOST_ONLY_QUALIFICATION'):admission.require_qualification(reader)
    def test_04_current_profile_source_must_equal_the_qualified_source(self):
        reader,_,_=model();reader.pin.return_value['sha256']='a'*64
        with patch.object(admission.r.compact,'unpack',side_effect=lambda v:v):
            with self.assertRaisesRegex(ValueError,'SAME_QUALIFIED_PROFILE_SOURCE'):admission.require_qualification(reader)
    def test_05_saved_exe_and_core_inventory_cannot_drop_or_replace_an_image(self):
        for mutate in (lambda v:v['runtime_current_image_pins'].pop(),
            lambda v:v['runtime_current_image_pins'][1].update(sha256='a'*64),
            lambda v:v['runtime_current_image_pins'].__setitem__(1,dict(v['runtime_current_image_pins'][0]))):
            reader,value,_=model();mutate(value)
            with patch.object(admission.r.compact,'unpack',side_effect=lambda v:v):
                with self.assertRaises(ValueError):admission.require_qualification(reader)
    def test_06_ready_denial_must_have_one_request_exit2_and_closed_io_job(self):
        for key,bad in [('cleanup',False),('exit_code',0),('requests',2),('io_threads_joined',False)]:
            reader,value,_=model();value['steps'][0][key]=bad
            with patch.object(admission.r.compact,'unpack',side_effect=lambda v:v):
                with self.assertRaisesRegex(ValueError,'CLOSED_READY_DENIAL'):admission.require_qualification(reader)
    def test_07_each_execution_boundary_pins_both_images_and_observes_loaded_paths_without_history(self):
        _,_,loaded=model();reader=NS(pin=Mock(side_effect=lambda name:admission.profile.specifications()[name]),json=Mock())
        with patch.object(admission.profile,'observe_loaded_images',return_value=loaded):result=admission.verify_current_reader(reader)
        self.assertEqual([c.args[0]for c in reader.pin.call_args_list],['python.exe','python312.dll']);reader.json.assert_not_called()
        self.assertFalse(result['native_session_or_execution_authorized'])
    def test_08_changed_current_core_is_rejected_not_replaced_with_saved_pin(self):
        _,_,loaded=model();pins=admission.profile.specifications();pins['python312.dll']['sha256']='a'*64
        reader=NS(pin=Mock(side_effect=lambda name:pins[name]))
        with patch.object(admission.profile,'observe_loaded_images',return_value=loaded):
            with self.assertRaisesRegex(ValueError,'CURRENT_EXE_AND_CORE_BYTES'):admission.verify_current_reader(reader)
    def test_09_qualification_denial_precedes_prerequisites_claim_scratch_and_native(self):
        status,execute,writes,_,absence=modeled_main(False,True,qualification_failure=True)
        self.assertEqual(status,2);execute.assert_not_called();absence.assert_not_called();self.assertEqual(len(writes),1)
        self.assertFalse(writes[0].args[1]['native_claim_created'])
        self.assertEqual(writes[0].args[1]['error_code'],'XREF_RUNTIME004_EXACT_QUALIFICATION_RECEIPT')
    def test_10_boundary004_closes_both_current_images_and_legacy_still_uses_legacy_gate(self):
        _,_,loaded=model();spec=admission.profile.specifications();shell=dict(path='powershell.exe',bytes=10,sha256='a'*64)
        native=dict(path=Path(runtime.installed.native.EXECUTABLE).name,bytes=runtime.installed.native.EXECUTABLE_BYTES,sha256=runtime.installed.native.EXECUTABLE_SHA)
        for current004 in (False,True):
            readers=[]
            def make_reader(root,check):
                values={}if len(readers)==0 else {native['path']:native}if len(readers)==1 else {shell['path']:shell}if len(readers)==2 else spec
                reader=NS(snapshots={},final_fresh_hashes=0)
                def pin(path):reader.snapshots[path]=copy.deepcopy(values[path]);return reader.snapshots[path]
                def finish():reader.final_fresh_hashes=len(reader.snapshots)
                reader.pin=pin;reader.finish=Mock(side_effect=finish);readers.append(reader);return reader
            with (patch.object(runtime.r.a,'AcceptanceReader',side_effect=make_reader),patch.object(runtime.installed,'runtime_pin_matches')as legacy,
                patch.object(admission.profile,'observe_loaded_images',return_value=loaded)):
                boundary=runtime.Boundary(NS(check=Mock()),{},set(),'model',shell,current004=current004);boundary.finish()
            self.assertEqual(legacy.call_count,0 if current004 else 1)
            self.assertEqual(boundary.summary()['readers']['runtime']['final_fresh_hashes'],2 if current004 else 1)
            self.assertTrue(boundary.closed);self.assertEqual([r.finish.call_count for r in readers],[1]*4)
    def test_11_invalid_boundary_scope_denied_before_creating_readers(self):
        with patch.object(runtime.r.a,'AcceptanceReader')as reader:
            for bad in(0,1,None,'4'):
                with self.assertRaisesRegex(ValueError,'EXACT_BOUNDARY004_FLAG'):runtime.Boundary(None,{},set(),'model',None,current004=bad)
        reader.assert_not_called()
