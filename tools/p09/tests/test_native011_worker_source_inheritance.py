"""Parent inheritance transaction models; no child, OS or Native claims."""
from types import SimpleNamespace as NS
import unittest
import native011_worker_source_inheritance as inheritance


class SourceInheritanceContracts(unittest.TestCase):
    def fixture(self):
        values={11:2,22:0};events=[];stamp=[(1,2)]
        class Flags:
            fail=None
            def flags(self,handle):return values[handle]
            def inheritable(self,handle,value):
                events.append((handle,value));values[handle]=(values[handle]&~1)|int(value)
                if self.fail==(handle,value):raise ValueError('MODEL_PARTIAL_SET_FAILURE')
        frame=NS(state='BEFORE_READ',reading=False,check=lambda:None,
            held=NS(acquired=True,closed=False,releasing=False,owned=[
                ('directory',None,33,True),('a',None,11,False),('b',None,22,False)]))
        seen=[]
        coverage=NS(verify=lambda *args,**kwargs:seen.append((args,kwargs)) or dict(exact_whole_worker_pin_coverage=True))
        api=Flags();loan=inheritance.SourceInheritance(frame,{'a':{},'b':{}},coverage,
            frame_type=object,api=api,identity=lambda:stamp[0])
        return loan,frame,api,values,events,stamp,seen

    def test_exact_selected_handles_only_and_original_bits_restored(self):
        loan,frame,api,values,events,stamp,seen=self.fixture()
        self.assertEqual(loan.arm(),(11,22));self.assertEqual(values,{11:3,22:1})
        self.assertTrue(loan.restore());self.assertEqual(values,{11:2,22:0})
        self.assertEqual(seen[0][1]['boundary'],'before')
        self.assertFalse(loan.summary()['actual_child_handle_inheritance_or_two_byte_reads_qualified'])

    def test_partial_set_failure_restores_including_failing_handle_and_never_rearms(self):
        loan,_,api,values,_,_,_=self.fixture();api.fail=(22,True)
        with self.assertRaisesRegex(ValueError,'MODEL_PARTIAL_SET_FAILURE'):loan.arm()
        self.assertEqual(values,{11:2,22:0});self.assertTrue(loan.failed)
        with self.assertRaisesRegex(ValueError,'ONE_ARM_ATTEMPT_ONLY'):loan.arm()

    def test_frame_owner_or_read_boundary_change_denied_before_flags(self):
        for mode in ('owner','reading','boundary'):
            loan,frame,api,values,events,stamp,_=self.fixture()
            if mode=='owner':stamp[0]=(99,2)
            elif mode=='reading':frame.reading=True
            else:frame.state='AFTER_READ'
            with self.assertRaises(ValueError):loan.arm()
            self.assertEqual(events,[])

    def test_preexisting_inheritance_flag_is_not_cleared_or_adopted(self):
        loan,_,_,values,events,_,_=self.fixture();values[22]=1
        with self.assertRaisesRegex(ValueError,'ORIGINAL_NONINHERITABLE_FLAGS'):loan.arm()
        self.assertEqual(values[22],1);self.assertEqual(events,[])

    def test_other_flag_drift_is_not_overwritten_and_cleanup_failure_is_sticky(self):
        loan,_,_,values,_,_,_=self.fixture();loan.arm();values[11]=7
        self.assertFalse(loan.restore());self.assertEqual(values[11],7)
        self.assertTrue(loan.failed);self.assertFalse(loan.summary()['restore_confirmed'])

    def test_closed_owner_or_restored_transaction_cannot_supply_handle_list(self):
        loan,frame,_,_,_,_,_=self.fixture();loan.arm();frame.held.closed=True
        with self.assertRaises(ValueError):loan.handle_list()
        self.assertTrue(loan.restore());frame.held.closed=False
        with self.assertRaises(ValueError):loan.handle_list()

    def test_coverage_refusal_precedes_selection_or_OS_api(self):
        def refused(*args,**kwargs):raise ValueError('ORIGINAL_COVERAGE_REFUSAL')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_COVERAGE_REFUSAL'):
            inheritance.SourceInheritance(None,{},NS(verify=refused),frame_type=object,api=NS())
