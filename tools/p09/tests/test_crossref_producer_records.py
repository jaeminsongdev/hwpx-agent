"""In-memory record consistency models and actual fixed-eight absence inventory.

No synthetic native directories/traces are written. Model agreement is never
native provenance, execution, cleanup or semantic/product acceptance.
"""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
import crossref_producer_records as binding
from crossref_native_host_channel import FLOW


def owners_for(index):
    return [dict(process_id=1000+index*2+offset,session_id=1,
        created_at_utc=f'2026-10-17T00:00:{index*2+offset:02}.0000000Z',
        executable_sha256=binding.limits.EXECUTABLE_SHA,window_handle_binds_exact_process=True) for offset in (0,1)]


class ModelScope:
    def __init__(self):self.profiles=[];self.current=None;self.checks=0;self.finishes=0;self.stop=False
    def _retire(self):
        if self.current is not None:
            self.profiles.append(dict(native_process_assigned=self.current.profile['native_process_assigned'],
                limits_readback=dict(verified=True),cleanup_confirmed=True,last_job_accounting=dict(active_processes=0)))
            self.current=None
    def checkpoint(self,index,step):
        self.checks+=1
        if self.stop:raise ValueError('STOP_MODEL_PARENT_CHECKPOINT')
        if step in ('create_reopen_session','final_source_check'):self._retire()
        if step in ('create_save_session','create_reopen_session'):
            self.current=NS(identity=None,profile=dict(native_process_assigned=False))
    def admit_owner(self,index,identity,window):
        self.current.identity=copy.deepcopy(identity);self.current.profile['native_process_assigned']=True
    def finish(self,index,status):self.finishes+=1;self._retire()


def model_case(index,provided_owners=None):
    owners=owners_for(index) if provided_owners is None else provided_owners
    pins={stage:dict(path=binding.artifact_path(index,stage),bytes=100+index+offset,
        sha256=hashlib.sha256(f'model-{index}-{stage}'.encode()).hexdigest())
        for offset,stage in enumerate(binding.STAGES)}
    lookup={binding.artifact_path(case,stage):dict(path=binding.artifact_path(case,stage),bytes=100+case+offset,
        sha256=hashlib.sha256(f'model-{case}-{stage}'.encode()).hexdigest())
        for case in range(1,index+1) for offset,stage in enumerate(binding.STAGES)}
    scope=ModelScope();reader=NS(pin=lambda path:copy.deepcopy(lookup[path]))
    observations=binding.ParentObservations(scope,reader)
    # Exercise each preceding MODEL case in order, never fabricate an offset or
    # write a native trace to disk just to make a later case appear completed.
    for current in range(1,index+1):
        admitted=0;current_owners=owners if current==index else owners_for(current)
        for operation,step in FLOW:
            if operation=='checkpoint':observations.checkpoint(current,step)
            else:observations.admit_owner(current,current_owners[admitted],1);admitted+=1
        observations.finish(current,'returned')
    parent=observations.records[-1]
    sessions=[dict(label=label,version='11.0.0.9136',register_module_return=True,process=copy.deepcopy(owners[offset]),
        cleanup_error=None,close_without_dirty_prompt_returned=True,quit_invoked=True,remaining_owned_process_count=0)
        for offset,label in enumerate(('save','reopen'))]
    events=[dict(stage=stage,artifact_sha256=pins[stage]['sha256'],artifact_bytes=pins[stage]['bytes'],
        observed_owner_identity=copy.deepcopy(owners[0 if stage!='reopened' else 1]),
        source_observation_only=False,producer_binding_qualified=False) for stage in binding.STAGES]
    operations={name:dict(**{flag:True},error_code=None,helper_returned=True) for name,flag in
        (('opened_save','save_invoked'),('sdk_insert','execute_invoked'),('saved_save','save_invoked'),
        ('fresh_saved_open','open_invoked'),('reopened_save','save_invoked'))}
    operations['sdk_insert']['execute_returned']=True
    probes={stage:dict(schema_version='hwpx-agent.private.crossref-worker-source-probe/v1',
        state='source_probe_completed_not_native_attestation',candidate_count=8,
        observed_output_sha256=pins[stage]['sha256'],selected_case=dict(case_id=binding.case_id(index),phase=stage),
        native_execution_attested=False,native_execution_authorized=False,p09_complete=False) for stage in binding.STAGES}
    trace=dict(schema_version='hwpx-agent.private.crossref-native-case-trace/v1',case_id=binding.case_id(index),
        state='lifecycle_callbacks_returned_semantics_unqualified',source_sha256=binding.SOURCE_SHA,
        sessions=sessions,artifacts={s:{k:v for k,v in p.items() if k!='path'} for s,p in pins.items()},
        producer_events=events,cleanup_events=[dict(session_identity=copy.deepcopy(owner),close_attempted=True,
            close_returned=True,document_release_returned=True) for owner in owners],operations=operations,
        probe_observations=probes,source_identity_preserved=True,producer_binding_qualified=False,
        native_host_guard_qualified=False,p09_complete=False,trace_write_attempted=True,
        completion=dict(cleanup_error_code=None,trace_write_error_code=None,trace_write_returned=False))
    return trace,parent,pins


