"""Diagnostic scope and closed-mode contracts; no original engine execution."""
import ast
from pathlib import Path
from types import MappingProxyType,SimpleNamespace as NS
import unittest
from unittest.mock import patch
import batch_zlib_frame_probe as module
import current_stored_runtime_scope as scope


class Tests(unittest.TestCase):
    def test_exact_metadata_driver_bootstrap_is_unexecuted_private_namespace(self):
        metadata=module.bootstrap(Path(__file__).resolve().parents[3])
        self.assertEqual(metadata.SELF,module.METADATA['path'])
        self.assertEqual(metadata.main.__globals__['__name__'],'p09_exact_frame_probe_metadata')
        self.assertEqual(metadata.main.__globals__['__file__'],str(Path(__file__).resolve().parents[3]/module.METADATA['path']))

    def test_scope_addition_preserves_original_parent_function_and_all_inputs(self):
        before={'old':dict(path='old',bytes=1,sha256='1'*64)}
        extra={'new':dict(path='new',bytes=2,sha256='2'*64)}
        calls=[]
        def project(*args):calls.append(args);return 'original_result'
        parent=NS(project_plan=project,source_table=object(),main=object())
        selected=module.extended_parent(parent,extra)
        args=(object(),object(),before,NS(scope=scope),object())
        self.assertEqual(selected.project_plan(*args),'original_result')
        self.assertIs(parent.project_plan,project);self.assertIs(selected.source_table,parent.source_table)
        self.assertIs(selected.main,parent.main);self.assertEqual(calls[0][2],{**before,**extra})
        for i in (0,1,3,4):self.assertIs(calls[0][i],args[i])
        self.assertEqual(before,{'old':dict(path='old',bytes=1,sha256='1'*64)})

    def test_new_scope_conflict_is_rejected_before_original_projection(self):
        called=[]
        original={'same':dict(path='same',bytes=1,sha256='1'*64)}
        extras={'same':dict(path='same',bytes=2,sha256='2'*64)}
        parent=NS(project_plan=lambda *a:called.append(a))
        with self.assertRaises(ValueError):module.extended_parent(parent,extras).project_plan(None,None,original,NS(scope=scope),None)
        self.assertEqual(called,[])

    def test_immutable_batch_pin_is_compared_as_exact_plain_pin_not_proxy_type(self):
        from accept_case112_current_epoch import exact
        pin=dict(path='new',bytes=1,sha256='1'*64);immutable=MappingProxyType(pin)
        exact(dict(immutable),pin,'TEST_EXACT_CURRENT_PIN')
        with self.assertRaises(ValueError):exact(dict(immutable),dict(pin,bytes=True),'TEST_NO_BOOLEAN_DRIFT')

    def test_no_native_product_or_GO_mode_reaches_bootstrap(self):
        for args in ([],['--run'],['--native'],['--frame'],['--metadata'],['--connect-only','--run']):
            with patch.object(module.sys,'argv',['probe',*args]),patch.object(module,'bootstrap') as bootstrap:
                with self.assertRaisesRegex(ValueError,'ONLY_PARENT_CONSTRUCTION'):module.main()
                bootstrap.assert_not_called()

    def test_diagnostic_program_never_calls_run_owned_or_worker_or_gate_write(self):
        path=Path(__file__).resolve().parents[3]/module.SELF
        tree=ast.parse(path.read_bytes())
        names=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertNotIn('run_owned',names);self.assertNotIn('worker',names);self.assertNotIn('write',names)
