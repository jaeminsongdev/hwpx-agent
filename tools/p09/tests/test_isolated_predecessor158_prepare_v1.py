from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_envelope_runtime_v25 as old
import isolated_predecessor158_prepare_v1 as m


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if old.base.CONFIG is None:old.base.configure(159)
        if old.base.CONFIG.index!=159 or old.base.CONFIG.before!=152:
            raise ValueError("TEST_REQUIRES_CURRENT159_CONFIG")
        cls.step=old.base.load_config(158)
    def test_real_private158_and_default159_separate(self):
        current=old.base.CONFIG;facade,proof=m.isolate(old,self.step)
        self.assertIs(old.base.CONFIG,current)
        self.assertIsNot(facade.base,old.base)
        self.assertIs(facade.base.CONFIG,self.step)
        self.assertEqual(old.base.CONFIG.index,159)
    def test_original_function_code_defaults_closure_and_kwdefaults_retained(self):
        facade,proof=m.isolate(old,self.step)
        for name in proof["original_function_family_cloned"]:
            original=getattr(old,name);private=getattr(facade,name)
            self.assertIs(private.__code__,original.__code__)
            self.assertIs(private.__defaults__,original.__defaults__)
            self.assertIs(private.__closure__,original.__closure__)
            self.assertIs(private.__kwdefaults__,original.__kwdefaults__)
    def test_private_family_globals_are_one_separate_environment(self):
        facade,proof=m.isolate(old,self.step)
        env=facade.only158.__globals__
        self.assertIsNot(env,old.only158.__globals__)
        for name in proof["original_function_family_cloned"]:
            self.assertIs(getattr(facade,name).__globals__,env)
        self.assertIs(env["base"],facade.base)
    def test_guard_requires_actual_prior158(self):
        from types import SimpleNamespace as NS
        for index,before in ((157,150),(159,152),(True,151),(158,True)):
            with self.subTest(index=index,before=before),self.assertRaises(ValueError):
                m.isolate(old,NS(index=index,before=before))
    def test_old_exact158_check_remains_and_only_private_config_passes(self):
        facade,_=m.isolate(old,self.step)
        facade.only158()
        with self.assertRaises(ValueError):old.only158()
    def test_own_admission_uses_private_original_callback(self):
        facade,_=m.isolate(old,self.step)
        self.assertIsNot(facade.own_inputs,old.own_inputs)
        self.assertIs(facade.API.own_inputs,facade.own_inputs)
        self.assertIs(facade._original_own_inputs.__globals__["base"],facade.base)
        self.assertIsNot(facade.API,old.API)
    def test_binding_checkpoint_initial_state_not_shared_assignment(self):
        facade,_=m.isolate(old,self.step)
        before=(old._binding,old._checkpoint)
        env=facade.only158.__globals__;env["_binding"]=object();env["_checkpoint"]=lambda:None
        self.assertIs(old._binding,before[0]);self.assertIs(old._checkpoint,before[1])
    def test_no_product_or_GO_or_temporary_config_swap_claim(self):
        _,proof=m.isolate(old,self.step)
        for key in ("original_current_CONFIG_mutated","temporary_CONFIG_swap_used",
                    "actual_product_or_Native_replayed","queue_acceptance_called"):
            self.assertIs(proof[key],False)
    def test_frozen_prepare_has_private_prior_config_not_current159(self):
        facade,_=m.isolate(old,self.step)
        raw=(old.c.ROOT/"tools/p09/flat_current_queue_acceptance.py").read_bytes()
        original=old.CURRENT_SOURCE.prepare_projection(raw)
        private=facade.CURRENT_SOURCE.prepare_projection(raw)
        self.assertEqual(private.__code__,original.__code__)
        self.assertIs(private.__globals__["r"].CONFIG,self.step)
        self.assertEqual(old.base.CONFIG.index,159)


if __name__=="__main__":unittest.main()
