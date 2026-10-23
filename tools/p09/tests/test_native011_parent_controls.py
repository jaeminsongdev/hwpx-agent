"""New entry declarations and whole bootstrap; no Native construction."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import unittest
import batch_verification as batch
import native011_parent_plan as plan


def pin(name):return dict(path=name,bytes=1,sha256='a'*64)


class ParentControlsContracts(unittest.TestCase):
    def fixture(self):
        hot=pin('tools/p09/original.py')
        cold=pin('implementation/p09/evidence/p09-361-case164-current-runtime-run001.v1.json')
        current={hot['path']:hot};history={cold['path']:cold};whole={**current,**history}
        owner=batch.Batch(whole,current,history,first_index=165,checkpoint=lambda:None)
        return NS(batch=owner,current=current,history=history,whole=whole,logical=copy.deepcopy(whole))

    def test_whole_original_bootstrap_does_not_register_or_hide_default_modules(self):
        before=dict(sys.modules);root=Path(__file__).resolve().parents[3]
        loader=plan.bootstrap_loader(root)
        self.assertEqual(loader.SELF,'tools/p09/runtime_envelope_namespace_bundle_v1.py')
        self.assertTrue(callable(loader.load));self.assertTrue(callable(loader.require))
        self.assertIs(sys.modules.get('runtime_envelope_namespace_bundle_v1'),before.get('runtime_envelope_namespace_bundle_v1'))
        self.assertTrue(all(sys.modules.get(n) is m for n,m in before.items()))

    def test_two_explicit_controls_retain_original_plan_and_cold_partition(self):
        old=self.fixture();before=copy.deepcopy((old.whole,old.current,old.history,old.logical))
        controls={n:pin(n) for n in plan.PARENT_CONTROLS}
        new,proof=plan.bind_parent_controls(old,controls,batch,lambda:None)
        self.assertEqual(new.history,old.history);self.assertEqual(len(new.current),3)
        self.assertEqual((old.whole,old.current,old.history,old.logical),before)
        self.assertTrue(proof['preservation_unchanged']);self.assertIs(type(new.batch),batch.Batch)

    def test_undeclared_extra_control_or_reapplication_rejected(self):
        old=self.fixture();controls={n:pin(n) for n in plan.PARENT_CONTROLS}
        with self.assertRaisesRegex(ValueError,'EXPLICIT_PARENT_ENTRY'):
            plan.bind_parent_controls(old,{**controls,'tools/p09/extra.py':pin('tools/p09/extra.py')},batch,lambda:None)
        new,_=plan.bind_parent_controls(old,controls,batch,lambda:None)
        with self.assertRaisesRegex(ValueError,'NO_CONTROL_REPLACEMENT'):
            plan.bind_parent_controls(new,controls,batch,lambda:None)

    def test_started_plan_cannot_change_runtime_controls(self):
        old=self.fixture();old.batch.phase='READY'
        with self.assertRaisesRegex(ValueError,'BEFORE_ANY_BATCH_OPEN'):
            plan.bind_parent_controls(old,{plan.SELF:pin(plan.SELF)},batch,lambda:None)


if __name__=='__main__':unittest.main()
