import ast
import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import native011_full_frame_worker_owned as m
import native011_readonly_terminal_monitor as terminal
import native011_full_frame_worker_validation as validation
import test_native011_full_frame_worker_validation as fixture


class Tests(unittest.TestCase):
    def read(self,pin):return (Path(__file__).resolve().parents[3]/pin['path']).read_bytes()
    def build(self):return m.build(Path('model-root'),self.read)
    def test_original_monitor_ast_inverse_exact_command_and_all_original_limits(self):
        node,proof=m.project(self.read(m.original.SOURCE));text=ast.unparse(ast.fix_missing_locations(node))
        self.assertTrue(proof['entire_original_monitor_connection_AST_inverse'])
        self.assertTrue(proof['three_live_epochs_and_empty_Job_before_audit_retained'])
        self.assertIn("command = [sys.executable, '-B', str(c.ROOT / TARGET), '--whole-no-go']",text)
        self.assertIn('2400',text);self.assertIn('_cleanup_terminal',text);self.assertIn('_terminal_complete',text)
        self.assertLess(text.index('_verify_preparation(q, a)'),text.index('OwnedSQLJobProcess(command'))
        self.assertNotIn('monitor.seen == 4',text);self.assertNotIn("'--go'",text)
    def test_build_constructs_only_functions_and_retains_original_capture_job_and_cleanup(self):
        selected=self.build();env=selected.environment
        self.assertEqual(env['TARGET'],m.TARGET);self.assertEqual(env['SELF'],m.SELF)
        self.assertEqual(env['STAGES'],('construction','opening','native_readonly','terminal_evidence'))
        self.assertEqual(env['Monitor'].MARKERS,env['MARKERS']);self.assertTrue(callable(selected.main))
        self.assertTrue(selected.validator_projection['entire_original_three_function_AST_inverse'])
        self.assertEqual(selected.validator_projection['exact_original_function_codes_attested'],4)
        self.assertIn('cleanup_owned',env);self.assertFalse(selected.projection['product_or_Native_GO_authorized'])
    def test_actual_validation_dependency_uses_new202_checker_without_old201_reclassification(self):
        selected=self.build();proof,frame,required,encode,read,reads=fixture.fixture()
        with patch.object(validation,'declared_worker',return_value=required) as declaration:
            result=selected.environment['_validate_readonly'](proof,read)
        declaration.assert_called_once();self.assertEqual(result['worker_source_count'],202)
        self.assertEqual(result['source_worker_creation_attempts'],1);self.assertFalse(result['product_executed'])
        self.assertEqual(len(reads),1)
    def test_original_sources_and_dependency_code_drift_are_denied_before_any_monitor_start(self):
        with self.assertRaises(ValueError):m.project(b'changed')
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_MONITOR_ADAPTER'):
            m.build(Path('model-root'),lambda pin:self.read(pin)+b' ' if pin==m.ADAPTER else self.read(pin))
        for name in ('project','restore_parts','validate_metadata_tail','validate'):
            with self.subTest(function=name),patch.object(m.original,name,lambda *args,**kwargs:None):
                with self.assertRaises(ValueError):self.build()
        with self.assertRaisesRegex(ValueError,'CLOSED_ADDITIONAL_ORIGINAL_FUNCTION_ATTESTATION'):
            validation.project(self.read(m.ADAPTER),m.original,extra_functions=('restore_parts',))
    def test_preparation_requires_same_sources_with_fresh_checks_not_receipt_or_hash_cache(self):
        pins=[dict(path=m.SELF,bytes=2,sha256='a'*64),dict(path=m.TARGET,bytes=3,sha256='b'*64)]
        proof=dict(state='PASS_WHOLE_NO_GO_MONITOR_CONNECTION_PREPARED_NOT_EXECUTION',cleanup_confirmed=True,
            fresh_inputs=2,final_fresh_hashes=2,source_pins=pins,actual_diagnostic_child_or_Native_or_product_executed=False)
        checks=[];reads=[];q=NS(json=lambda path:copy.deepcopy(proof),snapshots={m.SELF:pins[0]},final_fresh_hashes=0)
        def pin(path):reads.append(path);value=next(pin for pin in pins if pin['path']==path);q.snapshots[path]=value;return value
        q.pin=pin
        a=NS(exact=lambda actual,expected,label:(checks.append(expected['path']),self.assertEqual(actual,expected)))
        value=m.verify_preparation(q,a);self.assertEqual(checks,[m.SELF,m.TARGET]);self.assertEqual(reads,[m.TARGET])
        self.assertEqual(value['same_invocation_first_reads_compared'],1);self.assertEqual(value['additional_first_reads'],1)
        with self.assertRaisesRegex(ValueError,'ONE_PRELAUNCH_READER'):m.verify_preparation(q,a)
        proof['final_fresh_hashes']=1
        other=NS(json=lambda path:copy.deepcopy(proof),snapshots={},final_fresh_hashes=0)
        with self.assertRaisesRegex(ValueError,'CLOSED_CURRENT_PREPARATION'):m.verify_preparation(other,a)
    def test_changed_source_cannot_use_the_preparation_manifest(self):
        proof=dict(state='PASS_WHOLE_NO_GO_MONITOR_CONNECTION_PREPARED_NOT_EXECUTION',cleanup_confirmed=True,
            fresh_inputs=1,final_fresh_hashes=1,actual_diagnostic_child_or_Native_or_product_executed=False,
            source_pins=[dict(path=m.SELF,bytes=2,sha256='a'*64)])
        q=NS(json=lambda path:proof,pin=lambda path:dict(path=path,bytes=3,sha256='b'*64),snapshots={},final_fresh_hashes=0)
        def exact(actual,expected,label):
            if actual!=expected:raise ValueError('MODEL_CURRENT_SOURCE_CHANGED')
        with self.assertRaisesRegex(ValueError,'MODEL_CURRENT_SOURCE_CHANGED'):m.verify_preparation(q,NS(exact=exact))
    def test_default_entry_is_prepare_only_and_product_or_retry_arguments_are_rejected(self):
        with patch.object(sys,'argv',['owned.py']),patch.object(m,'prepare',return_value=17) as prepare:
            self.assertEqual(m.main(),17);prepare.assert_called_once()
        for args in (['--go'],['--attempt','2'],['--whole-no-go','--whole-no-go']):
            with patch.object(sys,'argv',['owned.py',*args]):
                with self.assertRaisesRegex(ValueError,'CLOSED_PREPARE_OR_SINGLE_WHOLE_NO_GO_ONLY'):m.main()
    def test_explicit_whole_no_go_calls_one_fixed_original_main_and_restores_arguments(self):
        calls=[];argv=['owned.py','--whole-no-go']
        def run():calls.append(list(sys.argv));return 19
        with patch.object(sys,'argv',argv),patch.object(m,'build',return_value=NS(main=run)):
            self.assertEqual(m.main(),19);self.assertIs(sys.argv,argv)
        self.assertEqual(calls,[['owned.py','--attempt','5','--generation','3']])
    def test_terminal_cleanup_then_audit_and_failure_preservation_dependencies_are_not_rewritten(self):
        selected=self.build();env=selected.environment;events=[]
        cleanup=env['cleanup_owned']
        with patch.object(terminal,'cleanup_and_audit',side_effect=lambda owned,capture,result,monitor,fn:
            (events.append(fn is cleanup) or {'model_only':True})):
            result=env['_cleanup_terminal'](object(),object(),{},object())
        self.assertEqual(events,[True]);self.assertEqual(result,{'model_only':True})
        with patch.object(m.original.original,'preserve_terminal_failure',side_effect=ValueError('MODEL_ORIGINAL_CHILD_ERROR')):
            with self.assertRaisesRegex(ValueError,'MODEL_ORIGINAL_CHILD_ERROR'):
                env['_preserve_terminal_failure'](object(),object(),{},'', '',NS(seen=3))


if __name__=='__main__':unittest.main()
