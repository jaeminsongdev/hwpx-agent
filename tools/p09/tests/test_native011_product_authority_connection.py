from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import native011_product_authority_connection as m
import native011_product_parent_handoff as parent
import test_native011_product_parent_handoff as fixture


class Tests(unittest.TestCase):
    def raw(self):return (Path(__file__).resolve().parents[3]/m.SOURCE['path']).read_bytes()
    def projected_fixture(self,authorize=None):
        before=parent.driver_type;selected,proof=m.project(self.raw(),parent,authorize=authorize)
        with patch.object(parent,'driver_type',selected):value=fixture.Tests().driver_fixture()
        self.assertIs(parent.driver_type,before);value.projection=proof
        value.control.admit(None,None,None);return value

    def test_entire_original_driver_inverse_only_two_dependency_and_evidence_sites(self):
        before=parent.driver_type;selected,proof=m.project(self.raw(),parent)
        self.assertTrue(proof['entire_original_driver_AST_inverse']);self.assertEqual(proof['exact_changed_sites'],dict(install=1,evidence=1))
        self.assertIsNot(selected,before);self.assertIs(parent.driver_type,before)
        self.assertFalse(proof['external_authority_supplied']);self.assertFalse(proof['GO_authorized'])
        self.assertTrue(proof['original_install_and_execute_Job_Frame_READY15_window10_code_retained'])

    def test_default_original_route_denies_before_job_frame_process_or_io(self):
        f=self.projected_fixture();out=f.run()
        self.assertFalse(out['actual_parent_handoff_connection']['authorization_dependency_present'])
        with self.assertRaisesRegex(ValueError,'EXTERNAL_NATIVE_GO_AUTHORITY_REQUIRED'):f.f.actual.run_owned(1)
        self.assertEqual(f.f.journal,[]);self.assertEqual(f.f.owner.parent_connection.state.frames,[])
        self.assertEqual(f.driver.parent_handoff.state.attempts,0)

    def test_false_external_dependency_is_called_only_at_execution_and_still_denies(self):
        calls=[];f=self.projected_fixture(lambda:(calls.append(1) or False));out=f.run()
        self.assertEqual(calls,[]);self.assertTrue(out['actual_parent_handoff_connection']['authorization_dependency_present'])
        with self.assertRaisesRegex(ValueError,'EXTERNAL_NATIVE_GO_AUTHORITY_REQUIRED'):f.f.actual.run_owned(1)
        self.assertEqual(calls,[1]);self.assertEqual(f.f.journal,[]);self.assertEqual(f.driver.parent_handoff.state.attempts,0)

    def test_explicit_dependency_reaches_original_execute_closure_without_being_consumed(self):
        calls=[]
        def external():calls.append(1);return True
        with patch.object(parent,'install',wraps=parent.install) as install:
            f=self.projected_fixture(external);out=f.run()
        install.assert_called_once();self.assertEqual(install.call_args.kwargs,dict(authorize=external))
        self.assertIs(parent.closure(f.f.actual.run_owned)['authorize'],external)
        self.assertEqual(calls,[]);self.assertEqual(f.f.journal,[])
        self.assertFalse(out['actual_parent_handoff_connection']['GO_authorized'])

    def test_changed_source_function_or_boolean_approval_flag_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_SOURCE'):m.project(self.raw()+b' ',parent)
        for value in (True,False,1,'approved'):
            with self.assertRaisesRegex(ValueError,'EXPLICIT_EXTERNAL_DEPENDENCY'):m.project(self.raw(),parent,authorize=value)
        with patch.object(parent,'driver_type',lambda base:base):
            with self.assertRaises(ValueError):m.project(self.raw(),parent)

    def wrapper(self,*,fail=False):
        calls=[];pins={name:dict(path=name,bytes=2,sha256='0'*64) for name in (m.SELF,m.TEST)}
        reader=NS(snapshots={},final_fresh_hashes=0,checkpoint=lambda:calls.append('guard'))
        def pin(name):reader.snapshots[name]=pins[name];return pins[name]
        def finish():
            calls.append('closing2')
            if fail:raise ValueError('MODEL_AUTHORITY_CLOSING_CHANGED')
            reader.final_fresh_hashes=len(reader.snapshots)
        reader.pin=pin;reader.finish=finish
        evidence=dict(execution_attempts=0,component_connections=0,original_owner=dict(observed_original_Jobs=0),authorization_dependency_present=False)
        class Base:
            def __init__(self):self.construct_only=True;self.native=None;self.parent_handoff=NS(evidence=lambda:evidence)
            def bind(self,*args):pass
            def run(self,*args):calls.append('original-construction');return dict(GO_authorized=False)
        _,proof=m.project(self.raw(),parent);driver=m.driver_type(Base,proof)()
        control=NS(admit=lambda *args,**kwargs:NS(control_names=tuple('base'+str(i) for i in range(70))))
        driver.bind(None,None,None,None,None,control)
        q=NS(checkpoint=lambda:None,finish=lambda:(_ for _ in ()).throw(AssertionError('NO_ORIGINAL_LEDGER_REPLAY')))
        a=NS(AcceptanceReader=lambda *args:reader,exact=lambda actual,expected,label:self.assertEqual(actual,expected))
        data=NS(planned=NS(current=pins))
        return NS(driver=driver,control=control,calls=calls,reader=reader,
            run=lambda:driver.run(Path('model-root'),q,a,None,None,None,data,None,None,None,None,{},None,None))

    def test_wrapper_names_exact72_roles_once_and_closes_two_new_inputs_not_old_ledger(self):
        f=self.wrapper();declared=f.control.admit(None,None,None)
        self.assertEqual(len(declared.control_names),72);self.assertEqual(declared.control_names[-2:],(m.SELF,m.TEST))
        with self.assertRaisesRegex(ValueError,'ONE_EXPLICIT_AUTHORITY_CONTROL_DECLARATION'):f.control.admit(None,None,None)
        out=f.run();self.assertEqual(f.calls,['original-construction','closing2','guard'])
        self.assertEqual(out['product_authority_connection']['connection_fresh_inputs'],2)
        self.assertFalse(out['product_authority_connection']['actual_Native_or_product_or_GO_or_intent_executed'])

    def test_wrapper_cannot_claim_success_after_current_closing_failure(self):
        f=self.wrapper(fail=True);f.control.admit(None,None,None)
        with self.assertRaisesRegex(ValueError,'MODEL_AUTHORITY_CLOSING_CHANGED'):f.run()
        self.assertEqual(f.reader.final_fresh_hashes,0)

    def test_same_authority_evidence_required_for_wrapper_and_no_claim_before_declaration(self):
        _,proof=m.project(self.raw(),parent)
        with self.assertRaisesRegex(ValueError,'SAME_EXPLICIT_AUTHORITY_DEPENDENCY'):m.driver_type(object,proof,authorize=lambda:True)
        f=self.wrapper()
        with self.assertRaisesRegex(ValueError,'SAME_ORIGINAL_PRODUCT_ROUTE_INERT'):f.run()

    def test_cli_default_only_constructs_and_rejects_product_no_go_retry_or_runtime_flags(self):
        with patch.object(sys,'argv',['authority.py']),patch.object(m,'construct',return_value=17) as construct:
            self.assertEqual(m.main(),17);construct.assert_called_once()
        for args in (['--go'],['--whole-no-go'],['--runtime'],['--attempt','1']):
            with patch.object(sys,'argv',['authority.py',*args]),patch.object(m,'construct',side_effect=AssertionError('NO_EXECUTION')):
                with self.assertRaisesRegex(ValueError,'CONSTRUCTION_ONLY_NO_GO_OR_RUNTIME_ARGUMENTS'):m.main()

    def test_construct_rejects_approval_flags_or_canonical_runtime_output_before_bootstrap(self):
        for options in (dict(authorize=True),dict(wrap=True),dict(output='D:/outside.json'),
                dict(output='implementation/p09/evidence/p09-361-case165-current-runtime-run011.v1.json'),
                dict(output='implementation/p09/evidence/p09-361-native011-other.v1.json')):
            with self.assertRaises(ValueError):m.construct(**options)


if __name__=='__main__':unittest.main()
