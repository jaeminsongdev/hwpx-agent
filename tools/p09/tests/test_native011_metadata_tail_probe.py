import ast
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
import native011_metadata_tail_probe as m


class Tests(unittest.TestCase):
    def test_driver_declares_six_explicit_roles_once_and_is_construct_only(self):
        class Base:
            def __init__(self,attempt,construct_only):self.attempt=attempt;self.construct_only=construct_only
            def bind(self,*args):pass
        control=NS(admit=lambda *args,**kwargs:NS(control_names=tuple(str(i) for i in range(35))))
        driver=m.driver_type(Base)();driver.bind(None,None,None,None,None,control)
        declaration=control.admit(None,None,None,exact_read=True,decoder_timing=True,chunk_join=True)
        self.assertEqual(declaration.control_names[-6:],m.CONTROLS);self.assertEqual(len(declaration.control_names),41)
        self.assertEqual(driver.attempt,7);self.assertTrue(driver.construct_only);self.assertEqual(driver.output,m.OUTPUT)
        with self.assertRaises(ValueError):control.admit(None,None,None,exact_read=True,decoder_timing=True,chunk_join=True)

    def test_driver_component_uses_separate_reader_not_constructor_input_credit(self):
        class Base:
            def __init__(self,attempt,construct_only):
                self.construct_only=construct_only;self.stage='construction';self.native=None;self.check=lambda **kwargs:None
            def run(self,*args):return dict(actual_Native_Frame_created=False,actual_product_executed=False)
        driver=m.driver_type(Base)();constructor=object();component=object()
        a=NS(AcceptanceReader=lambda *args:component);owner=object();prepared=object()
        data=NS(planned=NS(batch=owner))
        with patch.object(m,'component',return_value={'bounded_component':True}) as call:
            result=driver.run(None,constructor,a,None,None,None,data,prepared,None,None,None,{},None,None)
        self.assertIs(call.call_args.args[1],component);self.assertIsNot(call.call_args.args[1],constructor)
        self.assertFalse(result['actual_Native_Frame_created']);self.assertFalse(result['actual_product_executed'])
        self.assertIn('NOT_FULL_CALLBACK_OR_NATIVE',result['state'])

    def test_reused_component_reader_refused_before_any_component_loading(self):
        with self.assertRaisesRegex(ValueError,'SEPARATE_UNUSED_COMPONENT'):
            m.component(None,NS(read_passes=1),None,None,None,None)

    def test_closed_entry_has_no_product_go_subprocess_or_native_phase_entry(self):
        text=(Path(__file__).resolve().parents[3]/m.SELF).read_text(encoding='utf-8')
        tree=ast.parse(text)
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call)]
        self.assertFalse(any(isinstance(node.func,ast.Attribute) and node.func.attr in ('Popen','run_owned','begin') for node in calls))
        self.assertIn("require(sys.argv[1:] in ([],['--engine-owned']),'CLOSED_NO_GO_ENTRY')",text)

    def test_engine_owned_mode_declares_all_ten_named_sources_without_product_mode(self):
        class Base:
            def __init__(self,attempt,construct_only):self.attempt=attempt;self.construct_only=construct_only
            def bind(self,*args):pass
        control=NS(admit=lambda *args,**kwargs:NS(control_names=tuple(str(i) for i in range(35))))
        driver=m.driver_type(Base,engine_owned=True)();driver.bind(None,None,None,None,None,control)
        declaration=control.admit(None,None,None,exact_read=True,decoder_timing=True,chunk_join=True)
        self.assertEqual(len(declaration.control_names),45)
        self.assertEqual(declaration.control_names[-10:],m.CONTROLS+m.OWNED_CONTROLS)
        self.assertEqual(driver.output,m.OWNED_OUTPUT);self.assertTrue(driver.construct_only)
        with self.assertRaises(ValueError):m.driver_type(Base,engine_owned=1)
