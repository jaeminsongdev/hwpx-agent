import copy
import ast
from types import FunctionType,SimpleNamespace as NS
import unittest


class Tests(unittest.TestCase):
    def data(self):
        p=MODULE.PREFIX;run=5
        pin=lambda path:dict(path=path,bytes=1,sha256="a"*64)
        return dict(state=MODULE.STATE,index=165,physical_run=run,cleanup_confirmed=True,
            accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False,
            actual_Native_absent_before=True,actual_Native_absent_after=True,source_profile_version="v9",
            fresh_inputs=5,final_fresh_hashes=5,worker_entry_pin=dict(MODULE.ENTRY),
            graph_pin=pin(p+"successor-connections005.v9.json"),capsule_pin=pin(p+"successor-worker-capsule005.compact.v9.json"),
            bootstrap_pin=pin(p+"successor-worker-bootstrap005.v9.json"),
            no_go_probe=dict(exit_code=1,original_GO_rejection_observed=True,historical_runtime_or_authority_opens=0,
                GO_sent=False,product_child_execution_authorized=False))

    def test_valid_preparation_only_is_not_Native_pass(self):
        row=self.data();MODULE.validate(row,165,5,API)
        self.assertFalse(row["product_or_Native_executed"])
        # Match v4's late generic role-metadata rewrite, after installing a
        # function from this adapter in the private retry namespace.
        env=dict(MODULE.producer_inventory.__globals__,__name__="p09_exact_role_rewrite_regression")
        fn=FunctionType(MODULE.producer_inventory.__code__,env)
        retry=NS(previous_stops=fn)
        for installed in vars(retry).values():
            if type(installed) is FunctionType and installed.__globals__.get("__name__","").startswith("p09_exact_"):
                installed.__globals__.update(SELF="legacy-role.py",TEST="legacy-role-test.py")
        pins=[dict(path=MODULE.CLOSURE_SOURCE),dict(path=MODULE.CLOSURE_TEST)]
        self.assertEqual(set(fn(dict(source_pins=pins))),{MODULE.CLOSURE_SOURCE,MODULE.CLOSURE_TEST})
        with self.assertRaises(ValueError):fn(dict(source_pins=[dict(path="legacy-role.py"),dict(path="legacy-role-test.py")]))

    def test_wrong_context_or_claimed_product_rejected(self):
        for key,value in (("physical_run",6),("product_or_Native_executed",True),("GO_authorized",True),("cleanup_confirmed",False)):
            row=self.data();row[key]=value
            with self.assertRaises(ValueError):MODULE.validate(row,165,5,API)

    def test_no_go_must_be_actual_and_no_history_IO(self):
        for key,value in (("exit_code",0),("original_GO_rejection_observed",False),("historical_runtime_or_authority_opens",1),("GO_sent",True)):
            row=self.data();row["no_go_probe"][key]=value
            with self.assertRaises(ValueError):MODULE.validate(row,165,5,API)

    def test_absence_closing_hash_and_packet_identity_required(self):
        for key,value in (("actual_Native_absent_after",False),("final_fresh_hashes",4),("worker_entry_pin",MODULE.OLD)):
            row=self.data();row[key]=value
            with self.assertRaises(ValueError):MODULE.validate(row,165,5,API)

    def test_single_range_projection_retains_complete_original_body(self):
        env=dict(__name__="p09_exact_retry_test")
        exec("def previous_stops(q,ctx,a,bridge):\n for run in range(2,ctx.run):q.append(run)\n",env)
        original=env["previous_stops"];projected=MODULE.one_run(original,5);seen=[]
        projected(seen,NS(run=6),None,None)
        self.assertEqual(seen,[5]);self.assertIs(projected.__defaults__,original.__defaults__)
        self.assertEqual(original.__code__.co_consts,(None,2))

    def test_unbound_or_ambiguous_projection_rejected(self):
        def template(q,ctx,a,bridge):return 2
        public=FunctionType(template.__code__,{"__name__":"public_retry_test"})
        with self.assertRaises(ValueError):MODULE.one_run(public,5)
        env=dict(__name__="p09_exact_retry_test")
        exec("def f(q,ctx,a,bridge):\n return 2,5\n",env)
        with self.assertRaises(ValueError):MODULE.one_run(env["f"],5)
        from pathlib import Path
        root=Path(MODULE.__file__)
        tree=ast.parse(root.read_text(encoding="utf-8"))
        main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="main")
        eager={alias.name for node in main.body if isinstance(node,ast.Import) for alias in node.names}
        publication={"terminal_metadata_pressure_v1","distinct_final_sample_guard_v1","successor_preparation_workspace_v1"}
        self.assertFalse(eager & publication)
        branch=next(node for node in main.body if isinstance(node,ast.If))
        lazy={alias.name for node in branch.body if isinstance(node,ast.Import) for alias in node.names}
        self.assertTrue(publication <= lazy)