class ProducerRecordContracts(unittest.TestCase):
    inventory=None

    def test_01_all_eight_models_agree_without_native_promotion(self):
        triples=[model_case(index) for index in range(1,9)]
        result=binding.compare_whole_batch(*[list(values) for values in zip(*triples,strict=True)])
        self.assertEqual(len(result['cases']),8)
        self.assertFalse(result['native_provenance_qualified'] or result['native_execution_attested'] or result['p09_complete'])
        self.assertEqual(result['accepted_count_delta'],0)

    def test_02_artifact_hash_path_order_and_owner_changes_reject(self):
        for part in ('sha','path','order','owner'):
            trace,parent,pins=model_case(1)
            if part=='sha':trace['producer_events'][0]['artifact_sha256']='0'*64
            elif part=='path':parent['artifacts'][0]['pin']['path']=binding.artifact_path(2,'opened')
            elif part=='order':parent['artifacts'].reverse()
            else:parent['artifacts'][0]['identity']['process_id']+=10
            with self.assertRaises(ValueError):binding.compare_completed_case(1,trace,parent,pins)

    def test_03_reopen_birth_required_but_pid_reuse_with_new_birth_allowed(self):
        owners=owners_for(1);owners[1]['process_id']=owners[0]['process_id']
        binding.compare_completed_case(1,*model_case(1,owners))
        owners[1]['created_at_utc']=owners[0]['created_at_utc']
        with self.assertRaisesRegex(ValueError,'FRESH_REOPEN_BIRTH_NOT_PID_ONLY'):
            binding.compare_completed_case(1,*model_case(1,owners))

    def test_04_bool_counts_and_unconfirmed_cleanup_do_not_coerce(self):
        for part in ('child_count','parent_count','cleanup'):
            trace,parent,pins=model_case(1)
            if part=='child_count':trace['sessions'][0]['remaining_owned_process_count']=False
            elif part=='parent_count':parent['cleanup_profiles'][0]['remaining_processes']=False
            else:trace['cleanup_events'][1]['close_returned']=False
            with self.assertRaises(ValueError):binding.compare_completed_case(1,trace,parent,pins)

    def test_05_uncertain_sdk_and_indirect_io_never_count_as_completed(self):
        for name,key in (('sdk_insert','execute_returned'),('saved_save','helper_returned')):
            trace,parent,pins=model_case(1);trace['operations'][name][key]=None
            with self.assertRaises(ValueError):binding.compare_completed_case(1,trace,parent,pins)

    def test_06_wrong_case_phase_or_native_claim_in_probe_rejects(self):
        for part in ('case','phase','native'):
            trace,parent,pins=model_case(1);probe=trace['probe_observations']['saved']
            if part=='case':probe['selected_case']['case_id']=binding.case_id(2)
            elif part=='phase':probe['selected_case']['phase']='reopened'
            else:probe['native_execution_attested']=True
            with self.assertRaises(ValueError):binding.compare_completed_case(1,trace,parent,pins)

    def test_07_full_scope_and_unique_producer_lifetime_required(self):
        triples=[model_case(index) for index in range(1,9)]
        columns=[list(values) for values in zip(*triples,strict=True)]
        with self.assertRaisesRegex(ValueError,'WHOLE_EIGHT_REQUIRED'):
            binding.compare_whole_batch(*[values[:7] for values in columns])
        triples[1]=model_case(2,owners_for(1))
        with self.assertRaisesRegex(ValueError,'PRODUCER_LIFETIME_REUSED_ACROSS_CASES'):
            binding.compare_whole_batch(*[list(values) for values in zip(*triples,strict=True)])

    def test_08_failed_parent_checkpoint_blocks_work_but_finishes_once(self):
        scope=ModelScope();scope.stop=True
        recorder=binding.ParentObservations(scope,NS(pin=lambda p:None))
        with self.assertRaisesRegex(ValueError,'STOP_MODEL_PARENT_CHECKPOINT'):recorder.checkpoint(1,'prepare_slot')
        with self.assertRaisesRegex(ValueError,'OPERATION_ORDER_OR_STOP'):recorder.checkpoint(1,'prepare_slot')
        recorder.finish(1,'failed')
        self.assertEqual(scope.checks,1);self.assertEqual(scope.finishes,1)
        self.assertEqual(recorder.records[0]['finish_status'],'failed')
        with self.assertRaises(ValueError):recorder.finish(1,'failed')

    def test_09_actual_fixed_eight_inventory_stays_not_run(self):
        inventory=binding.current_inventory(NS(root=ROOT,checkpoint=lambda:None))
        self.assertEqual(len(inventory['cases']),8)
        self.assertTrue(all(row['state']=='NOT_RUN' for row in inventory['cases']))
        self.assertFalse(inventory['native_execution_attested'] or inventory['p09_complete'])
        self.inventory=inventory;ProducerRecordContracts.inventory=inventory


if __name__=='__main__':
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ProducerRecordContracts))
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state='nine_producer_record_contracts_pass_native_unqualified' if result.wasSuccessful()
        else 'producer_record_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),declared=result.testsRun,
        failures=failures,actual_fixed_inventory=ProducerRecordContracts.inventory,positive_record_tests_are_models_only=True,
        actual_Hangul_or_COM=False,native_provenance_qualified=False,native_execution_authorized=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
