"""Raw setup uses the current validator; hooked closures remain untouched."""
from types import FunctionType,SimpleNamespace as NS
import unittest
from pathlib import Path
import expanded_unhooked_setup_dependency_v1 as m


class Tests(unittest.TestCase):
    def test_raw_functions_keep_whole_code_and_current_validation(self):
        def worker_hint(value=1):return validate_worker_hint(value)
        env=dict(__name__="p09_exact_current_queue_successor_runtime",validate_worker_hint=lambda v:("old",v))
        original=FunctionType(worker_hint.__code__,env,argdefs=worker_hint.__defaults__)
        current=lambda v:("current",v)
        runtime=NS(worker_hint=original,reconstruct_worker_graph=original,validate_worker_hint=current)
        m.align(runtime)
        self.assertEqual(runtime.worker_hint(),("current",1))
        self.assertEqual(runtime.reconstruct_worker_graph(2),("current",2))
        self.assertIs(runtime.worker_hint.__code__,original.__code__)
        self.assertIs(runtime.worker_hint.__defaults__,original.__defaults__)
    def test_hooked_or_default_functions_not_replaced(self):
        def hooked():return "same"
        runtime=NS(worker_hint=hooked,reconstruct_worker_graph=hooked,validate_worker_hint=lambda v:v)
        m.align(runtime)
        self.assertIs(runtime.worker_hint,hooked);self.assertIs(runtime.reconstruct_worker_graph,hooked)
    def test_whole_frozen_setup_accepts_only_three_metadata_changes(self):
        import flat_current_queue_envelope_runtime_v25 as envelope
        root=Path(__file__).parents[3]
        loaded,_=envelope.namespace_bundle.load(root,[m.ORCHESTRATION],{})
        original=loaded.closed_prebody_preparation_io_v1.main
        changed=m.project_setup_main(root,original)
        self.assertEqual(changed.__code__.co_names,original.__code__.co_names)
        self.assertEqual(changed.__code__.co_varnames,original.__code__.co_varnames)
        self.assertEqual(changed.__defaults__,original.__defaults__)


if __name__=="__main__":unittest.main()
