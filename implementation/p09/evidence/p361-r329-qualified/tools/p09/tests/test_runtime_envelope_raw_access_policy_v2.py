import builtins
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_envelope_raw_access_policy_v2 as m
from test_runtime_envelope_scope_binding_v1 import fixture


class Tests(unittest.TestCase):
    def test_v1_terminal_latch_obstructs_unrelated_original_receipt_writer(self):
        binding,*_=fixture();armed=[False];error=ValueError("NATIVE_PRESSURE_FAILFAST_STOP_LATCHED_NATIVE_PRESSURE")
        def check():
            if armed[0]:raise error
        policy=m.original.Policy(Path.cwd(),binding,lambda:True,check)
        with policy.install():
            armed[0]=True
            with self.assertRaises(ValueError) as caught:
                policy.check_access("implementation/p09/evidence/p09-361-case158-current-runtime-run001.v1.json","Path.open")
        self.assertIs(caught.exception,error);self.assertTrue(policy.restored)

    def test_v2_original_receipt_open_delegates_after_terminal_source_latch(self):
        binding,*_=fixture();armed=[False];calls=[];token=object()
        def check():
            calls.append(1)
            if armed[0]:raise ValueError("ORIGINAL_TERMINAL_SOURCE_LATCH")
        policy=m.Policy(Path.cwd(),binding,lambda:True,check)
        with patch.object(builtins,"open",return_value=token) as original:
            with policy.install():
                before=len(calls);armed[0]=True
                self.assertIs(builtins.open("implementation/p09/evidence/p09-361-case158-current-runtime-run001.v1.json","x",encoding="utf-8"),token)
                self.assertEqual(len(calls),before)
            original.assert_called_once()
        self.assertTrue(policy.restored)

    def test_mapped_raw_source_still_preserves_original_guard_stop_identity(self):
        binding,*_=fixture();error=ValueError("ORIGINAL_CPU_RAM_SOURCE_STOP")
        def check():raise error
        policy=m.Policy(Path.cwd(),binding,lambda:True,check)
        with self.assertRaises(ValueError) as caught:
            policy.check_access(Path.cwd()/next(iter(binding.originals)),"Path.open")
        self.assertIs(caught.exception,error);self.assertEqual(policy.raw_attempts,0)

    def test_mapped_raw_denied_and_all_original_APIs_restore(self):
        binding,*_=fixture();policy=m.Policy(Path.cwd(),binding,lambda:True,lambda:None)
        with policy.install():
            with self.assertRaisesRegex(ValueError,"STOP_LIVE_RAW"):
                (Path.cwd()/next(iter(binding.originals))).open("rb")
        self.assertEqual(policy.raw_attempts,1);self.assertTrue(policy.restored)


if __name__=="__main__":unittest.main()
