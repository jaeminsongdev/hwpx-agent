import sys
import unittest
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_diagnostic_connection_v2 as connector
import flat_current_queue_native_diagnostic_runtime_v6 as runtime


def synthetic_namespace_chain():
    old = NS(bind_entry=lambda api, raw: None)
    def leaf():
        return connection
    leaf = FunctionType(leaf.__code__.replace(co_filename=connector.LEAF),
                        dict(connection=old, Path=Path, FunctionType=FunctionType))
    module = NS(run_owned=leaf, connection=old, Path=Path, FunctionType=FunctionType)
    def reconstructed():
        return FunctionType(prior.run_owned.__code__, dict(vars(prior)),
                            argdefs=prior.run_owned.__defaults__)()
    outer = FunctionType(reconstructed.__code__, dict(prior=module, FunctionType=FunctionType))
    return outer, module, old


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if runtime.M.base.CONFIG is None:
            runtime.M.base.configure(146)
        if runtime.M.base.CONFIG.index != 146:
            raise ValueError("TEST_ONLY146")

    def test_v1_reproduces_lost_binding_without_native_or_product(self):
        outer, module, old = synthetic_namespace_chain()
        connected, state = connector.prior.connect_run(outer, NS())
        self.assertIs(connected(), old)
        self.assertEqual(state["actual_local_bindings"], 0)
        self.assertIs(module.connection, old)

    def test_vars_namespace_reconstruction_reaches_new_leaf(self):
        outer, module, old = synthetic_namespace_chain()
        connected, state = connector.connect_run(outer, NS())
        self.assertIsNot(connected(), old)
        self.assertIs(module.connection, old)
        self.assertEqual(state["namespace_dependency_projections"][0]["fields"], ["connection"])

    def test_all_original_function_code_defaults_closures_preserved(self):
        outer, module, old = synthetic_namespace_chain()
        connected, state = connector.connect_run(outer, NS())
        self.assertIs(connected.__code__, outer.__code__)
        self.assertIs(connected.__defaults__, outer.__defaults__)
        self.assertIs(connected.__closure__, outer.__closure__)
        self.assertIs(connected.__globals__["prior"].run_owned.__code__, module.run_owned.__code__)

    def test_no_namespace_fields_hidden_or_added(self):
        outer, module, old = synthetic_namespace_chain()
        connected, state = connector.connect_run(outer, NS())
        self.assertEqual(set(vars(connected.__globals__["prior"])), set(vars(module)))

    def test_original_diagnostic_validator_not_changed(self):
        self.assertIs(connector.validate, connector.prior.validate)
        self.assertIs(connector.connect_entry, connector.prior.connect_entry)

    def test_unrelated_leaf_rejected(self):
        def unrelated():
            return 1
        with self.assertRaises(ValueError):
            connector.connect_run(unrelated, NS())

    def test_real_five_level_namespace_path_and_original_modules_retained(self):
        connected, state = connector.connect_run(runtime.API.original_run_owned, runtime.BACKEND)
        self.assertEqual(len(state["cloned_functions"]), 5)
        self.assertEqual(state["static_leaf_connections"], 1)
        self.assertEqual(state["actual_local_bindings"], 0)
        original = runtime.API.original_run_owned.__globals__["source"]
        self.assertIsNot(connected.__globals__["source"], original)
        self.assertIs(original.run_owned.__globals__["prior"],
                      runtime.API.original_run_owned.__globals__["source"].run_owned.__globals__["prior"])

    def test_real_wrappers_execute_only_to_intercepted_entry_not_product_or_probe(self):
        # REAL five wrapper bytecodes execute; no actual entry, factory, observer,
        # child, Native scope or product is executed. Entry carries private globals.
        def stopped_entry(run):
            return 0
        entry = NS(run_owned=FunctionType(stopped_entry.__code__, {}))
        calls = []
        def intercepted(api, raw, old, backend, state):
            self.assertIs(api, entry)
            self.assertIs(backend, runtime.BACKEND)
            self.assertTrue(raw)
            calls.append("native_dependency_reached")
            state["actual_local_bindings"] += 1
        connected, state = connector.connect_run(runtime.API.original_run_owned, runtime.BACKEND)
        with patch.object(runtime.M.base, "entry", return_value=(entry, {})), \
             patch.object(connector, "connect_entry", side_effect=intercepted), \
             patch("subprocess.Popen", side_effect=AssertionError("NO_CHILD")), \
             patch("subprocess.run", side_effect=AssertionError("NO_CHILD")):
            self.assertEqual(connected(1), 0)
        self.assertEqual(calls, ["native_dependency_reached"])
        self.assertEqual(state["actual_local_bindings"], 1)

    def test_nested_prior_namespace_contains_connected_leaf_dependency(self):
        connected, state = connector.connect_run(runtime.API.original_run_owned, runtime.BACKEND)
        self.assertEqual(len(state["namespace_dependency_projections"]), 4)
        self.assertTrue(any("connection" in row["fields"]
                            for row in state["namespace_dependency_projections"]))


if __name__ == "__main__":
    unittest.main()

