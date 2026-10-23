"""Closed construction mode and unchanged qualified parent main body."""
import ast
import json
from pathlib import Path
from unittest.mock import patch
import unittest
import batch_pre_go_namespace_probe as module


class Tests(unittest.TestCase):
    def probe(self):return module.bootstrap(Path(__file__).resolve().parents[3])

    def test_exact_frozen_parent_probe_bootstrap(self):
        probe=self.probe()
        self.assertEqual(probe.SELF,module.PARENT['path'])
        self.assertEqual(probe.main.__globals__['__name__'],'p09_exact_namespace_parent_probe')

    def test_complete_parent_main_code_defaults_and_closure_retained(self):
        probe=self.probe();selected=module.connect(probe)
        self.assertIs(selected.__code__,probe.main.__code__);self.assertIs(selected.__defaults__,probe.main.__defaults__)
        self.assertIs(selected.__closure__,probe.main.__closure__);self.assertIs(selected.__kwdefaults__,probe.main.__kwdefaults__)
        for key,value in probe.main.__globals__.items():
            if key not in ('SELF','bootstrap','json'):self.assertIs(selected.__globals__[key],value)

    def test_no_execution_mode_can_reach_original_bootstrap(self):
        for args in ([],['--run'],['--native'],['--frame'],['--diagnose-no-go'],['--connect-only','--run']):
            with patch.object(module.sys,'argv',['probe',*args]),patch.object(module,'bootstrap') as bootstrap:
                with self.assertRaisesRegex(ValueError,'ONLY_DIAGNOSTIC_CONSTRUCTION'):module.main()
                bootstrap.assert_not_called()

    def test_no_namespace_pass_without_actual_constructed_state(self):
        selected=module.connect(self.probe())
        with self.assertRaisesRegex(ValueError,'ONE_ACTUAL_DIAGNOSTIC_NAMESPACE_STATE'):
            selected.__globals__['json'].dumps({'state':'PASS_ACTUAL_PRE_GO_PARENT_CONNECTION_NOT_NATIVE'})

    def test_failure_not_relabelled_as_namespace_or_native_success(self):
        selected=module.connect(self.probe());row=dict(state='FAILED_ACTUAL_PRE_GO_PARENT_CONNECTION_NOT_NATIVE',error_code='ORIGINAL_FAILURE')
        self.assertEqual(json.loads(selected.__globals__['json'].dumps(row)),row)

    def test_diagnostic_entry_does_not_invoke_engine_worker_or_write(self):
        path=Path(__file__).resolve().parents[3]/module.SELF
        calls=[n.func.attr for n in ast.walk(ast.parse(path.read_bytes()))
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertNotIn('run_owned',calls);self.assertNotIn('worker',calls);self.assertNotIn('write',calls)
