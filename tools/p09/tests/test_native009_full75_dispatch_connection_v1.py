"""Small connection contracts; no project graph, worker or product imports."""
import unittest
from types import SimpleNamespace as NS
import native009_full75_dispatch_connection_v1 as module


class Tests(unittest.TestCase):
    def fixture(self):
        self.pin = dict(path='oracle.py', bytes=1, sha256='0'*64)
        self.metadata = object(); self.a = object(); self.calls = []; self.factory = []
        self.oracle = NS(connect=object()); self.names = NS(current_queue_successor_oracle=self.oracle)
        def load(root, pins, aliases):
            self.calls.append((root, pins, aliases)); return self.names, ['source-proof']
        self.loader = NS(load=load, unchanged=object())
        def factory(root, envelope, metadata, a):
            self.factory.append((root, metadata, a))
            return envelope.namespace_bundle.load(root, [self.pin], {'current_queue_successor_connections': metadata})[0].current_queue_successor_oracle
        self.configuration = NS(oracle_namespace=factory)
        return module.oracle_loader('root', self.loader, self.configuration, self.metadata, self.a, self.pin)

    def test_one_exact_existing_factory_and_original_dependency(self):
        loader, state = self.fixture()
        value = loader.load('root', [self.pin], {'current_queue_successor_connections': self.metadata})
        self.assertIs(value[0], self.names); self.assertIs(state.oracle, self.oracle)
        self.assertEqual((len(self.calls), len(self.factory), state.loads), (1, 1, 1))
        self.assertEqual(state.source_proofs, ['source-proof']); self.assertIs(loader.unchanged, self.loader.unchanged)

    def test_unrelated_dependency_is_delegated_without_installation(self):
        loader, state = self.fixture(); pins = [dict(path='other.py')]
        loader.load('root', pins, {})
        self.assertEqual(len(self.calls), 1); self.assertEqual(state.loads, 0); self.assertEqual(self.factory, [])

    def test_second_oracle_dependency_is_denied(self):
        loader, _ = self.fixture(); aliases = {'current_queue_successor_connections': self.metadata}
        loader.load('root', [self.pin], aliases)
        with self.assertRaises(ValueError): loader.load('root', [self.pin], aliases)
        self.assertEqual(len(self.calls), 1)

    def test_wrong_context_pin_alias_and_extra_dependency_are_denied(self):
        for kind in ('root', 'pin', 'alias', 'extra'):
            loader, state = self.fixture(); root = 'root'; pins = [self.pin]; aliases = {'current_queue_successor_connections': self.metadata}
            if kind == 'root': root = 'elsewhere'
            if kind == 'pin': pins = [dict(self.pin, bytes=2)]
            if kind == 'alias': aliases = {'current_queue_successor_connections': object()}
            if kind == 'extra': pins = [self.pin, dict(path='extra.py')]
            with self.assertRaises(ValueError): loader.load(root, pins, aliases)
            self.assertEqual((state.loads, len(self.calls)), (0, 0))

    def test_original_loader_error_preserved_and_retry_denied(self):
        loader, state = self.fixture(); failure = OSError('SYNTHETIC_SOURCE_ERROR')
        def fail(*args): raise failure
        self.loader.load = fail
        with self.assertRaises(OSError) as caught: loader.load('root', [self.pin], {'current_queue_successor_connections': self.metadata})
        self.assertIs(caught.exception, failure); self.assertEqual(state.loads, 1)
        with self.assertRaises(ValueError): loader.load('root', [self.pin], {'current_queue_successor_connections': self.metadata})

    def test_factory_cannot_read_oracle_twice(self):
        loader, _ = self.fixture()
        def factory(root, envelope, metadata, a):
            for _ in range(2): envelope.namespace_bundle.load(root, [self.pin], {'current_queue_successor_connections': metadata})
            return self.oracle
        self.configuration.oracle_namespace = factory
        with self.assertRaises(ValueError): loader.load('root', [self.pin], {'current_queue_successor_connections': self.metadata})
        self.assertEqual(len(self.calls), 1)

    def test_unwrapped_checker_is_rejected(self):
        checker = NS(validate_candidate=lambda row: True, environment={})
        with self.assertRaises((ValueError, KeyError)): module.verify_checker(checker, NS(binding=object()), NS())


if __name__ == '__main__': unittest.main()
