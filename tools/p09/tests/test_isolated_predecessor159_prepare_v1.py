from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_envelope_runtime_v27 as controller
import isolated_predecessor159_prepare_v1 as helper


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=controller.M
        if cls.m.base.CONFIG is None:cls.m.base.configure(160)
        if cls.m.base.CONFIG.index!=160:raise ValueError("TEST_REQUIRES_CURRENT160_CONFIG")
        cls.step=cls.m.base.load_config(159)
    def test_private159_and_default160_separate(self):
        current=self.m.base.CONFIG;facade,_=helper.isolate(controller,self.step)
        self.assertIs(self.m.base.CONFIG,current);self.assertIsNot(facade.base,self.m.base)
        self.assertIs(facade.base.CONFIG,self.step)
    def test_all_original_function_code_defaults_closure_kwdefaults(self):
        facade,proof=helper.isolate(controller,self.step)
        family=self.m.only159.__globals__
        for name in proof["original_function_family_cloned"]:
            original=family[name];private=facade.only159.__globals__[name]
            self.assertIs(private.__code__,original.__code__);self.assertIs(private.__defaults__,original.__defaults__)
            self.assertIs(private.__closure__,original.__closure__);self.assertIs(private.__kwdefaults__,original.__kwdefaults__)
    def test_one_private_family_environment(self):
        facade,proof=helper.isolate(controller,self.step)
        env=facade.only159.__globals__;self.assertIsNot(env,self.m.only159.__globals__)
        for name in proof["original_function_family_cloned"]:self.assertIs(env[name].__globals__,env)
    def test_wrong_or_boolean_prior_step_rejected(self):
        for index,before in ((158,151),(160,153),(True,152),(159,True)):
            with self.subTest(index=index,before=before),self.assertRaises(ValueError):
                helper.isolate(controller,NS(index=index,before=before))
    def test_only_private_only159_check_passes(self):
        facade,_=helper.isolate(controller,self.step);facade.only159()
        with self.assertRaises(ValueError):self.m.only159()
    def test_original_full_admission_not_bypassed(self):
        facade,_=helper.isolate(controller,self.step)
        self.assertIsNot(facade.own_inputs,self.m.own_inputs)
        self.assertIs(facade.API.own_inputs,facade.own_inputs)
        self.assertIs(facade.only159.__globals__["_original_own_inputs"].__globals__["base"],facade.base)
    def test_graph_checkpoint_assignment_private(self):
        facade,_=helper.isolate(controller,self.step);original=self.m.only159.__globals__
        before=(original["_graph"],original["_checkpoint"])
        facade.only159.__globals__.update(_graph=object(),_checkpoint=lambda:None)
        self.assertIs(original["_graph"],before[0]);self.assertIs(original["_checkpoint"],before[1])
    def test_frozen_prepare_prior_CONFIG_and_entire_code_retained(self):
        facade,_=helper.isolate(controller,self.step)
        raw=(self.m.c.ROOT/"tools/p09/flat_current_queue_acceptance.py").read_bytes()
        original=self.m.CURRENT_SOURCE.prepare_projection(raw);private=facade.CURRENT_SOURCE.prepare_projection(raw)
        self.assertEqual(private.__code__,original.__code__);self.assertIs(private.__globals__["r"].CONFIG,self.step)
    def test_no_temporary_swap_replay_or_queue_claim(self):
        _,proof=helper.isolate(controller,self.step)
        for key in ("temporary_CONFIG_swap","default160_config_mutated","current159_runtime_replayed","queue_acceptance_called"):
            self.assertIs(proof[key],False)


if __name__=="__main__":unittest.main()
