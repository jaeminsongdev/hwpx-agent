"""Closed private import map and unchanged function code."""
from pathlib import Path
import ast
import copy
from types import FunctionType,SimpleNamespace as NS
import sys
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import current_queue_successor_wire_runtime_v2 as m


class Tests(unittest.TestCase):
    def test_private_imports_keep_code_and_shared_builtins(self):
        def original():
            import explicit_fixture_dependency
            return explicit_fixture_dependency
        env=dict(original.__globals__,__name__="p09_exact_fixture")
        fn=FunctionType(original.__code__,env)
        namespace=NS(original=fn);value=object()
        import builtins
        before=builtins.__import__
        m.bind_imports(namespace,dict(explicit_fixture_dependency=value))
        self.assertIs(namespace.original.__code__,fn.__code__)
        self.assertIs(namespace.original(),value)
        self.assertIs(builtins.__import__,before)
        self.assertNotIn("explicit_fixture_dependency",sys.modules)
        def fields(row,values,label):
            if any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in values.items()):raise ValueError(label)
        api=NS(fields=fields,require=m.require)
        row=dict(state="DEFERRED_NOT_STARTED",task="case162-current-r002-tests",worker_created=False,
            product_body_observed=False,actual_product_child_executed=False,cleanup_confirmed=True,owned_tree_empty=True,
            accepted_count_delta=0,current_generation_runtime_candidate_qualified=False,Native_source_frame_qualified=False,
            passed_test_names=[],stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",source_frame=dict(frame_state="CLOSED",
                registered_live_frame=False,actual_byte_boundaries=[],handles=dict(input_lock_handles_remaining=0,
                    input_lock_cleanup_confirmed=True,active_reader_bindings=0,active_byte_streams=0,handle_close_failed_attempts=0,
                    file_write_or_delete_operation_executed=False,input_lock_handles_opened=2,input_lock_handles_closed=2)),
            parent_live_raw_access_policy=dict(active_scope=False,all_original_open_function_identities_restored=True))
        self.assertTrue(m.closed_prebody_stop(row,162,2,api))
        for mutate in (lambda r:r.update(product_body_observed=True),
            lambda r:r["source_frame"]["handles"].update(input_lock_handles_closed=1),
            lambda r:r["source_frame"]["handles"].update(active_byte_streams=1),
            lambda r:r["source_frame"].update(actual_byte_boundaries=[{}]),
            lambda r:r["parent_live_raw_access_policy"].update(active_scope=True)):
            bad=copy.deepcopy(row);mutate(bad)
            with self.assertRaises(ValueError):m.closed_prebody_stop(bad,162,2,api)
    def test_all_frozen_sources_declared_and_worker_entry_is_shared(self):
        self.assertEqual(len(m.PINS),5)
        self.assertTrue(any(p["path"].endswith("current_queue_successor_runtime.py") for p in m.PINS))
        self.assertTrue(any(p["path"].endswith("current_queue_successor_dispatch.py") for p in m.PINS))
        self.assertNotEqual(m.SELF,"tools/p09/current_queue_successor_runtime.py")
        tree=ast.parse((Path(__file__).parents[3]/m.SELF).read_text(encoding="utf-8"))
        load=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="load")
        condition=next(n for n in load.body if isinstance(n,ast.If) and isinstance(n.test,ast.UnaryOp))
        self.assertEqual(ast.unparse(condition.test),"not worker")
        self.assertTrue(any(isinstance(n,ast.Name) and n.id=="OLD_CONTROLLER" for n in ast.walk(condition)))
        projector=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="graph_v2_paths")
        self.assertTrue(any(isinstance(n,ast.Constant) and n.value=="WHOLE_GRAPH_PATH_AST_INVERSE" for n in ast.walk(projector)))


if __name__=="__main__":unittest.main()
