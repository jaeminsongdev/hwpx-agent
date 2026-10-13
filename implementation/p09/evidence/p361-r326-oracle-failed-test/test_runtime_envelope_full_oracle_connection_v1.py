import copy
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace as NS,FunctionType
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_envelope_full_oracle_connection_v1 as m
from test_runtime_envelope_scope_binding_v1 import packet

def setup():
    b,semantic,row=packet();row["source_frame"]["frame_state"]="COMMITTED"
    row["source_frame"]["original_owned_cleanup_confirmed_before_release"]=True
    row["original_terminal_predicate"]=True
    def generator(raw,row,listing,body):
        expected=original.scope.extend(body,listing)
        def check(candidate,current,old,fresh,guard):
            guard();expected_again=scope.extend(old,current)
            if expected!=expected_again:raise ValueError("ORIGINAL_SCOPE_DRIFT")
            if not candidate["original_terminal_predicate"]:raise ValueError("ORIGINAL_TERMINAL_FAILURE")
            return dict(original_terminal_checked=True,expected_count=len(expected),model=scope.cost(expected_again,14))
        checker=FunctionType(check.__code__,dict(check.__globals__,scope=ORACLE_SCOPE),closure=check.__closure__)
        return checker,dict(original_proof_preserved=True)
    raw_scope=m.binding_module.source.scope
    old_namespace=NS(scope=raw_scope)
    env=dict(original=old_namespace,ORACLE_SCOPE=raw_scope,mechanics_projection=lambda node:node,FunctionType=FunctionType)
    original=FunctionType(generator.__code__,env)
    def budget(required,requests):return dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,predicted_runtime_combined_seconds=590.0)
    execute,state=m.projector(original,b,budget,lambda:None)
    return b,semantic,row,original,execute,state

class Tests(unittest.TestCase):
    def test_generator_bytecode_and_default_namespace_not_mutated(self):
        b,s,row,original,execute,state=setup();before=dict(original.__globals__)
        check,proof=execute(b"source",row,{},s)
        generated=state.projected_generators[0]
        self.assertIs(generated.__code__,original.__code__);self.assertEqual(original.__globals__,before)
        self.assertTrue(proof["whole_original_checker_code_retained"])
        self.assertTrue(proof["original_proof_preserved"])
    def test_entire_original_checker_and_cost_plus5_are_called(self):
        b,s,row,original,execute,state=setup();check,proof=execute(b"source",row,{},s)
        result=check(row,{},s,None,lambda:None)
        self.assertTrue(result["original_terminal_checked"])
        self.assertEqual(result["model"]["predicted_runtime_combined_seconds"],595.0)
        self.assertEqual(state.observed["original_checker_calls"],1)
        self.assertEqual(state.observed["explicit_scope_checks"],2)
    def test_record_frame_and_counter_bytes_are_not_relabelled(self):
        b,s,row,original,execute,state=setup();before=copy.deepcopy(row)
        check,_=execute(b"source",row,{},s);check(row,{},s,None,lambda:None)
        self.assertEqual(row,before)
    def test_original_failure_is_still_failure(self):
        b,s,row,original,execute,state=setup();row["original_terminal_predicate"]=False
        check,_=execute(b"source",row,{},s)
        with self.assertRaisesRegex(ValueError,"ORIGINAL_TERMINAL_FAILURE"):check(row,{},s,None,lambda:None)
    def test_closed_real_or_fixture_frame_cannot_pass_generator(self):
        b,s,row,original,execute,state=setup();row["source_frame"]["frame_state"]="CLOSED"
        with self.assertRaisesRegex(ValueError,"EXACT_TERMINAL_FRAME_NOT_PROMOTION"):execute(b"source",row,{},s)
    def test_incomplete_semantic_scope_cannot_be_hidden_by_physical_row(self):
        b,s,row,original,execute,state=setup();del s[next(iter(b.originals))]
        with self.assertRaisesRegex(ValueError,"ALL_DECLARED_ORIGINALS_PRESENT"):execute(b"source",row,{},s)
    def test_different_candidate_identity_rejected(self):
        b,s,row,original,execute,state=setup();check,_=execute(b"source",row,{},s)
        with self.assertRaisesRegex(ValueError,"SAME_UNMODIFIED_CANDIDATE_OBJECT"):check(copy.deepcopy(row),{},s,None,lambda:None)
    def test_original_checkpoint_error_identity_preserved(self):
        b,s,row,original,execute,state=setup();error=ValueError("ORIGINAL_GUARD_STOP")
        def stop():raise error
        wrapped,_=m.projector(original,b,lambda *_:None,stop)
        with self.assertRaises(ValueError) as caught:wrapped(b"source",row,{},s)
        self.assertIs(caught.exception,error)
    def test_optional_mechanics_dependency_only_changes_private_generator(self):
        b,s,row,original,execute,state=setup();old=original.__globals__["mechanics_projection"];new=lambda node:node
        wrapped,other=m.projector(original,b,lambda *_:None,lambda:None,mechanics_projection=new)
        wrapped(b"source",row,{},s)
        self.assertIs(other.projected_generators[0].__globals__["mechanics_projection"],new)
        self.assertIs(original.__globals__["mechanics_projection"],old)

if __name__=="__main__":unittest.main()
