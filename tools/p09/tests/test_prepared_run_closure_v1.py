import copy
import ast
from types import FunctionType,SimpleNamespace as NS
import unittest


class Tests(unittest.TestCase):
    def original_v6_load(self):
        from pathlib import Path
        path="tools/p09/current_queue_closed_metadata_runtime_v6.py"
        root=Path(__file__).resolve().parents[3]
        tree=ast.parse((root/path).read_text(encoding="utf-8"))
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="load")
        env=dict(__name__="p09_exact_v6_epoch_test")
        exec(compile(ast.Module(body=[node],type_ignores=[]),path,"exec"),env)
        return env["load"]

    def test_component_epoch_preserves_complete_original_reader_body(self):
        from types import CodeType
        original=self.original_v6_load();changed=MODULE.component_epoch(original)
        def reverse(value):
            if type(value) is CodeType:return value.replace(co_consts=tuple(reverse(v) for v in value.co_consts))
            if type(value) is tuple:return tuple(reverse(v) for v in value)
            if type(value) is str:return {"runtime-code003":"runtime-code002","worker-code005":"worker-code004"}.get(value,value)
            return value
        self.assertEqual(reverse(changed.__code__),original.__code__)
        self.assertIs(changed.__globals__,original.__globals__)
        self.assertIs(changed.__defaults__,original.__defaults__)
        self.assertIs(changed.__kwdefaults__,original.__kwdefaults__)
        self.assertIs(changed.__closure__,original.__closure__)

    def test_component_epoch_rejects_public_or_already_projected_code(self):
        original=self.original_v6_load()
        public=FunctionType(original.__code__,dict(__name__="public"))
        with self.assertRaises(ValueError):MODULE.component_epoch(public)
        with self.assertRaises(ValueError):MODULE.component_epoch(MODULE.component_epoch(original))
        with self.assertRaises(ValueError):MODULE.component_epoch(MODULE.one_run)

    def test_component_epoch_requires_both_exact_fresh_receipt_selectors(self):
        from types import CodeType
        original=self.original_v6_load()
        def corrupt(value):
            if type(value) is CodeType:return value.replace(co_consts=tuple(corrupt(v) for v in value.co_consts))
            if type(value) is tuple:return tuple(corrupt(v) for v in value)
            return "runtime-code099" if value=="runtime-code002" else value
        broken=FunctionType(corrupt(original.__code__),original.__globals__)
        with self.assertRaises(ValueError):MODULE.component_epoch(broken)

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
