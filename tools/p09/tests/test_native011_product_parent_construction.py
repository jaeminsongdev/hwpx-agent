import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_product_parent_construction as m


class Tests(unittest.TestCase):
    def driver(self):
        class Base:
            def __init__(self):self.construct_only=True
            def bind(self,*args):pass
            def run(self,*args):return dict(actual_Native_Frame_created=False,actual_product_executed=False)
        state=NS(calls=1,admission=dict(worker_sources=202,source_declaration_only=True,GO_authorized=False))
        def bind(control,raw):
            before=control.admit
            def admit(*args,**kwargs):
                value=before(*args,**kwargs);return NS(**{**vars(value),'control_names':value.control_names+tuple('extra'+str(i) for i in range(10))})
            control.admit=admit;return state,dict(model=True)
        api=NS(SOURCE={'path':'tools/p09/native011_ready_scope_connection.py','bytes':13232},bind=bind)
        return m.driver_type(Base,api)(),state
    def row(self):
        return dict(exact_current_worker201_scope=dict(required_worker_sources=202,direct_current_worker_sources=202,
            missing_sources=[],conflicting_sources=[],history_inputs=419,original_base_reference_same=True,
            actual_live_Frame_coverage_qualified=False))
    def test_exact59_controls_keep_owned_base_and_named_new_source202_roles(self):
        driver,state=self.driver();control=NS(admit=lambda *args,**kwargs:NS(control_names=tuple('base'+str(i) for i in range(47))))
        root=Path(__file__).resolve().parents[3];driver.bind(root,None,None,None,None,control)
        value=control.admit(None,None,None);self.assertEqual(len(value.control_names),59)
        self.assertEqual(value.control_names[-2:],(m.SELF,m.TEST));self.assertTrue(driver.construct_only)
        self.assertEqual(driver.output,m.OUTPUT)
        with self.assertRaises(ValueError):control.admit(None,None,None)
    def test_actual_scope202_required_but_no_product_handoff_or_native_credit_created(self):
        driver,state=self.driver();driver.scope_state=state;driver.scope_projection={};row=self.row()
        result=driver.run(None,None,None,None,None,None,None,None,None,None,None,row,None,None)
        self.assertIn('NOT_NATIVE',result['state']);self.assertFalse(result['actual_product_launch_handoff_installed'])
        self.assertFalse(result['actual_worker202_GO_or_Native_qualified'])
        self.assertIs(result['exact_current_worker202_scope'],row['exact_current_worker201_scope'])
    def test_old201_or_missing_source_cannot_be_silently_called202(self):
        for fault in ('count','missing','history'):
            driver,state=self.driver();driver.scope_state=state;row=self.row()
            if fault=='count':row['exact_current_worker201_scope']['required_worker_sources']=201
            elif fault=='missing':row['exact_current_worker201_scope']['missing_sources']=['missing.py']
            else:row['exact_current_worker201_scope']['history_inputs']=418
            with self.assertRaises(ValueError):driver.run(None,None,None,None,None,None,None,None,None,None,None,row,None,None)
    def test_closed_constructor_has_no_whole_native_worker_product_or_intent_calls(self):
        text=(Path(__file__).resolve().parents[3]/m.SELF).read_text(encoding='utf-8');tree=ast.parse(text)
        calls={node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
        self.assertFalse(calls&{'Popen','run_owned','begin','consume_intent','NativePhase'})
        self.assertIn("require(sys.argv[1:]==[],'CLOSED_NO_GO_PARENT_CONSTRUCTION')",text)
