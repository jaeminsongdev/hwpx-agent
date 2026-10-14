"""Successor selection predicates, no writer or product execution."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("next_step",Path(__file__).parents[1]/"prepare_current_queue_step.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class Tests(unittest.TestCase):
    def inputs(self):
        names=[f"test_{i:03}" for i in range(249)]
        pin=dict(path="implementation/p09/evidence/p09-361-case160-current-epoch-accept001.v1.json",bytes=1,sha256="a"*64)
        authority=dict(state="PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE",accepted_count_after=154,
            next_runtime_index=161,accepted_count_delta=1,accepted_test_indices=[160],resource_cleanup_confirmed=True,
            P09_gate="OPEN",full249_current_qualified=False,signed16_current_qualified=False,P10_started=False,
            runtime_candidate_pin=dict(path="prior",bytes=1,sha256="b"*64))
        prior=dict(state="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",selected_test_index=160,
            cleanup_confirmed=True,owned_tree_empty=True,Native_source_frame_qualified=True,current_generation_runtime_candidate_qualified=True,
            source_frame=dict(frame_state="COMMITTED",actual_byte_boundaries=[{},{}]),selected_test_names=[names[159]])
        return [161,pin,authority,prior,names]

    def test_exact_successor_selection(self):
        result=module.derive_step(*self.inputs())
        self.assertEqual((result["index"],result["before"],result["case"]),(161,154,"test_160"))

    def test_bad_authority_or_gate_rejected(self):
        for key,value in (("accepted_count_after",153),("accepted_count_delta",0),("resource_cleanup_confirmed",False),
                          ("next_runtime_index",162),("state","PREPARED"),("P10_started",True)):
            args=self.inputs();args[2][key]=value
            with self.assertRaises(ValueError):module.derive_step(*args)

    def test_partial_predecessor_or_wrong_name_rejected(self):
        for edit in (lambda p:p.update(cleanup_confirmed=False),lambda p:p.update(selected_test_names=["wrong"]),
                     lambda p:p["source_frame"].update(actual_byte_boundaries=[{}]),lambda p:p["source_frame"].update(frame_state="CLOSED")):
            args=self.inputs();edit(args[3])
            with self.assertRaises(ValueError):module.derive_step(*args)

    def test_closed_index_and_full_roster_required(self):
        for index in (True,160,250,161.0,"161"):
            args=self.inputs();args[0]=index
            with self.assertRaises(ValueError):module.derive_step(*args)
        for names in ([],self.inputs()[-1][:-1],list(reversed(self.inputs()[-1]))):
            args=self.inputs();args[-1]=names
            with self.assertRaises(ValueError):module.derive_step(*args)


if __name__=="__main__":unittest.main()
