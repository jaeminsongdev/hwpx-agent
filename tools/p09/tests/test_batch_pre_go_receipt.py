"""Receipt-only code inverses and closure identity, no engine or IO run."""
from types import CellType,FunctionType,SimpleNamespace as NS
import unittest
import batch_pre_go_receipt as module
import post_product_recovery_connection_v1 as metadata


def leaf():
    raise AssertionError('NEVER_EXECUTE_THIS_BODY')
    return 'implementation/p09/evidence/p09-361-case165-current-runtime-run'


def actual_leaf():
    return 'implementation/p09/evidence/p09-361-case165-current-runtime-run'


def wrap(original):
    marker=object()
    def execute(run=1):
        if marker is None:raise AssertionError()
        return original(run)
    return execute


class Tests(unittest.TestCase):
    def engine(self,fn):return NS(run_owned=fn,worker=object(),extra=object())

    def test_exact_leaf_inverse_no_invocation_same_global_defaults_closure(self):
        engine=self.engine(actual_leaf)
        result,proof=module.project_engine(engine,metadata.receipt_namespace)
        self.assertEqual(module.literals(result.run_owned.__code__,module.DIAGNOSTIC),1)
        self.assertEqual(module.literals(result.run_owned.__code__,module.ORIGINAL),0)
        undo=metadata.receipt_namespace(result.run_owned,{module.DIAGNOSTIC:module.ORIGINAL})
        self.assertEqual(undo.__code__,actual_leaf.__code__)
        self.assertIs(engine.run_owned,actual_leaf);self.assertIs(result.worker,engine.worker)
        self.assertIs(result.extra,engine.extra);self.assertTrue(proof['complete_code_inverse'])

    def test_enclosing_bodies_defaults_globals_and_other_closure_cells_unchanged(self):
        original=wrap(wrap(actual_leaf));result,proof=module.project_engine(self.engine(original),metadata.receipt_namespace)
        self.assertEqual(len(proof['reconstructed_closure_path']),2)
        left=original;right=result.run_owned
        for _ in range(2):
            self.assertIs(left.__code__,right.__code__);self.assertIs(left.__globals__,right.__globals__)
            self.assertIs(left.__defaults__,right.__defaults__);self.assertIs(left.__kwdefaults__,right.__kwdefaults__)
            a=dict(zip(left.__code__.co_freevars,left.__closure__));b=dict(zip(right.__code__.co_freevars,right.__closure__))
            self.assertIs(a['marker'],b['marker']);left=a['original'].cell_contents;right=b['original'].cell_contents
        self.assertIs(left,actual_leaf);self.assertIs(right.__globals__,left.__globals__)

    def test_no_original_literal_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'ONE_EXACT_ORIGINAL'):module.project_engine(self.engine(lambda:None),metadata.receipt_namespace)

    def test_existing_diagnostic_literal_fails_closed(self):
        def existing():return 'implementation/p09/evidence/p09-361-case165-pre-go-runtime-diagnostic001-run'
        with self.assertRaisesRegex(ValueError,'NO_EXISTING_DIAGNOSTIC'):module.project_engine(self.engine(existing),metadata.receipt_namespace)

    def test_two_distinct_leaf_paths_are_not_ambiguously_rewritten(self):
        other=FunctionType(actual_leaf.__code__,actual_leaf.__globals__)
        def joined():return actual_leaf(),other()
        # actual_leaf is global, so explicitly capture both original functions.
        def capture(a,b):
            def joined():return a(),b()
            return joined
        with self.assertRaisesRegex(ValueError,'ONE_EXACT_ORIGINAL'):module.project_engine(self.engine(capture(actual_leaf,other)),metadata.receipt_namespace)

    def test_shared_function_path_is_rejected_not_silently_merged(self):
        def capture(a,b):
            def joined():return a(),b()
            return joined
        with self.assertRaisesRegex(ValueError,'SHARED_FUNCTION'):module.project_engine(self.engine(capture(actual_leaf,actual_leaf)),metadata.receipt_namespace)

    def test_cyclic_function_closure_is_rejected(self):
        def cycle():return cycle()
        with self.assertRaisesRegex(ValueError,'CYCLIC'):module.project_engine(self.engine(cycle),metadata.receipt_namespace)

    def test_depth_limit_is_not_unbounded_graph_search(self):
        fn=actual_leaf
        for _ in range(14):fn=wrap(fn)
        with self.assertRaisesRegex(ValueError,'BOUNDED'):module.project_engine(self.engine(fn),metadata.receipt_namespace)

    def test_missing_or_incorrect_metadata_projection_is_rejected(self):
        with self.assertRaises(ValueError):module.project_engine(self.engine(actual_leaf),lambda fn,values:fn)
        with self.assertRaises(ValueError):module.project_engine(self.engine(actual_leaf),None)

    def test_metadata_projector_must_preserve_actual_dependencies(self):
        def changed(fn,values):
            result=metadata.receipt_namespace(fn,values)
            return FunctionType(result.__code__,dict(result.__globals__))
        with self.assertRaisesRegex(ValueError,'PROJECTOR_DEPENDENCIES'):module.project_engine(self.engine(actual_leaf),changed)

    def test_original_metadata_projector_failure_is_preserved(self):
        error=ValueError('TEST_PROJECTOR_FAILURE')
        def fail(*args):raise error
        with self.assertRaises(ValueError) as caught:module.project_engine(self.engine(actual_leaf),fail)
        self.assertIs(caught.exception,error)

    def test_recovery_uses_original_strict_link_and_unchanged_template_code(self):
        calls=[]
        def connect(engine,component):calls.append((engine,component));return 'original_result'
        def template():return None
        window=NS(WINDOW_LINK=NS(connect_engine=connect,check_evidence=object()),template=template)
        recovery=NS(current_window=lambda *a:(window,{}),clone=metadata.clone,receipt_namespace=metadata.receipt_namespace)
        state=NS(windows=0,links=0,projection=None)
        api=module.recovery_api(recovery,state);selected,proof=api.current_window()
        self.assertIs(selected.template.__code__,template.__code__)
        self.assertIs(selected.WINDOW_LINK.check_evidence,window.WINDOW_LINK.check_evidence)
        engine=self.engine(actual_leaf);component=object()
        self.assertEqual(selected.WINDOW_LINK.connect_engine(engine,component),'original_result')
        self.assertIs(calls[0][1],component);self.assertIs(calls[0][0].worker,engine.worker)
        self.assertEqual((state.windows,state.links),(1,1))
        with self.assertRaises(ValueError):api.current_window()
        with self.assertRaises(ValueError):selected.WINDOW_LINK.connect_engine(engine,component)
        self.assertFalse(state.projection['GO_authorized'])

    def test_parent_loader_preserves_original_module_and_all_other_dependencies(self):
        original=NS(recovery_api=lambda recovery,*a,**kw:(recovery,a,kw),sentinel=object())
        other=object();loader=NS(load=lambda *a:(NS(native009_parent_launch_v1=original,other=other),{'original':True}))
        parent=NS(connect_package=lambda *a,**kw:NS(loader=loader,same=other),project_plan=object())
        selected,state=module.parent_api(parent);connected=selected.connect_package()
        libs,proof=connected.loader.load(None,[],{})
        self.assertIs(libs.other,other);self.assertIs(libs.native009_parent_launch_v1.sentinel,original.sentinel)
        self.assertIs(connected.same,other);self.assertEqual(proof,{'original':True})
        self.assertIs(selected.project_plan,parent.project_plan);self.assertEqual(state.loads,1)
        with self.assertRaises(ValueError):connected.loader.load(None,[],{})

    def test_parent_loader_non_target_result_untouched(self):
        libs=NS(other=object());proof=object();loader=NS(load=lambda *a:(libs,proof))
        parent=NS(connect_package=lambda:NS(loader=loader))
        selected,state=module.parent_api(parent);connected=selected.connect_package()
        actual,record=connected.loader.load(None,[],{})
        self.assertIs(actual,libs);self.assertIs(record,proof);self.assertEqual(state.loads,0)
