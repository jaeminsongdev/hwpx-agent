"""Synthetic policy/real source-body contracts, NOT Native/product evidence."""
import ast
import builtins
import copy
import hashlib
from contextlib import contextmanager
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS
import unittest

MODULE = None
RAW_RUNTIME = None
RAW_ENGINE = None


def pin(name, size=1):
    return dict(path=name, bytes=size, sha256='0' * 64)


H = pin('implementation/p09/evidence/p09-361-case114-current-runtime-run001.v1.json')
N = pin('target/current.exe', 2)


def oracle_generator(raw, row, listing, body):
    expected = original.scope.extend(body, listing)
    def check(candidate, current_listing, old_body, fresh, guard):
        guard()
        actual = ORACLE_SCOPE.extend(old_body, current_listing)
        if expected != actual:
            raise ValueError('ORIGINAL_ORACLE_SCOPE_DRIFT')
        if not candidate['original_terminal_predicate']:
            raise ValueError('ORIGINAL_ORACLE_TERMINAL_FAILURE')
        return dict(expected_count=len(expected), cost=ORACLE_SCOPE.cost(actual, 14))
    return check, dict(original_generator_proof=True)


class Reader:
    """No disk access. Counters model original readers for isolated contracts."""
    def __init__(self, rows, docs=None):
        self.rows = copy.deepcopy(rows)
        self.docs = {} if docs is None else copy.deepcopy(docs)
        self.snapshots = {}
        self.read_passes = self.bytes_read = 0
        self.names = []
        self.checkpoint = lambda: None
        self.maximum_parse_bytes = 16 * 1024 * 1024
        self.root = Path('D:/synthetic-policy-tests')
    def _read(self, name, parse=False):
        self.names.append(name)
        if name not in self.rows:
            raise FileNotFoundError()
        p = dict(self.rows[name])
        self.read_passes += 1
        self.bytes_read += p['bytes']
        return p, self.docs.get(name)
    def fresh_pin(self, name):
        p, _ = self._read(name)
        if name in self.snapshots and self.snapshots[name] != p:
            raise ValueError('ORIGINAL_CHANGED')
        self.snapshots[name] = p
        return dict(p)
    def _bind(self, name, actual):
        if name in self.snapshots and self.snapshots[name] != actual:
            raise ValueError('ORIGINAL_CHANGED')
        self.snapshots[name] = dict(actual)
        return self.snapshots[name]
    def pin(self, name):
        return dict(self.snapshots[name]) if name in self.snapshots else self.fresh_pin(name)
    def json(self, name):
        p, value = self._read(name, parse=True)
        self.snapshots[name] = p
        return copy.deepcopy(value)
    def text(self, name):
        return self.json(name)
    def diagnostics(self):
        return dict(read_passes=self.read_passes, bytes_read=self.bytes_read,
            original_owned_read_operations_preserved=True)


class Held:
    """Mock handles only. Never interpreted as physical Native evidence."""
    acquired = False
    closed = False
    def __init__(self):
        self.readers = []
    def acquire(self, rows):
        self.rows = rows
        self.acquired = True
    def check(self):
        if not self.acquired or self.closed:
            raise ValueError('NOT_HELD')
    @contextmanager
    def reader_sources(self, reader):
        self.readers.append(reader)
        yield
    def verify_two_byte_passes(self, rows):
        if len(self.readers) != 2 or any(r.snapshots != rows for r in self.readers):
            raise ValueError('INCOMPLETE_TWO_PASSES')
    def verify_held_identities(self):
        return dict(held_identity_checks_complete=True)
    def close(self):
        self.closed = True
        return True
    def summary(self):
        count = len(self.rows) if self.acquired else 0
        return dict(input_lock_handles_remaining=0 if self.closed else count,
            input_lock_cleanup_confirmed=self.closed, input_lock_handles_opened=count,
            input_lock_handles_closed=count if self.closed else 0)


