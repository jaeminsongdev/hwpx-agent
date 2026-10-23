import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_engine_owned_metadata_entry as m


class Tests(unittest.TestCase):
    def driver(self):
        class Base:
            def __init__(self,attempt,construct_only):
                self.attempt=attempt;self.construct_only=construct_only;self.stage='construction';self.native=None
            def bind(self,*args):pass
            def run(self,*args):return dict(actual_Native_Frame_created=False,actual_product_executed=False)
        return m.driver_type(Base,dict(model=True))()
    def fixture(self):
        owner=NS(phase='NEW',metadata_connection=NS(readers=[],budgets=[]),shared=NS(metadata=None,frame=None))
        data=NS(planned=NS(batch=owner));prepared=NS(linked=NS(state=NS(attempts=0,calls=0)))
        proof=dict(original_engine_owned_assignment_required=True,original_engine_metadata_IO_rates=dict(binary=1048576,other=2097152),
            metadata_factory_connection=dict(engine_assignment_stage=dict(original_engine_assignment_required_before_IO=True),
                entire_original_metadata_factory_and_Router_code_retained=True),reader_allocations_during_connection=0)
        row=dict(metadata_tail_connection=proof,actual_engine_and_checker_same_complete_model=True)
        return data,prepared,row
    def test_one_closed_entry_declares_exact47_controls_and_owns_no_product_mode(self):
        driver=self.driver();control=NS(admit=lambda *args,**kwargs:NS(control_names=tuple(str(i) for i in range(39))))
        driver.bind(None,None,None,None,None,control)
        options=dict(exact_read=True,decoder_timing=True,chunk_join=True,metadata_tail=True)
        declaration=control.admit(None,None,None,**options)
        self.assertEqual(len(declaration.control_names),47);self.assertEqual(declaration.control_names[-8:],m.CONTROLS)
        self.assertEqual(driver.attempt,8);self.assertTrue(driver.construct_only);self.assertEqual(driver.output,m.OUTPUT)
        with self.assertRaises(ValueError):control.admit(None,None,None,**options)
    def test_actual_common_unopened_owner_and_checker_are_required(self):
        driver=self.driver();data,prepared,row=self.fixture();q=NS(final_fresh_hashes=1,snapshots={'model':None})
        result=driver.run(None,q,None,None,None,None,data,prepared,None,None,None,row,None,None)
        self.assertIn('NOT_EXECUTION',result['state']);self.assertFalse(result['GO_authorized'])
        self.assertFalse(result['actual_metadata_body_or_Native_or_worker_or_product_executed'])
        row['actual_engine_and_checker_same_complete_model']=False
        with self.assertRaises(ValueError):driver.run(None,q,None,None,None,None,data,prepared,None,None,None,row,None,None)
    def test_used_reader_frame_or_worker_cannot_qualify_construct_only(self):
        for field in ('reader','frame','worker'):
            driver=self.driver();data,prepared,row=self.fixture();q=NS(final_fresh_hashes=0,snapshots={})
            if field=='reader':data.planned.batch.metadata_connection.readers.append(object())
            elif field=='frame':data.planned.batch.shared.frame=object()
            else:prepared.linked.state.attempts=1
            with self.assertRaises(ValueError):driver.run(None,q,None,None,None,None,data,prepared,None,None,None,row,None,None)
    def test_entry_has_no_native_or_product_dispatch_and_no_whole_audit_replay(self):
        text=(Path(__file__).resolve().parents[3]/m.SELF).read_text(encoding='utf-8');tree=ast.parse(text)
        names={node.func.attr for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)}
        self.assertFalse(names&{'run_owned','begin','Popen','NativePhase','finish_batch','send_GO'})
        self.assertIn("require(sys.argv[1:]==[],'CLOSED_NO_GO_CONSTRUCTION_ENTRY')",text)
