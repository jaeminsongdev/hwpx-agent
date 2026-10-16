"""Synthetic policy/real source-body contracts, NOT Native/product evidence."""
import ast
import builtins
import copy
from contextlib import contextmanager
from types import SimpleNamespace as NS
import unittest

MODULE = None
RAW_RUNTIME = None


def pin(name, size=1):
    return dict(path=name, bytes=size, sha256='0' * 64)


H = pin('implementation/p09/evidence/p09-361-case114-current-runtime-run001.v1.json')
N = pin('target/current.exe', 2)


class Reader:
    """No disk access. Counters model original readers for isolated contracts."""
    def __init__(self, rows, docs=None):
        self.rows = copy.deepcopy(rows)
        self.docs = {} if docs is None else copy.deepcopy(docs)
        self.snapshots = {}
        self.read_passes = self.bytes_read = 0
        self.names = []
        self.checkpoint = lambda: None
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
