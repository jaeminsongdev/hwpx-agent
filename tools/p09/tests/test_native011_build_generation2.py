"""Generation identities only; no old suite, source audit or compiler rerun."""
from pathlib import Path
import unittest
import native011_current_cohort_plan as plan
import native011_current_cohort_build as build


class GenerationContracts(unittest.TestCase):
    def test_generation2_fresh_target_suffix_and_original_inverse(self):
        root=Path('D:/example');original=['rustc','--target-dir',str(root/plan.OLD_TARGET),
            '--locked','--offline','--jobs','1','--','-C','extra-filename=-p361-case112-r001']
        new=plan.project_recipe(original,root,2)
        self.assertEqual(new[2],str(root/'target/p09-361-native011-current-source-g002'))
        self.assertEqual(new[-1],'extra-filename=-p361-native011-g002')
        self.assertEqual([i for i,(a,b) in enumerate(zip(original,new)) if a!=b],[2,9])
        self.assertEqual(plan.target_for(1),plan.TARGET)

    def test_generation_numbers_cannot_alias_or_expand_without_design(self):
        for value in (0,3,True,'2',None):
            with self.assertRaisesRegex(ValueError,'CLOSED_BUILD_GENERATION'):plan.target_for(value)

    def test_generation2_context_and_original_parser_keep_separate_outputs(self):
        import accept_case112_current_epoch as a,conservative_maintenance as c
        import stored_test_profile81 as profile,signed_durable_build_stream as stream
        selected,pin=build.generation_context(plan,2)
        self.assertEqual(pin,build.PLAN2)
        self.assertNotEqual(pin['path'],build.PLAN['path'])
        self.assertNotEqual(selected.TARGET,plan.TARGET)
        raw=(c.ROOT/plan.BUILD).read_text(encoding='utf-8')
        module=build.definitions(raw,a,c,profile,stream,selected)
        original=a.native.definitions(raw,('require','task_for','recipe'),dict(profile=profile,
            TARGET=c.ROOT/plan.OLD_TARGET,ARGS=['rustc','-p','hwpx-agent-cli','--test','form_stored_provider','--profile','test']))
        self.assertEqual(module.recipe(2),plan.project_recipe(original.recipe(1),c.ROOT,2))
        self.assertEqual(module.executable_name(2),selected.TARGET+'/debug/deps/form_stored_provider-p361-native011-g002.exe')


if __name__=='__main__':unittest.main()
