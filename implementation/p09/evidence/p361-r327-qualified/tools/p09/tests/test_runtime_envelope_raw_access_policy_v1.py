import builtins
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_envelope_raw_access_policy_v1 as m
from test_runtime_envelope_scope_binding_v1 import fixture

def fixture_policy(active=True,checkpoint=lambda:None,identity=lambda:1):
    binding,*_=fixture();policy=m.Policy(Path.cwd(),binding,lambda:active,checkpoint,identity)
    name=next(iter(binding.originals));return policy,Path.cwd()/name

class Tests(unittest.TestCase):
    def test_all_four_open_APIs_deny_before_real_IO(self):
        policy,path=fixture_policy()
        with policy.install():
            for call in (lambda:path.open("rb"),lambda:io.open(path,"rb"),lambda:builtins.open(path,"rb"),lambda:os.open(path,os.O_RDONLY)):
                with self.assertRaisesRegex(ValueError,"STOP_LIVE_RAW_ENVELOPE_RECEIPT_ACCESS"):call()
        self.assertEqual(policy.raw_attempts,4);self.assertTrue(policy.restored)
    def test_original_owner_guard_exception_identity_precedes_policy_stop(self):
        error=ValueError("ORIGINAL_CPU_RAM_LOCK_STOP")
        def stop():raise error
        policy,path=fixture_policy(checkpoint=stop)
        with self.assertRaises(ValueError) as caught:policy.check_access(path,"Path.open")
        self.assertIs(caught.exception,error);self.assertEqual(policy.raw_attempts,0)
    def test_inactive_metadata_preparation_retains_original_call_arguments(self):
        policy,path=fixture_policy(False);token=object()
        with patch.object(builtins,"open",return_value=token) as original:
            with policy.install():self.assertIs(builtins.open(path,"rb",buffering=0),token)
            original.assert_called_once_with(path,"rb",buffering=0)
        self.assertTrue(policy.restored)
    def test_other_source_and_physical_envelope_are_not_blocked(self):
        policy,path=fixture_policy();binding=policy.binding
        for name in ("crates/current.rs",next(iter(binding.physical))):
            policy.check_access(Path.cwd()/name,"io.open")
        self.assertEqual(policy.raw_attempts,0)
    def test_non_path_descriptor_delegates_unchanged(self):
        policy,path=fixture_policy();token=object()
        with patch.object(builtins,"open",return_value=token) as original:
            with policy.install():self.assertIs(builtins.open(4,"rb",closefd=False),token)
            original.assert_called_once_with(4,"rb",closefd=False)
        self.assertEqual(policy.non_path_calls,1)
    def test_lexical_normalization_handles_relative_path_and_dotdot(self):
        policy,path=fixture_policy();relative=next(iter(policy.binding.originals))
        for name in (relative,Path(relative).parent/"unused"/".."/Path(relative).name):
            with self.assertRaises(ValueError):policy.check_access(name,"os.open")
    def test_body_failure_restores_every_original_API_identity(self):
        policy,path=fixture_policy();before=(Path.open,io.open,builtins.open,os.open);error=OSError("ORIGINAL_BODY_ERROR")
        with self.assertRaises(OSError) as caught:
            with policy.install():raise error
        self.assertIs(caught.exception,error);self.assertEqual((Path.open,io.open,builtins.open,os.open),before)
        self.assertTrue(policy.restored);self.assertFalse(policy.installed)
    def test_nested_install_same_policy_rejected_and_outer_restored(self):
        policy,path=fixture_policy()
        with policy.install():
            with self.assertRaisesRegex(ValueError,"ONE_OWNER_RAW_POLICY_SCOPE"):
                with policy.install():pass
        self.assertTrue(policy.restored)
    def test_nonowner_blocked_without_new_sampler(self):
        owner=[1];sample=[];policy,path=fixture_policy(checkpoint=lambda:sample.append(1),identity=lambda:owner[0]);owner[0]=2
        with self.assertRaises(ValueError):policy.check_access(path,"io.open")
        self.assertEqual(sample,[])
    def test_evidence_never_claims_worker_or_OS_sandbox_qualification(self):
        policy,path=fixture_policy();e=policy.evidence()
        self.assertFalse(e["worker_entry_and_live_parent_connection_qualified"])
        self.assertFalse(e["unwrapped_OS_APIs_or_external_process_access_guarded"])
        self.assertFalse(e["GO_authorized"]);self.assertTrue(e["path_values_or_content_logged"] is False)

if __name__=="__main__":unittest.main()
