"""Private factory selection models; never actual Native or product IO."""
from types import FunctionType,SimpleNamespace as NS
import unittest
import owned_source_read_pressure as pressure
import native011_precise_boundary_pacer as precise
import native011_precise_boundary_connection as connection


class PreciseConnectionContracts(unittest.TestCase):
    def fixture(self):
        class Reader(pressure.WeightedReader):
            def diagnostics(self):return {}
        def run(run):return 0
        env=dict(BoundaryReader=Reader,byte_policy=pressure)
        fn=FunctionType(run.__code__,env)
        return NS(engine=NS(run_owned=fn),state=NS(attempts=0,calls=0)),Reader,env
    def test_construction_changes_only_private_factory_slot_without_creating_reader(self):
        linked,Reader,env=self.fixture();before=dict(env);api,proof=connection.connect(linked,precise,modules=())
        self.assertEqual(api.state.attempts,0);self.assertEqual(api.state.proofs,[])
        self.assertIs(api.original_reader,Reader);self.assertIs(env['byte_policy'],before['byte_policy'])
        self.assertFalse(proof['actual_Frame_or_product_qualified'])
    def test_both_factory_calls_return_original_reader_class_with_fresh_pacer(self):
        linked,Reader,env=self.fixture();api,_=connection.connect(linked,precise,modules=())
        readers=[env['BoundaryReader']('.',lambda:None) for _ in range(2)]
        self.assertTrue(all(type(reader) is Reader for reader in readers));self.assertIsNot(readers[0],readers[1])
        self.assertIsNot(readers[0].pacer,readers[1].pacer);self.assertEqual(api.state.completed,2)
        with self.assertRaisesRegex(ValueError,'TWO_BOUNDARY_FACTORIES'):env['BoundaryReader']('.',lambda:None)
    def test_failed_pacer_connection_cannot_retry_in_same_factory(self):
        linked,_,env=self.fixture()
        def fail(*args):raise ValueError('MODEL_PACER_REFUSED')
        api,_=connection.connect(linked,NS(connect=fail),modules=())
        with self.assertRaisesRegex(ValueError,'MODEL_PACER_REFUSED'):env['BoundaryReader']('.',lambda:None)
        with self.assertRaisesRegex(ValueError,'TWO_BOUNDARY_FACTORIES'):env['BoundaryReader']('.',lambda:None)
        self.assertTrue(api.state.failed);self.assertEqual(api.state.completed,0)
    def test_default_module_or_already_attempted_engine_is_not_modified(self):
        linked,_,env=self.fixture();original=env['BoundaryReader']
        module=type('Module',(),{})();module.__dict__.update(env)
        # The actual engine globals dictionary, not an equal-looking copy, is protected.
        module=NS();linked.engine.run_owned=FunctionType(linked.engine.run_owned.__code__,module.__dict__)
        module.__dict__.update(env)
        with self.assertRaisesRegex(ValueError,'PRIVATE_NAMESPACE_NOT_DEFAULT'):connection.connect(linked,precise,modules=(module,))
        self.assertIs(module.BoundaryReader,original)
        linked,_,env=self.fixture();linked.state.attempts=1
        with self.assertRaisesRegex(ValueError,'BEFORE_ANY_WORKER_ATTEMPT'):connection.connect(linked,precise,modules=())
