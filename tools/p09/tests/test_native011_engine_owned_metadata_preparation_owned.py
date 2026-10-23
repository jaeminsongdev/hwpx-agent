import ast
import copy
from pathlib import Path
import unittest
import native011_engine_owned_metadata_preparation_owned as m


class Tests(unittest.TestCase):
    def fixture(self):
        first=dict(actual_complete=True,fresh_inputs=4,bytes_read=100,full_pin_sha256='model')
        meta=dict(state='PASS_ACTUAL_NATIVE011_METADATA_CALLBACK_NOT_NATIVE',fresh_inputs=2,final_fresh_hashes=2,
            selected_current_inputs=3,callback_attempts=2,metadata_body_executed=True,
            Frame_created=False,worker_created=False,GO_authorized=False,preparation_only_owned_allocation=True,
            complete_product_input_pins_qualified=False,physical_read_passes=4,physical_bytes_read=200,
            original_owned_allocation_assignment_prefix=dict(original_statements_executed=2))
        adopted=dict(original_engine_owned_assignment_adopted=True,failed=False,assignment_attempts=1,assignment_completed=1,
            semantic_fresh_inputs=2,semantic_final_fresh_hashes=2,physical_read_passes=4,physical_bytes_read=200,
            original_owned_rates=dict(binary=1048576,other=2097152))
        checkpoints={phase:dict(path=phase) for phase in ('opening','metadata','closing')}
        prep=dict(epochs=[dict(stage=stage,cleanup_confirmed=True,elapsed_seconds=.1)
            for stage in ('construction','opening','metadata','closing')],whole_opening=first,whole_closing=copy.deepcopy(first),
            declared_whole_inputs=4,declared_whole_bytes=100,whole_pin_sha256='model',metadata=meta,
            actual_owned_metadata_adoption=adopted,original_query_requests=4,actual_paced_bytes_by_kind={'binary':0,'other':200},
            completed_stage_checkpoint_pins=checkpoints)
        source=dict(fresh_inputs=1,final_fresh_hashes=1,source_pins=[dict(path='model.py')],constructor_reader_reused=False,
            callback_projection=dict(entire_original_metadata_body_inverse=True,changed_allocation_dependency_sites=1),
            connection=dict(original_engine_metadata_IO_rates=dict(binary=1048576,other=2097152)))
        proof=dict(state=m.CHILD_PASS,cleanup_confirmed=True,fresh_inputs=3,final_fresh_hashes=3,process_creation_attempts=0,
            actual_Native_Frame_created=False,actual_product_executed=False,GO_authorized=False,Native_clock_reset_or_extended=False,
            shared_budget_restored=True,parent_attempts=0,Frame_instances=0,worker_attempts=0,worker_calls=0,
            owned_metadata_preparation=prep,whole_inputs=4,current_inputs=3,preparation_source_evidence=source,
            shared_parent_connection=dict(preaudit_callback_attempts=1,original_preaudit_denial_before_metadata_IO=True),
            shared_decoder_timing_observation_artifact=dict(path='timing'))
        artifacts={phase:dict(phase=phase,execution_scope_whole_sha256='model',GO_authorized=False,accepted_count_delta=0,
            evidence=dict(whole_opening=copy.deepcopy(first))) for phase in checkpoints}
        for phase in ('metadata','closing'):artifacts[phase]['evidence']['metadata']=copy.deepcopy(meta)
        artifacts['closing']['evidence']['whole_closing']=copy.deepcopy(first)
        artifacts['timing']=dict(attempts=1,completed=1,failed=False,roles={'metadata':{}},
            original_shared=dict(shared_limit_seconds=5.,metadata_registered=True,Frame_registered=False,total_decoder_work_seconds=.1))
        return proof,artifacts
    def test_full_original_monitor_inverse_and_exact_closed_child_command(self):
        raw=(Path(__file__).resolve().parents[3]/m.original.SOURCE['path']).read_bytes()
        node,proof=m.project(raw);text=ast.unparse(ast.fix_missing_locations(node))
        self.assertTrue(proof['entire_parent_monitor_AST_inverse']);self.assertTrue(proof['parent']['entire_original_monitor_main_AST_inverse'])
        self.assertIn("command = [sys.executable, '-B', str(c.ROOT / TARGET)]",text)
        self.assertIn('2400',text);self.assertIn('cleanup_owned',text);self.assertIn('OwnedSQLJobProcess',text)
        self.assertIn('_observe_markers',text);self.assertIn('_preserve_terminal_failure',text)
        self.assertFalse(proof['original_Native_or_product_authorized'])
    def test_nonoriginal_source_rejected_before_job_or_compilation(self):
        with self.assertRaises(ValueError):m.project(b'not original')
    def test_complete_preparation_requires_both_whole_and_semantic_closing(self):
        proof,artifacts=self.fixture();self.assertEqual(m.validate(proof,lambda pin:artifacts[pin['path']]),[dict(path='model.py')])
        proof['owned_metadata_preparation']['whole_closing']['bytes_read']=99
        with self.assertRaisesRegex(ValueError,'BOTH_COMPLETE'):m.validate(proof,lambda pin:artifacts[pin['path']])
    def test_partial_or_product_or_deadline_extended_result_not_accepted(self):
        for field,value in (('actual_product_executed',True),('Native_clock_reset_or_extended',True),
            ('fresh_inputs',4),('state','PASS_COMPONENT_ONLY')):
            proof,artifacts=self.fixture();proof[field]=value
            with self.assertRaises(ValueError):m.validate(proof,lambda pin:artifacts[pin['path']])
    def test_allocation_policy_and_exact_original_preaudit_denial_retained(self):
        proof,artifacts=self.fixture();proof['owned_metadata_preparation']['actual_owned_metadata_adoption']['original_owned_rates']['other']=4194304
        with self.assertRaisesRegex(ValueError,'ORIGINAL_OWNED_POLICY'):m.validate(proof,lambda pin:artifacts[pin['path']])
        proof,artifacts=self.fixture();proof['shared_parent_connection']['preaudit_callback_attempts']=0
        with self.assertRaises(ValueError):m.validate(proof,lambda pin:artifacts[pin['path']])
    def test_missing_stage_checkpoint_or_changed_metadata_evidence_rejected(self):
        proof,artifacts=self.fixture();del proof['owned_metadata_preparation']['completed_stage_checkpoint_pins']['metadata']
        with self.assertRaisesRegex(ValueError,'ALL_THREE'):m.validate(proof,lambda pin:artifacts[pin['path']])
        proof,artifacts=self.fixture();artifacts['metadata']['evidence']['metadata']['fresh_inputs']=1
        with self.assertRaisesRegex(ValueError,'COMPLETE_METADATA_CHECKPOINT'):m.validate(proof,lambda pin:artifacts[pin['path']])
    def test_four_original600_preparation_epochs_and_shared5_not_redefined(self):
        proof,artifacts=self.fixture();proof['owned_metadata_preparation']['epochs'][-1]['elapsed_seconds']=600.1
        with self.assertRaisesRegex(ValueError,'FOUR_ORIGINAL'):m.validate(proof,lambda pin:artifacts[pin['path']])
        proof,artifacts=self.fixture();artifacts['timing']['original_shared']['total_decoder_work_seconds']=5.1
        with self.assertRaisesRegex(ValueError,'UNCHANGED_METADATA_SHARED5'):m.validate(proof,lambda pin:artifacts[pin['path']])
