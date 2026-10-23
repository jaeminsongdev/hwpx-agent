"""New source-generation plan contracts; no Cargo, products or live source audit."""
from pathlib import Path
import unittest
import native011_current_cohort_plan as plan


class CohortContracts(unittest.TestCase):
    def fixture(self):
        names=sorted(plan.CHANGED)+[f'crates/x/src/f{i}.rs' for i in range(782)]
        old={n:dict(path=n,bytes=10,sha256='a'*64) for n in names}
        changes=[dict(path=n,declared=old[n],observed=dict(old[n],bytes=11)) for n in sorted(plan.CHANGED)]
        adds=[dict(path=f'crates/new/src/f{i}.rs',bytes=12,sha256='b'*64) for i in range(18)]
        return old,dict(changed=changes,added=adds,unobserved_compiled=[],
            current_live_freshness_qualified=False,closing_boundary_qualified=False)

    def test_exact_cohort_preserves_original_and_separates_live23_from_historical782(self):
        old,comparison=self.fixture();result,delta=plan.reconcile(old,comparison)
        self.assertEqual((len(result),len(delta)),(805,23))
        self.assertTrue(all(old[n]['bytes']==10 and result[n]['bytes']==11 for n in plan.CHANGED))
        self.assertFalse(comparison['closing_boundary_qualified'])

    def test_addition_cannot_replace_an_existing_input(self):
        old,comparison=self.fixture();comparison['added'][0]=dict(next(iter(old.values())))
        with self.assertRaisesRegex(ValueError,'NO_ADDITION_OVERWRITE'):plan.reconcile(old,comparison)

    def test_unobserved_or_promoted_failure_rejected(self):
        old,comparison=self.fixture();comparison['unobserved_compiled']=['missing']
        with self.assertRaisesRegex(ValueError,'ORIGINAL787_OBSERVED'):plan.reconcile(old,comparison)
        comparison['unobserved_compiled']=[];comparison['closing_boundary_qualified']=True
        with self.assertRaisesRegex(ValueError,'RECOVERY_NOT_PROMOTED'):plan.reconcile(old,comparison)

    def test_recipe_changes_only_two_identities_no_run_command_or_clock(self):
        root=Path('D:/example');old=['rustc','--target-dir',str(root/plan.OLD_TARGET),
            '--locked','--offline','--jobs','1','--','-C','extra-filename=-p361-case112-r001']
        result=plan.project_recipe(old,root)
        self.assertEqual([i for i,(a,b) in enumerate(zip(old,result)) if a!=b],[2,9])
        self.assertEqual(old[-1],'extra-filename=-p361-case112-r001')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_RECIPE_IDENTITIES'):
            plan.project_recipe(['test',*old[1:9],'unexpected'],root)


if __name__=='__main__':unittest.main()
