"""New mandatory-outer-input contracts; no old suite, corpus or Native run."""
import copy
from types import SimpleNamespace as NS
import unittest
import batch_verification as batch
import native011_parent_plan as parent


class IntrinsicPartitionContracts(unittest.TestCase):
    def fixture(self):
        names=('implementation/p09/evidence/p09-361-case112-current-runtime-run001.v1.json',
            'implementation/p09/evidence/p09-361-case112-current-runtime-run003.v1.json')
        required={n:dict(path=n,bytes=b,sha256=s) for n,b,s in zip(names,(3720,56097),(
            '8c26646fe69111b5429f33ee53f13c044d2d3d45828d8141e15c3f7252e3f7e2',
            '1fd05236e9c1a56be7402a708e4372e154f957e617cf6286bd1ef0ef6356c470'))}
        hot=dict(path='tools/p09/control.py',bytes=1,sha256='a'*64)
        cold=dict(path='implementation/p09/evidence/p09-361-case164-current-runtime-run001.v1.json',
            bytes=1,sha256='b'*64)
        current={hot['path']:hot};history={**copy.deepcopy(required),cold['path']:cold}
        whole={**current,**history};owner=batch.Batch(whole,current,history,first_index=165,checkpoint=lambda:None)
        return NS(batch=owner,current=current,history=history,whole=whole,logical=copy.deepcopy(whole)),required

    def test_exact_two_outer_inputs_and_all_other_history_retained(self):
        plan,required=self.fixture();before=copy.deepcopy((plan.current,plan.history,plan.whole,plan.logical))
        result,proof=parent.bind_intrinsic_failures(plan,required,batch,lambda:None)
        self.assertEqual(result.whole,plan.whole);self.assertEqual(result.logical,plan.logical)
        self.assertEqual(len(result.history),1);self.assertEqual(len(result.current),3)
        self.assertTrue(all(result.current[n]==p for n,p in required.items()))
        self.assertEqual((plan.current,plan.history,plan.whole,plan.logical),before)
        self.assertEqual((proof['preservation_before'],proof['preservation_after']),(3,1))
        self.assertIs(type(result.batch),batch.Batch);self.assertEqual(result.batch.phase,'NEW')

    def test_changed_pin_or_arbitrary_promotion_rejected(self):
        for mode in ('changed','other'):
            plan,required=self.fixture();bad=copy.deepcopy(required)
            if mode=='changed':next(iter(bad.values()))['bytes']+=1
            else:bad.update({n:p for n,p in plan.history.items() if n not in required})
            with self.assertRaisesRegex(ValueError,'ONLY_TWO_EXACT_INTRINSIC_FAILURE_PINS'):
                parent.bind_intrinsic_failures(plan,bad,batch,lambda:None)

    def test_opened_plan_rejected(self):
        plan,required=self.fixture();plan.batch.phase='READY'
        with self.assertRaisesRegex(ValueError,'BEFORE_ANY_BATCH_OPEN'):
            parent.bind_intrinsic_failures(plan,required,batch,lambda:None)

    def test_inconsistent_raw_history_pin_rejected(self):
        plan,required=self.fixture();plan.logical[next(iter(required))]['bytes']+=1
        with self.assertRaisesRegex(ValueError,'EXACT_TWO_PRESERVED_RAW_INPUTS'):
            parent.bind_intrinsic_failures(plan,required,batch,lambda:None)


if __name__=='__main__':unittest.main()