class Tests(unittest.TestCase):
    def entry_fixture(self, *, mutate=None, bad_count=False):
        import json
        import batch_worker_entry as entry
        prefix = 'implementation/p09/evidence/p09-361-case165-'
        digest = lambda path, raw: dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        encode = lambda obj: json.dumps(obj, sort_keys=True, separators=(',', ':')).encode('ascii')
        step = dict(index=165, before=158)
        old_wire = b'synthetic reference wire'
        current_wire = b'synthetic future wire'
        old_pin = digest(prefix+'successor-worker-capsule009.compact.v6.json', old_wire)
        new_pin = digest(prefix+'successor-worker-capsule010.compact.v1.json', current_wire)
        prior = encode(dict(run=9, index=165, step=step, capsule_pin=old_pin))
        prior_pin = digest(prefix+'successor-worker-bootstrap009.v6.json', prior)
        rows = [dict(index=i) for i in range(162)]
        manifest = pin('implementation/p09/evidence/synthetic-manifest')
        core = dict(index=165, run=10, step=step, capsule_pin=new_pin,
            manifest_pin=manifest, first_descriptor=rows[0])
        bootstrap = dict(schema_version='hwpx-agent.p09-run010-worker-preparation/v1', execution=core,
            reference_bootstrap_pin=prior_pin, reference_wire_pin=old_pin,
            reference_is_constructor_data_not_product_replay=True, GO_authorized=False)
        if mutate:mutate(bootstrap)
        raw = encode(bootstrap)
        boot_pin = digest(prefix+'successor-worker-bootstrap010.v1.json', raw)
        files = {boot_pin['path']:raw, prior_pin['path']:prior, old_pin['path']:old_wire, new_pin['path']:current_wire}
        calls = []
        def read(value, limit):
            calls.append(('read', value['path']))
            self.assertEqual(limit, 16384)
            return files[value['path']]
        binding = NS(descriptors=lambda: rows, manifest_pin=manifest)
        def reference_factory(hint, wire, checkpoint):
            calls.append('reference')
            self.assertEqual(wire, old_wire)
            return NS(binding=binding), {}
        def transport_factory(reference, step, checkpoint):
            calls.append('transport')
            def decode(wire, expected, guard):
                calls.append('decoder')
                self.assertEqual(wire, current_wire)
                return (NS(descriptors=lambda:rows[:-1], manifest_pin=manifest) if bad_count else binding), {}
            return NS(worker=NS(TASK='case165-current-r010-tests', decode=decode)), NS(validate_worker_hint=lambda *args:(165,10))
        args = ('case165-current-r010-tests', boot_pin, read, reference_factory, transport_factory, lambda:None)
        return entry, args, calls, files

    def test_entry_admits_four_inputs_then_constructs_once_without_encoder(self):
        entry, args, calls, files = self.entry_fixture()
        value = entry.reconstruct(*args)
        self.assertEqual([kind for kind in calls if type(kind) is str], ['reference','transport','decoder'])
        self.assertEqual(sum(type(kind) is tuple for kind in calls), 4)
        self.assertEqual(value.proof['metadata_byte_admissions'], 4)
        self.assertFalse(value.proof['fresh_physical_IO_claimed_by_entry'])
        self.assertFalse(value.proof['encoder_or_negative_qualification_cases_run'])
        self.assertFalse(value.proof['GO_authorized'])

    def test_entry_wrong_task_fails_before_io(self):
        entry, args, calls, _ = self.entry_fixture()
        with self.assertRaisesRegex(ValueError, 'ENTRY_EXACT_TASK_BEFORE_IO'):
            entry.reconstruct('case165-current-r009-tests', *args[1:])
        self.assertEqual(calls, [])

    def test_entry_changed_bootstrap_bytes_cannot_start_reference_constructor(self):
        entry, args, calls, files = self.entry_fixture()
        files[args[1]['path']] += b' '
        with self.assertRaisesRegex(ValueError, 'ENTRY_FRESH_BYTES_MATCH_PIN'):
            entry.reconstruct(*args)
        self.assertNotIn('reference', calls)

    def test_entry_go_flag_cannot_be_smuggled_by_valid_hash(self):
        entry, args, calls, _ = self.entry_fixture(mutate=lambda row:row.update(GO_authorized=True))
        with self.assertRaisesRegex(ValueError, 'ENTRY_CLOSED_NO_GO_BOOTSTRAP'):
            entry.reconstruct(*args)
        self.assertNotIn('reference', calls)

    def test_entry_old_run_or_boolean_case_is_not_new_identity(self):
        for change in (dict(run=9), dict(index=True)):
            entry, args, calls, _ = self.entry_fixture(mutate=lambda row:row['execution'].update(change))
            with self.assertRaisesRegex(ValueError, 'ENTRY_EXACT_CASE_AND_RUN'):
                entry.reconstruct(*args)
            self.assertNotIn('reference', calls)

    def test_entry_unknown_reference_path_denied_before_reference_io(self):
        entry, args, calls, _ = self.entry_fixture(mutate=lambda row:
            row['reference_wire_pin'].update(path='implementation/p09/evidence/unknown.json'))
        with self.assertRaisesRegex(ValueError, 'ENTRY_CLOSED_REFERENCE_AND_WIRE_PATHS'):
            entry.reconstruct(*args)
        self.assertEqual(len(calls), 1)

    def test_entry_descriptor_subset_is_never_current_qualification(self):
        entry, args, calls, _ = self.entry_fixture(bad_count=True)
        with self.assertRaisesRegex(ValueError, 'ENTRY_COMPLETE162_NOT_SUBSET_OR_REBASE'):
            entry.reconstruct(*args)

    def test_entry_resource_error_identity_preserved_before_io(self):
        entry, args, calls, _ = self.entry_fixture()
        error = ValueError('ORIGINAL_RESOURCE_STOP')
        def stop():raise error
        with self.assertRaises(ValueError) as caught:
            entry.reconstruct(*args[:-1], stop)
        self.assertIs(caught.exception, error)
        self.assertEqual(calls, [])

    def test_entry_file_reader_original_scope_link_and16K_contracts(self):
        import io
        import batch_worker_entry as entry
        class Root:
            parents = ()
            linked = False
            opened = 0
            data = b'synthetic bounded metadata'
            def is_dir(self):return True
            def is_symlink(self):return self.linked
            def is_junction(self):return False
            def __truediv__(self, name):
                root = self
                class File:
                    parent = root
                    def is_file(self):return True
                    def is_symlink(self):return False
                    def is_junction(self):return False
                    def open(self, mode):
                        root.opened += 1
                        return io.BytesIO(root.data)
                return File()
        root = Root()
        read = entry.file_reader(root, lambda:None)
        selected = pin('implementation/p09/evidence/p09-361-case165-successor-worker-bootstrap010.v1.json')
        self.assertEqual(read(selected, 16384), root.data)
        with self.assertRaisesRegex(ValueError, 'ENTRY_ORIGINAL_DIRECT_READ_SCOPE'):
            read(pin('unknown.json'), 16384)
        root.linked = True
        with self.assertRaisesRegex(ValueError, 'ENTRY_DIRECT_ANCESTORS'):
            read(selected, 16384)
        self.assertEqual(root.opened, 1)
        root.linked = False; root.data = b'x'*16385
        with self.assertRaisesRegex(ValueError, 'ENTRY_ORIGINAL_READ16K'):
            read(selected, 16384)

    def identity_fixture(self, data=b'synthetic inner bytes', error=None):
        calls = []
        digest = lambda raw: dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        def encode(binding, authority, prior, guard):
            guard()
            return data, digest(data)
        def decode(raw, expected, guard):
            guard()
            calls.append((raw, expected))
            if error is not None:
                raise error
            return NS(), dict(policy_capsule_bytes=len(raw))
        worker = NS(TASK='case165-current-r010-tests', MAX_BYTES=16384, encode=encode, decode=decode)
        return MODULE.identity_wire(worker, lambda: None), calls, digest

    def test_identity_wire_both_hashes_and_inner_counter_preserved(self):
        worker, calls, digest = self.identity_fixture()
        wire, expected = worker.encode(None, None, None, lambda: None)
        _, proof = worker.decode(wire, expected, lambda: None)
        self.assertEqual(expected, digest(wire))
        self.assertEqual(calls, [(b'synthetic inner bytes', digest(b'synthetic inner bytes'))])
        self.assertEqual(proof['policy_capsule_bytes'], len(b'synthetic inner bytes'))
        self.assertEqual(proof['identity_transport_bytes'], len(wire))
        self.assertTrue(proof['original_inner_byte_counter_not_relabelled'])

    def test_identity_wire_old_packet_never_reaches_inner_decoder(self):
        worker, calls, digest = self.identity_fixture()
        old = b'P09W3-reference009-only'
        with self.assertRaisesRegex(ValueError, 'IDENTITY_MAGIC_NOT_OLD009_WIRE'):
            worker.decode(old, digest(old), lambda: None)
        self.assertEqual(calls, [])

    def test_identity_wire_wrong_external_hash_never_reaches_inner_decoder(self):
        worker, calls, _ = self.identity_fixture()
        wire, expected = worker.encode(None, None, None, lambda: None)
        with self.assertRaisesRegex(ValueError, 'IDENTITY_TRANSPORT_HASH'):
            worker.decode(wire, dict(expected, sha256='0'*64), lambda: None)
        self.assertEqual(calls, [])

    def test_identity_wire_wrong_task_even_with_valid_outer_hash_rejected(self):
        worker, calls, digest = self.identity_fixture()
        wire, _ = worker.encode(None, None, None, lambda: None)
        bad = wire.replace(b'case165-current-r010-tests', b'case165-current-r009-tests')
        with self.assertRaisesRegex(ValueError, 'EXACT_IDENTITY_TASK_CASE_AND_RUN'):
            worker.decode(bad, digest(bad), lambda: None)
        self.assertEqual(calls, [])

    def test_identity_wire_changed_inner_even_with_valid_outer_hash_rejected(self):
        worker, calls, digest = self.identity_fixture()
        wire, _ = worker.encode(None, None, None, lambda: None)
        bad = wire[:-1] + bytes([wire[-1] ^ 1])
        with self.assertRaisesRegex(ValueError, 'INNER_IDENTITY_HASH'):
            worker.decode(bad, digest(bad), lambda: None)
        self.assertEqual(calls, [])

    def test_identity_wire_header_cannot_expand_original16K_ceiling(self):
        worker, calls, _ = self.identity_fixture(data=b'x'*16384)
        with self.assertRaisesRegex(ValueError, 'UNCHANGED_IDENTITY_WIRE16K'):
            worker.encode(None, None, None, lambda: None)
        self.assertEqual(calls, [])

    def test_identity_wire_original_decoder_error_identity_preserved(self):
        error = ValueError('ORIGINAL_INNER_DECODER_FAILURE')
        worker, calls, _ = self.identity_fixture(error=error)
        wire, expected = worker.encode(None, None, None, lambda: None)
        with self.assertRaises(ValueError) as caught:
            worker.decode(wire, expected, lambda: None)
        self.assertIs(caught.exception, error)
        self.assertEqual(len(calls), 1)

    def test_identity_wire_hard_guard_error_precedes_decode(self):
        worker, calls, _ = self.identity_fixture()
        error = ValueError('ORIGINAL_RESOURCE_FAILURE')
        def stop():
            raise error
        with self.assertRaises(ValueError) as caught:
            worker.decode(b'', {}, stop)
        self.assertIs(caught.exception, error)
        self.assertEqual(calls, [])

    def engine_builder(self):
        node = next(n for n in ast.parse(RAW_RUNTIME).body
            if isinstance(n, ast.FunctionDef) and n.name == 'connect_factory')
        env = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), MODULE.RUNTIME, 'exec'), env)
        runtime = NS(connect_factory=env['connect_factory'])
        return MODULE.prepare_engine_builder(RAW_ENGINE, runtime, RAW_RUNTIME), runtime

    def test_future_builder_positional_inverse_does_not_change_product10(self):
        builder, runtime = self.engine_builder()
        self.assertEqual(builder.task, 'case165-current-r010-tests')
        self.assertTrue(builder.receipt.endswith('run010.v1.json'))
        self.assertEqual(builder.proof['target_descriptors'], 162)
        self.assertTrue(builder.proof['original_product10_retained'])
        node = next(n for n in ast.parse(RAW_ENGINE).body if isinstance(n, ast.FunctionDef) and n.name == 'build')
        env = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), MODULE.ENGINE, 'exec'), env)
        original = env['build'].__code__
        changed = builder.build.__code__
        slots = builder.proof['engine_metadata_inverses'][1]['slots']
        restored = list(changed.co_consts)
        for slot, before, after in slots:
            self.assertEqual(changed.co_consts[slot], after)
            restored[slot] = before
        self.assertEqual(MODULE._code_shape(changed.replace(co_consts=tuple(restored))), MODULE._code_shape(original))
        for position, value in enumerate(original.co_consts):
            if type(value) is int and value == 10:
                self.assertEqual(changed.co_consts[position], 10)
        self.assertFalse(builder.proof['GO_authorized'])
        self.assertFalse(builder.proof['new_identity_graph_transport_or_worker_qualified'])

    def test_future_builder_factory_original_body_and_default_are_unchanged(self):
        builder, runtime = self.engine_builder()
        original = runtime.connect_factory
        expected = original.__code__
        values = list(builder.factory.__code__.co_consts)
        slot = builder.proof['factory_bound_inverse']['constant_slot']
        self.assertEqual(values[slot], 10)
        values[slot] = 8
        self.assertEqual(MODULE._code_shape(builder.factory.__code__.replace(co_consts=tuple(values))),
            MODULE._code_shape(expected))
        self.assertIs(runtime.connect_factory.__code__, expected)
        self.assertEqual(builder.proof['factory_bound_inverse']['new'], 10)

    def test_future_builder_rejects_changed_sources_and_nonoriginal_runtime(self):
        builder, runtime = self.engine_builder()
        with self.assertRaisesRegex(ValueError, 'EXACT_ORIGINAL_ENGINE_SOURCE'):
            MODULE.prepare_engine_builder(RAW_ENGINE + b'\n', runtime, RAW_RUNTIME)
        with self.assertRaisesRegex(ValueError, 'EXACT_ORIGINAL_FACTORY_SOURCE'):
            MODULE.prepare_engine_builder(RAW_ENGINE, runtime, RAW_RUNTIME + b'\n')
        runtime.connect_factory = lambda *args: None
        with self.assertRaisesRegex(ValueError, 'ENTIRE_ORIGINAL_RUNTIME_FACTORY'):
            MODULE.prepare_engine_builder(RAW_ENGINE, runtime, RAW_RUNTIME)

    def test_future_builder_old_task_or_wrong_count_cannot_reach_downstream(self):
        for task, count in (('case165-current-r009-tests', 162), ('case165-current-r010-tests', 75)):
            builder, _ = self.engine_builder()
            graph = NS(worker=NS(TASK=task), binding=NS(next_case=165, descriptors=lambda: [None]*count))
            with self.assertRaisesRegex(ValueError, 'EXACT_FULL69_RUN009_GRAPH'):
                builder.build(None, None, None, graph, None, None, None, lambda: None)

    def test_future_builder_existing_new_result_guard_is_still_original(self):
        builder, _ = self.engine_builder()
        paths = []
        class Root:
            def __truediv__(self, name):
                paths.append(name)
                return NS(exists=lambda: True)
        graph = NS(worker=NS(TASK=builder.task), binding=NS(next_case=165, descriptors=lambda: [None]*162))
        with self.assertRaisesRegex(ValueError, 'NO_EXISTING_NATIVE009_RECEIPT'):
            builder.build(Root(), None, None, graph, None, None, None, lambda: None)
        self.assertEqual(paths, [builder.receipt])

    def test_future_builder_complete_body_single_fixture_construction_no_worker_execution(self):
        builder, runtime = self.engine_builder()
        calls = []
        worker = lambda *args: self.fail('product fixture worker executed')
        engine = NS(worker=worker)
        def template():
            calls.append('template')
            return engine, {}
        names = NS(physical_run=lambda index: 10, task=lambda index: builder.task,
            root_path=lambda config: builder.receipt, public_run=lambda index, run: 1)
        def factory(root, loader, window, index, run, checkpoint):
            self.assertEqual((index, run), (165, 10))
            return template, names, {}
        # Private test-only dependency. Real factory code is separately checked
        # above; this isolates the unchanged WHOLE builder control flow.
        builder.build.__globals__['factory9'] = lambda original: (factory, {})
        state = NS(original=worker, attempts=0, calls=0, completed=False)
        def compose(same_engine, graph, root, checkpoint):
            self.assertIs(same_engine()[0], engine)
            return worker, state, NS(), {}
        runtime.compose_worker = compose
        window = NS(M=NS(base=NS(configure=lambda index: calls.append(index))), WINDOW=NS(SECONDS=10))
        class Root:
            def __truediv__(self, name):
                return NS(exists=lambda: False, read_bytes=lambda: b'synthetic window only')
        graph = NS(worker=NS(TASK=builder.task), binding=NS(next_case=165, descriptors=lambda: [None]*162))
        built = builder.build(Root(), None, NS(runtime=runtime), graph, NS(),
            NS(current_window=lambda *args: (window, {})), NS(WINDOW_PIN={'path': 'synthetic-window'}), lambda: None)
        self.assertEqual(calls, [165, 'template'])
        self.assertIs(built.original_worker, worker)
        self.assertEqual((built.state.attempts, built.state.calls), (0, 0))
        self.assertFalse(built.product_Native_or_GO_authorized)

    def batch(self):
        m = MODULE
        whole = {H['path']: H, N['path']: N}
        return m.Batch(whole, {N['path']: N}, {H['path']: H}, first_index=165, checkpoint=lambda: None)
    def opened(self):
        b = self.batch()
        b.begin(Reader(MODULE.plain(b.whole)))
        return b
    def frame(self, b):
        m = MODULE
        f = m.phased.frames.Frame(m.phased.frames.Registry(), m.plain(b.current), lambda: None, held=Held())
        f.acquire()
        return f
    def commit(self, b, frame):
        for _ in range(2):
            frame.read_boundary(lambda guard: Reader(MODULE.plain(b.current)), lambda: None)
        frame.commit(dict(cleanup_confirmed=True, owned_tree_empty=True,
            job_final=dict(active_processes=0, owned_processes=[])))

    def parent(self, b, *, lifecycle=False):
        """Synthetic parent constructor; no native handles or product body."""
        base = MODULE.phased.frames
        def run():
            raise AssertionError('original fixture body must not execute')
        original = FunctionType(run.__code__, dict(run.__globals__, native=NS(frames=base)))
        worker = lambda: None
        engine = NS(run_owned=original, worker=worker)
        def connect_engine(engine, binding):
            state = NS(original=engine.run_owned, original_worker=engine.worker, frames=[], attempts=0)
            class Projected(base.Frame):
                pass
            class Parent(Projected):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    state.frames.append(self)
            native = NS(frames=NS(Frame=Parent))
            def execute():
                state.attempts += 1
                return native.frames.Frame(base.Registry(), MODULE.plain(b.current), lambda: None, held=Held()).acquire()
            return NS(run_owned=execute, worker=engine.worker), state
        return b.connect_parent(engine, NS(parent=NS(connect_engine=connect_engine), binding=NS(next_case=b.first_index)),
            connect_lifecycle=lifecycle)

    def test_parent_lifecycle_hooks_call_original_acquire_and_commit(self):
        b = self.batch()
        parent, state = self.parent(b, lifecycle=True)
        b.begin(Reader(MODULE.plain(b.whole)))
        frame = parent.run_owned()
        self.assertEqual(b.phase, 'CASE_ACTIVE')
        self.assertIs(b.active[1], frame)
        self.commit(b, frame)
        self.assertEqual(b.phase, 'READY')
        self.assertEqual(frame.state, 'COMMITTED')
        self.assertEqual(len(b.cases), 1)
        self.assertEqual(len(frame.readers), 2)
        result = b.finish(Reader(MODULE.plain(b.whole)))
        self.assertTrue(result['parent_lifecycle_connected'])
        self.assertFalse(result['queue_advance_authorized'])

    def test_parent_lifecycle_no_acquisition_before_whole_start(self):
        b = self.batch()
        parent, state = self.parent(b, lifecycle=True)
        with self.assertRaisesRegex(ValueError, 'AUDITED_READY_BEFORE_PARENT_ACQUIRE'):
            parent.run_owned()
        self.assertFalse(state.frames[0].held.acquired)
        self.assertEqual(b.cases, [])

    def test_parent_lifecycle_abort_releases_handles_but_breaks_batch(self):
        b = self.batch()
        parent, state = self.parent(b, lifecycle=True)
        b.begin(Reader(MODULE.plain(b.whole)))
        frame = parent.run_owned()
        self.assertTrue(frame.close())
        self.assertTrue(frame.held.closed)
        self.assertEqual(b.phase, 'BROKEN')
        with self.assertRaisesRegex(ValueError, 'BROKEN_BATCH'):
            b.finish(Reader(MODULE.plain(b.whole)))

    def test_parent_lifecycle_incomplete_commit_is_original_failure_not_acceptance(self):
        b = self.batch()
        parent, state = self.parent(b, lifecycle=True)
        b.begin(Reader(MODULE.plain(b.whole)))
        frame = parent.run_owned()
        try:
            with self.assertRaisesRegex(ValueError, 'COMPLETE_TWO_BYTE_BOUNDARIES'):
                frame.commit({})
            self.assertEqual(b.phase, 'BROKEN')
            self.assertEqual(b.cases, [])
        finally:
            frame.close()

    def test_exact_connected_parent_frame_keeps_original_two_boundaries(self):
        b = self.batch()
        default = MODULE.phased.frames.Frame
        parent, state = self.parent(b)
        self.assertIs(MODULE.phased.frames.Frame, default)
        self.assertEqual(state.frames, [])
        b.begin(Reader(MODULE.plain(b.whole)))
        frame = parent.run_owned()
        self.assertIsNot(type(frame), default)
        b.case_started(165, frame)
        self.commit(b, frame)
        b.case_finished(frame)
        result = b.finish(Reader(MODULE.plain(b.whole)))
        self.assertEqual(len(frame.boundaries), 2)
        self.assertTrue(result['exact_parent_frame_class_connected'])
        self.assertFalse(result['queue_advance_authorized'])
        self.assertIs(MODULE.phased.frames.Frame, default)

    def test_unconnected_subclass_is_still_rejected(self):
        b = self.opened()
        class Other(MODULE.phased.frames.Frame):
            pass
        frame = Other(MODULE.phased.frames.Registry(), MODULE.plain(b.current), lambda: None, held=Held()).acquire()
        try:
            with self.assertRaisesRegex(ValueError, 'LIVE_NATIVE_FRAME_NOT_SERIALIZED'):
                b.case_started(165, frame)
            self.assertEqual(b.phase, 'BROKEN')
        finally:
            frame.close()

    def test_parent_binding_must_precede_start_and_cannot_be_replaced(self):
        b = self.batch()
        self.parent(b)
        with self.assertRaisesRegex(ValueError, 'PARENT_CONNECTION_ONCE'):
            self.parent(b)
        with self.assertRaisesRegex(ValueError, 'PARENT_CONNECTION_ONCE'):
            self.parent(self.opened())

    def test_connected_parent_class_mutation_rejected_before_live_admission(self):
        b = self.batch()
        parent, _ = self.parent(b)
        b.begin(Reader(MODULE.plain(b.whole)))
        frame = parent.run_owned()
        type(frame).check = lambda self: None
        try:
            with self.assertRaisesRegex(ValueError, 'UNCHANGED_CONNECTED_FRAME_CLASSES'):
                b.case_started(165, frame)
            self.assertEqual(b.phase, 'BROKEN')
        finally:
            frame.close()

    def test_connected_parent_instance_shadow_rejected(self):
        b = self.batch()
        parent, _ = self.parent(b)
        b.begin(Reader(MODULE.plain(b.whole)))
        frame = parent.run_owned()
        frame.check = lambda: None
        try:
            with self.assertRaisesRegex(ValueError, 'NO_INSTANCE_FRAME_METHOD_REPLACEMENT'):
                b.case_started(165, frame)
        finally:
            frame.close()

    def test_connected_parent_in_place_function_code_mutation_rejected(self):
        b = self.batch()
        parent, _ = self.parent(b)
        b.begin(Reader(MODULE.plain(b.whole)))
        frame = parent.run_owned()
        # Use a method local to this fixture, never mutate a shared base class.
        method = type(frame).__init__
        old_code = method.__code__
        try:
            method.__code__ = old_code.replace(co_name='changed_constructor')
            with self.assertRaisesRegex(ValueError, 'UNCHANGED_CONNECTED_FRAME_METHOD_CODE'):
                b.case_started(165, frame)
        finally:
            method.__code__ = old_code
            frame.close()

    def test_connected_parent_closing_rechecks_class_integrity(self):
        b = self.batch()
        parent, _ = self.parent(b)
        b.begin(Reader(MODULE.plain(b.whole)))
        frame = parent.run_owned()
        b.case_started(165, frame)
        self.commit(b, frame)
        type(frame).summary = lambda self: {}
        with self.assertRaisesRegex(ValueError, 'UNCHANGED_CONNECTED_FRAME_CLASSES'):
            b.case_finished(frame)
        self.assertEqual(b.phase, 'BROKEN')

    def test_whole_start_and_end_are_distinct_fresh_boundaries(self):
        b = self.batch()
        first = Reader(MODULE.plain(b.whole))
        b.begin(first)
        last = Reader(MODULE.plain(b.whole))
        result = b.finish(last)
        self.assertEqual(first.read_passes, 2)
        self.assertEqual(last.read_passes, 2)
        self.assertEqual(result['phase'], 'EMPTY_BATCH_AUDITED_NOT_ACCEPTED')

    def test_batch_history_reads_do_not_grow_per_case(self):
        b = self.opened()
        frames = []
        for index in range(165, 168):
            frame = self.frame(b)
            b.case_started(index, frame)
            self.commit(b, frame)
            b.case_finished(frame)
            frames.append(frame)
        last = Reader(MODULE.plain(b.whole))
        result = b.finish(last)
        self.assertEqual(result['cases_with_original_Frame_checks'], 3)
        self.assertEqual(result['phase'], 'SOURCE_BOUNDARIES_COMPLETE_NOT_ACCEPTED')
        self.assertEqual(last.names.count(H['path']), 1)
        self.assertEqual([len(f.boundaries) for f in frames], [2, 2, 2])
        self.assertTrue(all(H['path'] not in r.names for f in frames for r in f.readers))

    def test_closed_batch_does_not_authorize_any_acceptance(self):
        b = self.opened()
        f = self.frame(b)
        b.case_started(165, f)
        self.commit(b, f)
        b.case_finished(f)
        result = b.finish(Reader(MODULE.plain(b.whole)))
        for key in ('queue_advance_authorized', 'GO_authorized', 'product_execution_authorized'):
            self.assertIs(result[key], False)
        self.assertEqual(result['accepted_count_delta'], 0)

    def oracle_fixture(self, *, close=True):
        # Actual unchanged full projector code with a typed in-memory Binding
        # dependency. Not physical envelope/Native evidence or a real acceptor.
        import runtime_envelope_full_oracle_connection_v1 as full
        m = MODULE
        b = self.batch()
        class Binding:
            next_case = 165
            def __init__(self):
                self.scope_checks = 0
            def descriptors(self):
                return []
            def semantic_union(self, rows, checkpoint):
                checkpoint()
                return m.scope.pins(list(rows.values())), {}
            def project(self, rows, checkpoint):
                values, proof = self.semantic_union(rows, checkpoint)
                return NS(physical_pins=values), proof
            def validate_scope_evidence(self, row, rows, checkpoint):
                checkpoint()
                m.require(m.scope.pins(row['source_freeze']) == rows, 'ORACLE_FIXTURE_EXACT_CURRENT_ROW')
                self.scope_checks += 1
            def runtime_budget(self, rows, requests, budget, checkpoint):
                checkpoint()
                return budget(rows, requests)
        binding = Binding()
        function = full.projector
        typed = FunctionType(function.__code__, dict(function.__globals__,
            binding_module=NS(Binding=Binding, require=m.require)),
            argdefs=function.__defaults__, closure=function.__closure__)
        typed.__kwdefaults__ = function.__kwdefaults__
        original = NS(**{**vars(full), 'projector': typed})
        linked = b.connect_full_oracle(original, binding, index=165)
        generator = FunctionType(oracle_generator.__code__, dict(oracle_generator.__globals__,
            original=NS(scope=m.scope), ORACLE_SCOPE=m.scope, mechanics_projection=lambda node: node))
        project, state = linked.projector(generator, binding,
            lambda rows, requests: dict(input_count=len(rows), requests=requests), lambda: None)
        frame = None
        if close:
            b.begin(Reader(m.plain(b.whole)))
            frame = self.frame(b)
            b.case_started(165, frame)
            self.commit(b, frame)
            b.case_finished(frame)
            b.finish(Reader(m.plain(b.whole)))
        row = dict(source_freeze=[dict(N)], original_terminal_predicate=True)
        return b, binding, original, linked, generator, project, state, row, frame

    def test_full_oracle_connect_does_not_mutate_default_projector_or_generator(self):
        b, binding, original, linked, generator, project, state, row, frame = self.oracle_fixture()
        old_projector = original.projector
        before_globals, before_row = dict(generator.__globals__), copy.deepcopy(row)
        check, proof = project(b'source', row, {N['path']: N}, {H['path']: H})
        result = check(row, {N['path']: N}, {H['path']: H}, None, lambda: None)
        self.assertIs(original.projector, old_projector)
        self.assertEqual(generator.__globals__, before_globals)
        self.assertEqual(row, before_row)
        self.assertEqual(result, dict(expected_count=1, cost=dict(input_count=1, requests=167)))
        self.assertEqual(state.batch.whole_scope_checks, 2)
        self.assertEqual(binding.scope_checks, 2)
        self.assertTrue(proof['whole_original_checker_code_retained'])
        self.assertTrue(proof['independent_whole_expectations_checked_before_current_selection'])
        self.assertFalse(proof['queue_acceptance_authorized'])

    def test_full_oracle_blocks_before_start_and_before_closing(self):
        b, binding, _, _, _, project, state, row, _ = self.oracle_fixture(close=False)
        for phase in ('NEW', 'READY'):
            if phase == 'READY':
                b.begin(Reader(MODULE.plain(b.whole)))
            with self.assertRaisesRegex(ValueError, 'COMPLETE_WHOLE_BOUNDARIES_BEFORE_ORACLE'):
                project(b'source', row, {N['path']: N}, {H['path']: H})
        self.assertEqual(state.original.observed['generator_calls'], 0)
        self.assertEqual(binding.scope_checks, 0)

    def test_full_oracle_empty_batch_is_not_product_evidence(self):
        b, _, _, _, _, project, _, row, _ = self.oracle_fixture(close=False)
        b.begin(Reader(MODULE.plain(b.whole)))
        b.finish(Reader(MODULE.plain(b.whole)))
        with self.assertRaisesRegex(ValueError, 'COMPLETE_WHOLE_BOUNDARIES_BEFORE_ORACLE'):
            project(b'source', row, {N['path']: N}, {H['path']: H})

    def test_full_oracle_independent_missing_history_not_hidden_by_current_candidate(self):
        b, _, _, _, _, project, _, row, _ = self.oracle_fixture()
        with self.assertRaisesRegex(ValueError, 'INDEPENDENT_ORACLE_WHOLE_EXACT'):
            project(b'source', row, {N['path']: N}, {N['path']: N})

    def test_full_oracle_unknown_whole_input_requires_new_plan(self):
        b, _, _, _, _, project, _, row, _ = self.oracle_fixture()
        extra = pin('tools/p09/not-declared.py')
        with self.assertRaisesRegex(ValueError, 'INDEPENDENT_ORACLE_WHOLE_EXACT'):
            project(b'source', row, {N['path']: N}, {H['path']: H, extra['path']: extra})

    def test_full_oracle_wrong_current_row_rejected_by_original_projector_dependency(self):
        b, _, _, _, _, project, _, row, _ = self.oracle_fixture()
        row['source_freeze'] = [H]
        with self.assertRaisesRegex(ValueError, 'ORACLE_FIXTURE_EXACT_CURRENT_ROW'):
            project(b'source', row, {N['path']: N}, {H['path']: H})

    def test_full_oracle_original_terminal_failure_remains_failure(self):
        b, _, _, _, _, project, _, row, _ = self.oracle_fixture()
        check, _ = project(b'source', row, {N['path']: N}, {H['path']: H})
        row['original_terminal_predicate'] = False
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_ORACLE_TERMINAL_FAILURE'):
            check(row, {N['path']: N}, {H['path']: H}, None, lambda: None)
        self.assertEqual(b.phase, 'BROKEN')

    def test_full_oracle_unchanged_candidate_identity_check_is_retained(self):
        b, _, _, _, _, project, _, row, _ = self.oracle_fixture()
        check, _ = project(b'source', row, {N['path']: N}, {H['path']: H})
        with self.assertRaisesRegex(ValueError, 'SAME_UNMODIFIED_CANDIDATE_OBJECT'):
            check(copy.deepcopy(row), {N['path']: N}, {H['path']: H}, None, lambda: None)
        self.assertEqual(b.phase, 'BROKEN')

    def test_full_oracle_generator_cannot_omit_independent_scope_check(self):
        b, binding, _, linked, generator, _, _, row, _ = self.oracle_fixture()
        def unchecked(raw, row, listing, body):
            def check(*args):
                return {}
            return check, {}
        forged = FunctionType(unchecked.__code__, dict(generator.__globals__))
        project, _ = linked.projector(forged, binding, lambda *args: None, lambda: None)
        with self.assertRaisesRegex(ValueError, 'INDEPENDENT_WHOLE_SCOPE_MUST_BE_CHECKED'):
            project(b'source', row, {N['path']: N}, {H['path']: H})
        self.assertEqual(b.phase, 'BROKEN')

    def test_full_oracle_rechecks_batch_and_frame_before_checker(self):
        for corrupt in ('batch', 'frame'):
            b, _, _, _, _, project, state, row, frame = self.oracle_fixture()
            check, _ = project(b'source', row, {N['path']: N}, {H['path']: H})
            if corrupt == 'batch':
                b.phase = 'BROKEN'
            else:
                frame.state = 'CLOSED'
            with self.assertRaises(ValueError):
                check(row, {N['path']: N}, {H['path']: H}, None, lambda: None)
            self.assertEqual(state.original.observed['original_checker_calls'], 0)

    def test_changed_history_at_closing_is_sticky_failure(self):
        b = self.opened()
        rows = MODULE.plain(b.whole)
        rows[H['path']]['sha256'] = 'a' * 64
        with self.assertRaisesRegex(ValueError, 'WHOLE_BOUNDARY_CHANGED'):
            b.finish(Reader(rows))
        self.assertEqual(b.phase, 'BROKEN')
        with self.assertRaisesRegex(ValueError, 'BROKEN_BATCH'):
            b.finish(Reader(MODULE.plain(b.whole)))

    def test_missing_history_stops_original_read(self):
        b = self.batch()
        with self.assertRaises(FileNotFoundError):
            b.begin(Reader({N['path']: N}))
        self.assertEqual(b.phase, 'BROKEN')

    def test_reused_initial_reader_cannot_supply_closing(self):
        b = self.batch()
        first = Reader(MODULE.plain(b.whole))
        b.begin(first)
        with self.assertRaisesRegex(ValueError, 'FRESH_DISTINCT'):
            b.finish(first)

    def test_lying_read_accounting_denied(self):
        b = self.batch()
        r = Reader(MODULE.plain(b.whole))
        old = r.fresh_pin
        def lie(name):
            value = old(name)
            r.bytes_read -= value['bytes']
            return value
        r.fresh_pin = lie
        with self.assertRaisesRegex(ValueError, 'WHOLE_ACTUAL_READ_ACCOUNTING'):
            b.begin(r)

    def test_no_metadata_before_batch_start(self):
        b = self.batch()
        with self.assertRaises(ValueError):
            with b.metadata_reader(Reader(MODULE.plain(b.whole))):
                pass

    def test_unknown_or_history_read_denied_before_io_and_latched(self):
        for name in (H['path'], 'unknown.json'):
            b = self.opened()
            r = Reader(MODULE.plain(b.whole))
            old = r._read
            with b.metadata_reader(r):
                with self.assertRaisesRegex(ValueError, 'PRESERVATION_OR_UNDECLARED'):
                    r.fresh_pin(name)
                with self.assertRaisesRegex(ValueError, 'BROKEN_BATCH'):
                    r.fresh_pin(N['path'])
            self.assertEqual(r.names, [])
            self.assertEqual(r._read, old)

    def test_current_changed_bytes_fail_before_selection(self):
        b = self.opened()
        rows = MODULE.plain(b.whole)
        rows[N['path']]['bytes'] = 3
        with self.assertRaisesRegex(ValueError, 'CURRENT_METADATA_BYTES_CHANGED'):
            with b.metadata_reader(Reader(rows)) as r:
                r.fresh_pin(N['path'])

    def test_logical_alias_uses_current_carrier_without_replacing_original_io(self):
        b = self.opened()
        logical = pin('implementation/p09/evidence/logical-receipt.json', 3)
        descriptor = dict(semantic_original_pin=logical, physical_envelope_pin=N)
        binding = NS(descriptors=lambda: [descriptor], semantic_union=lambda rows, checkpoint: (rows, {}))
        r = Reader({logical['path']: logical})
        with b.metadata_reader(r, binding):
            self.assertEqual(r.fresh_pin(logical['path']), logical)
            self.assertEqual(b.select_current(MODULE.plain(b.whole), r, binding), MODULE.plain(b.current))
        self.assertEqual(r.names, [logical['path']])

    def test_current_scope_keeps_logical_pins_while_frame_scope_is_physical(self):
        b = self.opened()
        logical = pin('implementation/p09/evidence/logical-source.json', 3)
        binding = NS(descriptors=lambda: [dict(semantic_original_pin=logical, physical_envelope_pin=N)],
            semantic_union=lambda rows, checkpoint: (rows, {}))
        r = Reader({logical['path']: logical})
        with b.metadata_reader(r, binding):
            r.fresh_pin(logical['path'])
            result = b.select_current({logical['path']: logical, H['path']: H}, r, binding)
        self.assertEqual(result, {logical['path']: logical})
        self.assertEqual(MODULE.plain(b.current), {N['path']: N})

    def test_old_declaration_injection_cannot_silently_expand_current_scope(self):
        b = self.opened()
        binding = NS(descriptors=lambda: [],
            semantic_union=lambda rows, checkpoint: (MODULE.plain(b.whole), {}))
        with self.assertRaisesRegex(ValueError, 'CURRENT_SCOPE_MUST_NOT_REINTRODUCE_HISTORY'):
            with b.metadata_reader(Reader(MODULE.plain(b.whole)), binding) as r:
                b.select_current(MODULE.plain(b.whole), r, binding)

    def test_logical_alias_cannot_authorize_cold_carrier(self):
        b = self.opened()
        logical = pin('implementation/p09/evidence/logical-cold.json')
        binding = NS(descriptors=lambda: [dict(semantic_original_pin=logical, physical_envelope_pin=H)])
        r = Reader({logical['path']: logical})
        with self.assertRaisesRegex(ValueError, 'PRESERVATION_OR_UNDECLARED'):
            with b.metadata_reader(r, binding):
                r.fresh_pin(logical['path'])
        self.assertEqual(r.names, [])

    def test_alias_descriptor_outside_whole_or_duplicate_is_rejected(self):
        logical = pin('implementation/p09/evidence/logical.json')
        for carriers in ((pin('outside.json'),), (N, N)):
            b = self.opened()
            binding = NS(descriptors=lambda: [dict(semantic_original_pin=logical, physical_envelope_pin=p) for p in carriers])
            with self.assertRaises(ValueError):
                with b.metadata_reader(Reader({}), binding):
                    pass

    def test_original_resource_error_precedes_policy_check(self):
        b = self.opened()
        r = Reader(MODULE.plain(b.whole))
        error = ValueError('ORIGINAL_RESOURCE_STOP')
        def stop():
            raise error
        with self.assertRaises(ValueError) as ctx:
            with b.metadata_reader(r):
                r.checkpoint = stop
                r.fresh_pin(H['path'])
        self.assertIs(ctx.exception, error)
        self.assertEqual(r.names, [])

    def test_no_cleanup_overwrite_of_changed_handler(self):
        b = self.opened()
        r = Reader(MODULE.plain(b.whole))
        changed = lambda name, parse=False: None
        with self.assertRaisesRegex(ValueError, 'RESTORE_EXACT'):
            with b.metadata_reader(r):
                r._read = changed
        self.assertIs(r._read, changed)
        self.assertEqual(b.phase, 'BROKEN')

    def test_owner_change_denied(self):
        b = self.opened()
        b.identity = lambda: ('foreign', 'owner')
        with self.assertRaisesRegex(ValueError, 'SAME_PROCESS'):
            b.finish(Reader(MODULE.plain(b.whole)))

    def test_scope_subset_or_new_input_cannot_silently_change_plan(self):
        for mode in ('subset', 'extra'):
            b = self.opened()
            required = MODULE.plain(b.whole)
            if mode == 'subset':
                required.pop(H['path'])
            else:
                required['new.json'] = pin('new.json')
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'EXACT_CURRENT_BATCH_WHOLE'):
                with b.metadata_reader(Reader(MODULE.plain(b.whole))) as r:
                    b.select_current(required, r)

    def test_partial_prior_bootstrap_need_not_contain_future_descriptors(self):
        b = self.opened()
        logical = pin('implementation/p09/evidence/new-current-descriptor.json', 3)
        def full_union(rows, checkpoint):
            if rows.get(logical['path']) != logical:
                raise ValueError('ORIGINAL_ALL_DESCRIPTORS_REQUIRED')
            return rows, {}
        binding = NS(descriptors=lambda: [dict(semantic_original_pin=logical, physical_envelope_pin=N)],
            semantic_union=full_union)
        b.require_preserved([H], binding)
        self.assertEqual(b.bootstrap_memberships, 1)

    def test_bootstrap_projection_is_not_fresh_batch_authority(self):
        b = self.batch()
        binding = NS(descriptors=lambda: [], semantic_union=lambda rows, checkpoint: (rows, {}))
        self.assertEqual(b.bootstrap_declaration([H], binding), {H['path']: H})
        with self.assertRaisesRegex(ValueError, 'BATCH_START_BEFORE_BOOTSTRAP_REUSE'):
            b.require_preserved([H], binding)

    def test_declared_scope_composition_is_not_live_metadata_authority(self):
        b = self.batch()
        binding = NS(descriptors=lambda: [], semantic_union=lambda rows, checkpoint: (rows, {}))
        self.assertEqual(b.scope_declaration({N['path']: N}, binding), MODULE.plain(b.whole))
        with self.assertRaisesRegex(ValueError, 'DECLARATION_SEED_ONLY_INSIDE_AUDITED_METADATA'):
            b.seed_scope_declaration({N['path']: N}, binding)

    def test_history_not_selected_from_code_current_or_future(self):
        for name in ('crates/test.rs', 'tools/p09/old.py', 'fixtures/a.hwpx',
                     H['path'].replace('case114', 'case165'), H['path'].replace('case114', 'case166')):
            hist = pin(name)
            with self.assertRaisesRegex(ValueError, 'EXPLICIT_PRIOR_RECEIPTS_ONLY'):
                MODULE.Batch({name: hist, N['path']: N}, {N['path']: N}, {name: hist},
                    first_index=165, checkpoint=lambda: None)

    def test_partition_overlap_missing_or_changed_pin_denied(self):
        whole = {H['path']: H, N['path']: N}
        for current, history in ((whole, {H['path']: H}), ({N['path']: N}, {}),
                                  ({N['path']: pin(N['path'], 3)}, {H['path']: H})):
            with self.assertRaises(ValueError):
                MODULE.Batch(whole, current, history, first_index=165, checkpoint=lambda: None)

    def test_serialized_frame_never_live_authority(self):
        b = self.opened()
        with self.assertRaises(ValueError):
            b.case_started(165, dict(frame_state='COMMITTED'))
        self.assertEqual(b.phase, 'BROKEN')

    def test_cannot_close_with_live_case(self):
        b = self.opened()
        f = self.frame(b)
        try:
            b.case_started(165, f)
            with self.assertRaisesRegex(ValueError, 'NO_CLOSING_WITH_ACTIVE'):
                b.finish(Reader(MODULE.plain(b.whole)))
        finally:
            f.close()

    def test_incomplete_frame_cannot_finish_case(self):
        b = self.opened()
        f = self.frame(b)
        b.case_started(165, f)
        f.close()
        with self.assertRaises(ValueError):
            b.case_finished(f)
        self.assertEqual(b.phase, 'BROKEN')

    def test_same_case_cannot_be_replayed(self):
        b = self.opened()
        f = self.frame(b)
        b.case_started(165, f)
        self.commit(b, f)
        b.case_finished(f)
        with self.assertRaisesRegex(ValueError, 'BOUNDED_ORDERED'):
            b.case_started(165, f)

    def test_eight_case_bound_is_not_extended(self):
        b = self.opened()
        for i in range(MODULE.MAX_CASES):
            f = self.frame(b)
            b.case_started(165 + i, f)
            self.commit(b, f)
            b.case_finished(f)
        with self.assertRaisesRegex(ValueError, 'BOUNDED_ORDERED'):
            b.case_started(173, None)

    def runtime_fixture(self):
        """Execute the REAL original source body against synthetic IO only."""
        import accept_case112_current_epoch as a
        import current_queue_successor_binding as bindings
        m = MODULE
        names = dict(step='implementation/p09/evidence/p09-361-case165-step-config001.v1.json',
            report='implementation/p09/evidence/current-report.json',
            manifest='implementation/p09/evidence/current-manifest.json',
            capsule='implementation/p09/evidence/current-capsule.json',
            queue='implementation/p09/evidence/current-queue.json',
            prior='implementation/p09/evidence/current-prior.json',
            listing='implementation/p09/evidence/current-listing.json',
            derive='tools/p09/prepare_current_queue_step.py')
        current = {name: pin(name) for name in names.values()}
        current[N['path']] = dict(N)
        rust = {f'crates/synthetic/input{i:03}.rs': pin(f'crates/synthetic/input{i:03}.rs') for i in range(787)}
        current.update(rust)
        whole = {**current, H['path']: H}
        batch = m.Batch(whole, current, {H['path']: H}, first_index=165, checkpoint=lambda: None)
        batch.begin(Reader(whole))
        p = lambda key: dict(current[names[key]])
        step = dict(index=165, prior_queue_pin=p('queue'), prior_candidate_pin=p('prior'))
        docs = {names['report']: dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',
            index=165, cleanup_confirmed=True, accepted_count_delta=0, product_or_Native_executed=False,
            GO_authorized=False, step=step, manifest_pin=p('manifest'), fresh_inputs=2, final_fresh_hashes=2,
            source_pins=[p('derive')], capsule_pin=p('capsule')),
            names['manifest']: dict(descriptors=[], historical_predecessor_provenance={}),
            names['queue']: dict(fresh_input_pins=[p('queue')]),
            names['prior']: dict(source_input_representation=dict(semantic_source_freeze=list(whole.values()), descriptors=[]),
                bootstrap_metadata=dict(input_pins=[H])),
            names['listing']: dict(source_test_names=['synthetic'] * 249),
            names['derive']: 'synthetic derivation source, not execution evidence'}
        fake_a = NS(exact=a.exact, fields=a.fields, read_exact=a.read_exact,
            native=NS(definitions=lambda *args: NS(derive_step=lambda *values: copy.deepcopy(step))))
        fake_scope = NS(pins=m.scope.pins, extend=m.scope.extend, require=m.scope.require,
            LIST_PIN=p('listing'), EXE_PIN=dict(N), listing_inputs=lambda value: copy.deepcopy(rust))
        fake_binding = NS(PROVENANCE_KEYS=bindings.PROVENANCE_KEYS, inherited_scope=bindings.inherited_scope)
        modules = dict(accept_case112_current_epoch=fake_a, current_stored_runtime_scope=fake_scope,
            current_queue_successor_binding=fake_binding)
        ordinary = builtins.__import__
        def imported(name, globals=None, locals=None, fromlist=(), level=0):
            return modules[name] if level == 0 and name in modules else ordinary(name, globals, locals, fromlist, level)
        env = dict(__builtins__={**vars(builtins), '__import__': imported}, metadata=NS(require=m.require))
        node = next(n for n in ast.parse(RAW_RUNTIME).body if isinstance(n, ast.FunctionDef) and n.name == 'current_input_scope')
        exec(compile(ast.Module(body=[node], type_ignores=[]), m.RUNTIME, 'exec'), env)
        runtime = NS(current_input_scope=env['current_input_scope'])
        graph = NS(binding=NS(next_case=165, manifest_pin=p('manifest'), descriptors=lambda: [],
            semantic_union=lambda rows, checkpoint: (copy.deepcopy(rows), {})))
        args = (graph, step, p('report'), p('manifest'), {names['step']: p('step'), names['derive']: p('derive')})
        return batch, runtime, Reader(whole, docs), args, names

    def test_real_original_scope_keeps_other_checks_but_stops_whole_bootstrap_io(self):
        batch, runtime, reader, args, _ = self.runtime_fixture()
        original = runtime.current_input_scope
        baseline_reader = Reader(reader.rows, reader.docs)
        old_whole, old_rust = original(baseline_reader, *args)
        self.assertIn(H['path'], baseline_reader.names)
        updated, proof = MODULE.install_scope(runtime, RAW_RUNTIME, batch)
        current, rust = updated.current_input_scope(reader, *args)
        self.assertEqual(old_rust, rust)
        self.assertEqual(len(rust), 787)
        self.assertEqual({**current, **MODULE.plain(batch.history)}, old_whole)
        self.assertNotIn(H['path'], reader.names)
        self.assertEqual(batch.bootstrap_memberships, 1)
        self.assertEqual(batch.scope_selections, 1)
        self.assertIs(runtime.current_input_scope, original)
        self.assertIs(proof['exact_original_AST_inverse'], True)
        self.assertIs(proof['actual_parent_worker_or_Native_connected'], False)

    def test_original_parent_report_checks_are_not_skipped(self):
        batch, runtime, reader, args, names = self.runtime_fixture()
        reader.docs[names['report']]['cleanup_confirmed'] = False
        updated, _ = MODULE.install_scope(runtime, RAW_RUNTIME, batch)
        with self.assertRaises(ValueError):
            updated.current_input_scope(reader, *args)
        self.assertEqual(batch.phase, 'BROKEN')

    def test_prior_declaration_does_not_need_to_predict_current_programs(self):
        batch, runtime, reader, args, names = self.runtime_fixture()
        rows = reader.docs[names['prior']]['source_input_representation']['semantic_source_freeze']
        reader.docs[names['prior']]['source_input_representation']['semantic_source_freeze'] = [p for p in rows
            if p['path'] != 'crates/synthetic/input786.rs']
        updated, _ = MODULE.install_scope(runtime, RAW_RUNTIME, batch)
        current, _ = updated.current_input_scope(reader, *args)
        self.assertIn('crates/synthetic/input786.rs', current)
        self.assertNotIn(H['path'], current)

    def test_derived_unplanned_pin_cannot_be_dropped_by_declaration_seed(self):
        batch, runtime, reader, args, names = self.runtime_fixture()
        reader.docs[names['prior']]['source_input_representation']['semantic_source_freeze'].append(pin('unknown-derived.json'))
        updated, _ = MODULE.install_scope(runtime, RAW_RUNTIME, batch)
        with self.assertRaisesRegex(ValueError, 'DERIVED_SCOPE_MUST_MATCH_DECLARED_PLAN'):
            updated.current_input_scope(reader, *args)

    def test_changed_prior_bootstrap_not_accepted_from_initial_membership(self):
        batch, runtime, reader, args, names = self.runtime_fixture()
        reader.docs[names['prior']]['bootstrap_metadata']['input_pins'][0]['sha256'] = 'a' * 64
        updated, _ = MODULE.install_scope(runtime, RAW_RUNTIME, batch)
        with self.assertRaisesRegex(ValueError, 'EVERY_PRIOR_BOOTSTRAP_PIN_PRESERVED'):
            updated.current_input_scope(reader, *args)

    def test_additional_unplanned_preparation_input_stops_before_io(self):
        batch, runtime, reader, args, names = self.runtime_fixture()
        reader.docs[names['report']]['source_pins'].append(pin('implementation/p09/evidence/new-unplanned.json'))
        updated, _ = MODULE.install_scope(runtime, RAW_RUNTIME, batch)
        with self.assertRaisesRegex(ValueError, 'PRESERVATION_OR_UNDECLARED'):
            updated.current_input_scope(reader, *args)
        self.assertNotIn('implementation/p09/evidence/new-unplanned.json', reader.names)

    def test_source_tampering_or_preexisting_function_patch_rejected(self):
        batch, runtime, _, _, _ = self.runtime_fixture()
        with self.assertRaisesRegex(ValueError, 'EXACT_ORIGINAL_SCOPE_SOURCE'):
            MODULE.install_scope(runtime, RAW_RUNTIME + b'\n', batch)
        runtime.current_input_scope = lambda *args: ({}, set())
        with self.assertRaisesRegex(ValueError, 'NO_PRIOR_FUNCTION_PATCH'):
            MODULE.install_scope(runtime, RAW_RUNTIME, batch)

    def test_boolean_numeric_or_signature_patch_not_equal_original_code(self):
        for mode in ('boolean', 'signature'):
            batch, runtime, _, _, _ = self.runtime_fixture()
            fn = runtime.current_input_scope
            if mode == 'boolean':
                self.assertTrue(any(type(v) is bool for v in fn.__code__.co_consts))
                code = fn.__code__.replace(co_consts=tuple(int(v) if type(v) is bool else v
                    for v in fn.__code__.co_consts))
            else:
                code = fn.__code__.replace(co_posonlyargcount=1)
            runtime.current_input_scope = MODULE.FunctionType(code, fn.__globals__)
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'NO_PRIOR_FUNCTION_PATCH'):
                MODULE.install_scope(runtime, RAW_RUNTIME, batch)

    def namespace_fixture(self, *, mode='rb'):
        name = 'tools/p09/synthetic_namespace_example.py'
        raw = b'value = 17\n'
        expected = dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        reader = Reader({name: expected}, {name: raw})
        observations = []
        def load(root, pins, reuse):
            observations.append(reader.maximum_parse_bytes)
            with (root / pins[0]['path']).open(mode) as stream:
                source = stream.read(pins[0]['bytes'] + 1)
            if len(source) != pins[0]['bytes'] or hashlib.sha256(source).hexdigest() != pins[0]['sha256']:
                raise ValueError('ORIGINAL_NAMESPACE_SOURCE_HASH')
            return NS(source=source), []
        original = NS(load=load)
        paced = MODULE.PacedNamespaceLoader(original, reader, {name: expected})
        return paced, reader, expected, raw, observations, original

    def test_namespace_source_opens_are_fresh_not_a_byte_cache(self):
        paced, reader, p, raw, _, original = self.namespace_fixture()
        fn = original.load
        for _ in range(2):
            value, _ = paced.api.load(reader.root, [p], {})
            self.assertEqual(value.source, raw)
        self.assertEqual(reader.read_passes, 2)
        self.assertEqual(paced.source_reads, 2)
        self.assertIs(original.load, fn)

    def test_namespace_unqualified_pin_or_root_denied_before_io(self):
        for mode in ('pin', 'root'):
            paced, reader, p, _, _, _ = self.namespace_fixture()
            root = reader.root
            if mode == 'pin':
                p = dict(p, sha256='a' * 64)
            else:
                root = Path('D:/not-the-reader-root')
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                paced.api.load(root, [p], {})
            self.assertEqual(reader.read_passes, 0)

    def test_namespace_reader_budget_is_lowered_then_restored(self):
        paced, reader, p, _, _, _ = self.namespace_fixture()
        before = reader.maximum_parse_bytes
        original = reader._read
        caps = []
        def checked(name, parse=False):
            caps.append(reader.maximum_parse_bytes)
            return original(name, parse=parse)
        reader._read = checked
        paced.api.load(reader.root, [p], {})
        self.assertEqual(caps, [p['bytes'] + 1])
        self.assertEqual(reader.maximum_parse_bytes, before)

    def test_namespace_original_read_error_and_parse_limit_preserved(self):
        paced, reader, p, _, _, _ = self.namespace_fixture()
        before = reader.maximum_parse_bytes
        error = ValueError('ORIGINAL_READER_STOP')
        def stop(name, parse=False):
            raise error
        reader._read = stop
        with self.assertRaises(ValueError) as ctx:
            paced.api.load(reader.root, [p], {})
        self.assertIs(ctx.exception, error)
        self.assertEqual(reader.maximum_parse_bytes, before)

    def test_namespace_writes_are_denied_before_io(self):
        paced, reader, p, _, _, _ = self.namespace_fixture(mode='wb')
        with self.assertRaisesRegex(ValueError, 'NAMESPACE_READ_ONLY'):
            paced.api.load(reader.root, [p], {})
        self.assertEqual(reader.read_passes, 0)

    def test_namespace_bound_and_original_hash_check_are_not_removed(self):
        for mode in ('size', 'bytes'):
            paced, reader, p, _, _, _ = self.namespace_fixture()
            if mode == 'size':
                p = dict(p, bytes=65537)
                paced.allowed[p['path']] = p
            else:
                reader.docs[p['path']] = b'changed!!!'
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                paced.api.load(reader.root, [p], {})
