"""Explicit batch preservation policy; no process/GO/queue execution.

Whole history is freshly hashed at batch start/end. Each product case still
needs the original live Frame and its two complete CURRENT-input boundaries.
No per-case acceptance is granted before batch closing. A metadata read of a
preservation-only/undeclared file fails before its original IO.

The opt-in scope adapter changes explicit policy slots in the original body:
prior-bootstrap freshness -> checked batch membership; approved declaration
seed -> complete current schema; whole -> current scope.
Every other AST statement is retained, with a lossless inverse check.
"""
import ast
import copy
from contextlib import contextmanager
import hashlib
import os
import threading
from types import FunctionType, MappingProxyType, MethodType, SimpleNamespace as NS

import current_stored_runtime_scope as scope
import historical_receipt_batch_partition_v1 as partition
import phased_preservation_read_gate_v2 as phased

SELF = 'tools/p09/batch_verification.py'
TEST = 'tools/p09/tests/test_batch_verification.py'
RUNTIME = 'tools/p09/current_queue_successor_runtime.py'
RUNTIME_SHA = '523fbe57dc31f73612651cf44dbca9a85fe706a40e563f391ccade2aa0cf63df'
MAX_CASES = 8
ENGINE = 'tools/p09/native009_engine_connection_v1.py'
ENGINE_SHA = 'fee9a1af80ec92b7422db8d4b707422c8b7efe1699fa17336b2a38b258baff18'
# Exact committed blob 285e193180038bc069934986c4f55e043f6943af.
# The original historical controller reads this configuration during assembly.
# It is a NEW current input, never retroactive Native009 source qualification.
LEGACY_CONFIG = dict(path='implementation/p09/evidence/p09-361-case160-run007-graph-config-r388.v1.json',
    bytes=561, sha256='227220e7949895b6b2fbd66e4e7b27678100f2b0e8f43034103e049871f14a09')


def require(ok, code):
    if not ok:
        raise ValueError('BATCH_VERIFY_' + code)


def frozen(rows):
    checked = scope.pins(list(rows.values()))
    require(checked == rows and len({n.casefold() for n in checked}) == len(checked), 'EXACT_UNALIASED_MAPPING')
    return MappingProxyType({n: MappingProxyType(p) for n, p in checked.items()})


def plain(rows):
    return {n: dict(p) for n, p in rows.items()}


class Batch:
    def __init__(self, whole, current, history, *, first_index, checkpoint,
                 identity=lambda: (os.getpid(), threading.get_ident())):
        require(callable(checkpoint) and callable(identity), 'ORIGINAL_CHECKPOINT_AND_OWNER')
        require(type(first_index) is int and 161 <= first_index <= 249, 'CURRENT_FIRST_INDEX')
        self.whole = frozen(whole)
        self.current = frozen(current)
        self.history = frozen(history) if history else MappingProxyType({})
        require(not set(current) & set(history) and {**current, **history} == whole, 'LOSSLESS_DISJOINT_PARTITION')
        for name in history:
            eligible = any((match := pattern.fullmatch(name)) and 1 <= int(match[1]) < first_index
                           for _, pattern in partition.PATTERNS)
            require(eligible, 'EXPLICIT_PRIOR_RECEIPTS_ONLY_NOT_PRODUCT_CODE_OR_FIXTURES')
        self.first_index = first_index
        self.checkpoint = checkpoint
        self.identity = identity
        self.owner = identity()
        self.phase = 'NEW'
        self.initial = self.final = None
        self.initial_reader = None
        self.active = None
        self.cases = []
        self.metadata_reader_active = False
        self.parent_connection = None
        self.metadata_reads = self.bootstrap_memberships = self.scope_selections = 0

    def connect_parent(self, engine, graph, *, connect_lifecycle=True):
        """Bind the exact class constructed by the existing private parent.

        Construction only: this does not execute run_owned, acquire a Frame,
        install raw policy, or supply product permission. The graph must be
        admitted through the original pinned namespace loader by the caller.
        No default module/class is patched and arbitrary subclasses are not
        accepted. Default lifecycle hooks call the unchanged acquisition and
        commit bodies, then notify this batch at their actual boundaries.
        """
        self.check()
        require(type(connect_lifecycle) is bool, 'EXPLICIT_PARENT_LIFECYCLE_MODE')
        require(self.phase == 'NEW' and self.initial is None and self.parent_connection is None,
            'PARENT_CONNECTION_ONCE_BEFORE_BATCH_START')
        require(type(graph.binding.next_case) is int and graph.binding.next_case == self.first_index,
            'EXACT_PARENT_FIRST_CASE_BINDING')
        original = engine.run_owned
        require(type(original) is FunctionType, 'ORIGINAL_PARENT_FUNCTION')
        original_frames = original.__globals__['native'].frames
        base = original_frames.Frame
        reference = phased.frames.Frame
        require(type(base) is type and base.__mro__ == (base, object)
            and set(vars(base)) == set(vars(reference)), 'ORIGINAL_FRAME_CLASS_LAYOUT')
        for name, expected in vars(reference).items():
            if type(expected) is FunctionType:
                actual = vars(base)[name]
                require(type(actual) is FunctionType
                    and _code_shape(actual.__code__) == _code_shape(expected.__code__)
                    and actual.__defaults__ == expected.__defaults__
                    and actual.__closure__ is expected.__closure__, 'ORIGINAL_FRAME_METHOD_BODIES')
        parent, state = graph.parent.connect_engine(engine, graph.binding)
        connected = parent.run_owned
        require(type(connected) is FunctionType and connected.__closure__ is not None
            and state.original is original and state.original_worker is engine.worker
            and parent.worker is engine.worker and state.frames == [] and state.attempts == 0,
            'PARENT_CONSTRUCTED_NOT_EXECUTED')
        closure = dict(zip(connected.__code__.co_freevars,
            (cell.cell_contents for cell in connected.__closure__)))
        frame_type = closure['native'].frames.Frame
        require(type(frame_type) is type and len(frame_type.__mro__) == 4
            and frame_type.__mro__[2:] == (base, object)
            and closure['state'] is state, 'EXACT_PARENT_PROJECTED_ORIGINAL_FRAME_CHAIN')
        original_acquire, original_commit, original_close = frame_type.acquire, frame_type.commit, frame_type.close
        committing = []
        if connect_lifecycle:
            def acquire(frame):
                self.check()
                require(self.phase == 'READY' and self.active is None and not self.metadata_reader_active,
                    'AUDITED_READY_BEFORE_PARENT_ACQUIRE')
                try:
                    self._check_parent_frame(frame)
                    result = original_acquire(frame)
                    self.case_started(self.first_index, frame)
                    return result
                except BaseException:
                    self.phase = 'BROKEN'
                    raise
            def commit(frame, owned):
                self.check()
                require(self.phase == 'CASE_ACTIVE' and self.active is not None
                    and self.active[1] is frame and not committing, 'EXACT_PARENT_COMMIT_OWNER')
                try:
                    self._check_parent_frame(frame)
                    committing.append(frame)
                    result = original_commit(frame, owned)
                    self.case_finished(frame)
                    return result  # Do not rewrite the original terminal row.
                except BaseException:
                    self.phase = 'BROKEN'
                    raise
                finally:
                    committing.clear()
            def close(frame):
                try:
                    return original_close(frame)
                finally:
                    # An abort is never an accepted/closable batch, even if the
                    # original runner successfully releases all native handles.
                    if self.active is not None and self.active[1] is frame and not committing:
                        self.phase = 'BROKEN'
            frame_type.acquire, frame_type.commit, frame_type.close = acquire, commit, close
        self.parent_connection = NS(parent=parent, state=state, frame_type=frame_type,
            registry_type=original_frames.Registry,
            lifecycle_connected=connect_lifecycle,
            original_acquire=original_acquire, original_commit=original_commit, original_close=original_close,
            classes=tuple((cls, dict(vars(cls))) for cls in frame_type.__mro__[:-1]),
            methods=tuple((value, value.__code__, value.__defaults__, value.__closure__,
                dict(value.__kwdefaults__) if value.__kwdefaults__ is not None else None)
                for cls in frame_type.__mro__[:-1] for value in vars(cls).values()
                if type(value) is FunctionType))
        return parent, state

    def _check_parent_frame(self, frame):
        connection = self.parent_connection
        if connection is not None:
            require(all(set(vars(cls)) == set(saved)
                and all(vars(cls)[name] is value for name, value in saved.items())
                for cls, saved in connection.classes), 'UNCHANGED_CONNECTED_FRAME_CLASSES')
            require(all(fn.__code__ is code and fn.__defaults__ is defaults and fn.__closure__ is closure
                and fn.__kwdefaults__ == keywords for fn, code, defaults, closure, keywords in connection.methods),
                'UNCHANGED_CONNECTED_FRAME_METHOD_CODE')
            require(type(frame) is connection.frame_type
                and type(frame.registry) is connection.registry_type
                and connection.state.attempts == 1 and len(connection.state.frames) == 1
                and connection.state.frames[0] is frame, 'EXACT_OWNED_PARENT_FRAME_REFERENCE')
            methods = {name for _, saved in connection.classes for name, value in saved.items()
                if type(value) is FunctionType}
            require(not methods.intersection(vars(frame)), 'NO_INSTANCE_FRAME_METHOD_REPLACEMENT')
        return connection

    def _case_gate(self, frame):
        gate = phased.Gate(plain(self.whole), plain(self.current), plain(self.history), identity=self.identity)
        connection = self._check_parent_frame(frame)
        if connection is not None:
            original = phased.original.Gate.native_started
            # Keep the entire original check, including exact type, owner,
            # live registry/handles and current scope. Only the private class
            # dependency is bound to this parent's constructed class.
            private = FunctionType(original.__code__, dict(original.__globals__,
                frames=NS(Frame=connection.frame_type)), argdefs=original.__defaults__, closure=original.__closure__)
            gate.native_started = MethodType(private, gate)
        return gate

    def check(self):
        # Resource errors take precedence over policy decisions.
        self.checkpoint()
        require(self.identity() == self.owner, 'SAME_PROCESS_AND_THREAD')
        require(self.phase != 'BROKEN', 'BROKEN_BATCH_NO_RETRY')

    def _boundary(self, reader):
        """One complete fresh boundary, not a reused hash/finished qualifier.

        Start and end are the two batch-wide boundaries. They use different
        fresh original readers, allowing separate serial resource epochs. Do
        not claim either one alone as an old two-pass qualification receipt.
        """
        self.check()
        require(reader is not self.initial_reader and reader.read_passes == reader.bytes_read == 0
            and reader.snapshots == {}, 'FRESH_DISTINCT_WHOLE_BOUNDARY_READER')
        observed = {}
        for name, expected in self.whole.items():
            self.check()
            actual = reader.fresh_pin(name)
            require(actual == dict(expected), 'WHOLE_BOUNDARY_CHANGED_OR_MISSING')
            observed[name] = dict(actual)
        require(reader.read_passes == len(self.whole)
            and reader.bytes_read == sum(p['bytes'] for p in self.whole.values())
            and reader.snapshots == observed, 'WHOLE_ACTUAL_READ_ACCOUNTING')
        self.check()
        return observed

    def begin(self, reader):
        self.check()
        require(self.phase == 'NEW', 'ONE_BATCH_START')
        try:
            self.phase = 'OPENING'
            self.initial = self._boundary(reader)
            self.initial_reader = reader
            self.phase = 'READY'
        except BaseException:
            self.phase = 'BROKEN'
            raise

    @contextmanager
    def metadata_reader(self, reader, binding=None):
        self.check()
        require(self.phase == 'READY' and not self.metadata_reader_active, 'READY_METADATA_OWNER_ONLY')
        aliases = self._metadata_aliases(binding)
        old = reader._read
        self.metadata_reader_active = True
        def guarded(name, parse=False):
            try:
                reader.checkpoint()
                self.check()
                require(self.phase == 'READY' and reader._read is guarded, 'UNCHANGED_METADATA_BINDING')
                expected, physical = aliases.get(name, (self.current.get(name), name))
                require(physical in self.current and expected is not None,
                    'PRESERVATION_OR_UNDECLARED_READ_REQUIRES_NEW_PLAN')
                actual, buffer = old(name, parse=parse)
                require(actual == dict(expected), 'CURRENT_METADATA_BYTES_CHANGED')
                self.metadata_reads += 1
                return actual, buffer
            except BaseException:
                self.phase = 'BROKEN'
                raise
        reader._read = guarded
        try:
            yield reader
        except BaseException:
            self.phase = 'BROKEN'
            raise
        finally:
            self.metadata_reader_active = False
            # Never overwrite somebody else's handler during cleanup.
            if reader._read is not guarded:
                self.phase = 'BROKEN'
                require(False, 'RESTORE_EXACT_METADATA_HANDLER')
            reader._read = old

    def _metadata_aliases(self, binding):
        """Keep logical receipt names while guarding their declared carriers.

        The original reader still verifies/decodes the bytes. Descriptor data
        alone is not a fresh byte observation or permission for a cold carrier.
        """
        if binding is None:
            return {}
        descriptors = binding.descriptors()
        require(type(descriptors) is list and len(descriptors) <= 249, 'BOUNDED_METADATA_DESCRIPTORS')
        aliases = {}
        physical_names = set()
        for row in descriptors:
            require(type(row) is dict and 'semantic_original_pin' in row and 'physical_envelope_pin' in row,
                'EXPLICIT_METADATA_DESCRIPTOR')
            semantic = scope.pins([row['semantic_original_pin']])
            physical = scope.pins([row['physical_envelope_pin']])
            name, original = next(iter(semantic.items()))
            path, carrier = next(iter(physical.items()))
            require(name not in aliases and path not in physical_names,
                'UNIQUE_LOGICAL_AND_PHYSICAL_METADATA_NAMES')
            require(self.whole.get(path) == carrier, 'METADATA_CARRIER_INSIDE_EXACT_WHOLE')
            require(name not in self.whole or self.whole[name] == original,
                'NO_LOGICAL_METADATA_PIN_COLLISION')
            aliases[name] = (original, path)
            physical_names.add(path)
        return aliases

    def require_preserved(self, bootstrap_rows, binding):
        self.check()
        require(self.phase == 'READY' and self.initial is not None, 'BATCH_START_BEFORE_BOOTSTRAP_REUSE')
        physical = self.bootstrap_declaration(bootstrap_rows, binding)
        require(all(self.initial.get(n) == p for n, p in physical.items()), 'EVERY_PRIOR_BOOTSTRAP_PIN_PRESERVED')
        self.bootstrap_memberships += 1

    def bootstrap_declaration(self, bootstrap_rows, binding):
        """Declaration-only check; it never substitutes for begin()."""
        self.check()
        declared = scope.pins(bootstrap_rows)
        aliases = self._metadata_aliases(binding)
        # A prior bootstrap predates some current descriptors. Seed only the
        # already declared current originals so the unchanged full Binding can
        # normalize old physical aliases without requiring the prior document
        # to have predicted future evidence. Every seeded carrier is in whole.
        seeded = scope.extend(declared, {n: dict(value[0]) for n, value in aliases.items()}) if aliases else declared
        normalized, _ = binding.semantic_union(seeded, self.checkpoint)
        physical = {}
        for name, pin in normalized.items():
            expected, path = aliases.get(name, (pin, name))
            require(dict(expected) == pin, 'EXACT_BOOTSTRAP_LOGICAL_PIN')
            actual = dict(self.whole[path]) if name in aliases else dict(pin)
            require(self.whole.get(path) == actual, 'EVERY_PRIOR_BOOTSTRAP_PIN_PRESERVED')
            require(path not in physical or physical[path] == actual, 'NO_BOOTSTRAP_PHYSICAL_COLLISION')
            physical[path] = actual
        return physical

    def select_current(self, required, reader, binding=None):
        self.check()
        require(self.phase == 'READY' and self.metadata_reader_active, 'SELECT_INSIDE_CHECKED_METADATA')
        aliases = self._metadata_aliases(binding)
        checked = scope.pins(list(required.values()))
        projected = {}
        selected = {}
        for name, pin in checked.items():
            expected, physical = aliases.get(name, (pin, name))
            require(dict(expected) == pin, 'EXACT_LOGICAL_INPUT_PIN_BEFORE_PHYSICAL_SELECTION')
            physical_pin = dict(self.whole[physical]) if name in aliases else pin
            require(physical not in projected or projected[physical] == physical_pin, 'NO_SCOPE_ALIAS_COLLISION')
            projected[physical] = physical_pin
            if physical in self.current:
                selected[name] = dict(pin)
        require(projected == plain(self.whole), 'EXACT_CURRENT_BATCH_WHOLE_NOT_SUBSET_OR_NEW_INPUT')
        for name, pin in reader.snapshots.items():
            expected, physical = aliases.get(name, (self.current.get(name), name))
            require(physical in self.current and expected is not None and dict(expected) == pin,
                'ALL_OBSERVED_CURRENT_INPUTS_DECLARED')
        if binding is not None:
            normalized, _ = binding.semantic_union(selected, self.checkpoint)
            require(normalized == selected, 'CURRENT_SCOPE_MUST_NOT_REINTRODUCE_HISTORY')
        self.scope_selections += 1
        return selected

    def seed_scope_declaration(self, required, binding):
        """Compose the approved declaration, never new IO/freshness evidence.

        A prior candidate cannot list later policy programs/evidence. Validate
        its derived pins first, then use the batch's explicitly declared whole
        table. The immediately following selection excludes preservation-only
        inputs again, and the real Binding must not re-inject them afterwards.
        """
        self.check()
        require(self.phase == 'READY' and self.metadata_reader_active and self.initial is not None,
            'DECLARATION_SEED_ONLY_INSIDE_AUDITED_METADATA')
        return self.scope_declaration(required, binding)

    def scope_declaration(self, required, binding):
        """Inspect declaration composition without claiming a fresh boundary."""
        self.check()
        aliases = self._metadata_aliases(binding)
        declared = scope.pins(list(required.values()))
        seeded = scope.extend(declared, {n: dict(value[0]) for n, value in aliases.items()}) if aliases else declared
        normalized, _ = binding.semantic_union(seeded, self.checkpoint)
        by_carrier = {path: original for original, path in aliases.values()}
        logical_whole = {}
        for name, pin in self.whole.items():
            original = by_carrier.get(name, pin)
            require(original['path'] not in logical_whole
                or logical_whole[original['path']] == dict(original), 'NO_SEEDED_LOGICAL_COLLISION')
            logical_whole[original['path']] = dict(original)
        require(all(logical_whole.get(n) == p for n, p in normalized.items()), 'DERIVED_SCOPE_MUST_MATCH_DECLARED_PLAN')
        return logical_whole

    def case_started(self, index, frame):
        self.check()
        require(self.phase == 'READY' and not self.metadata_reader_active and self.active is None, 'SERIAL_CASE_START')
        require(type(index) is int and index == self.first_index + len(self.cases)
            and index <= 249 and len(self.cases) < MAX_CASES, 'BOUNDED_ORDERED_CASE_NO_REPLAY')
        try:
            gate = self._case_gate(frame)
            gate.native_started(list(self.initial.values()), frame)
        except BaseException:
            self.phase = 'BROKEN'
            raise
        self.active = (index, frame, gate)
        self.phase = 'CASE_ACTIVE'

    def case_finished(self, frame):
        self.check()
        require(self.phase == 'CASE_ACTIVE' and self.active is not None
            and self.active[1] is frame, 'SAME_ACTIVE_CASE_FRAME')
        try:
            index, _, gate = self.active
            if self.parent_connection is not None:
                self._check_parent_frame(frame)
            gate.native_finished(frame)
            self.cases.append((index, gate))
            self.active = None
            self.phase = 'READY'
        except BaseException:
            self.phase = 'BROKEN'
            raise

    def finish(self, reader):
        self.check()
        require(self.phase == 'READY' and self.active is None and not self.metadata_reader_active,
            'NO_CLOSING_WITH_ACTIVE_FRAME_OR_READER')
        try:
            self.phase = 'CLOSING'
            self.final = self._boundary(reader)
            require(self.final == self.initial, 'EXACT_WHOLE_AT_BOTH_BATCH_BOUNDARIES')
            for _, gate in self.cases:
                gate.finish(list(self.final.values()))
            self.phase = 'SOURCE_BOUNDARIES_COMPLETE_NOT_ACCEPTED' if self.cases else 'EMPTY_BATCH_AUDITED_NOT_ACCEPTED'
        except BaseException:
            self.phase = 'BROKEN'
            raise
        return self.summary()

    def _closed_oracle_case(self, index):
        self.check()
        require(self.phase == 'SOURCE_BOUNDARIES_COMPLETE_NOT_ACCEPTED'
            and self.active is None and not self.metadata_reader_active
            and self.initial == plain(self.whole) and self.final == plain(self.whole),
            'COMPLETE_WHOLE_BOUNDARIES_BEFORE_ORACLE')
        matches = [gate for case, gate in self.cases if case == index]
        require(len(matches) == 1 and matches[0].phase == 'CONTRACT_COMPLETE_NOT_ACCEPTED',
            'EXACT_COMPLETED_CASE_BEFORE_ORACLE')
        frame = matches[0].frame
        if self.parent_connection is not None:
            self._check_parent_frame(frame)
        require(frame.state == 'COMMITTED' and not frame.registered and frame.held.closed
            and frame.owned_cleanup_seen is True, 'SAME_COMMITTED_FRAME_BEFORE_ORACLE')

    def _closed_oracle_scope(self, joined, binding, index):
        """Keep independent whole expectations; select only after batch close."""
        self._closed_oracle_case(index)
        normalized, _ = binding.semantic_union(joined, self.checkpoint)
        projection, _ = binding.project(normalized, self.checkpoint)
        require(plain(projection.physical_pins) == plain(self.whole),
            'INDEPENDENT_ORACLE_WHOLE_EXACT_NOT_CANDIDATE_DERIVED')
        aliases = self._metadata_aliases(binding)
        selected = {n: dict(p) for n, p in normalized.items()
            if aliases.get(n, (p, n))[1] in self.current}
        current, _ = binding.project(selected, self.checkpoint)
        require(plain(current.physical_pins) == plain(self.current), 'INDEPENDENT_ORACLE_CURRENT_EXACT')
        return selected

    def connect_full_oracle(self, original, binding, *, index):
        """Connect existing full checker without changing candidate records.

        The original generator/checker, explicit envelope evidence, budget and
        terminal predicates still execute. The sole new policy dependency is
        whole -> current selection after the independently computed whole
        scope matches BOTH batch boundaries and the completed live case.
        Connection itself grants no qualification, execution or acceptance.
        """
        self.check()
        require(type(index) is int and index == self.first_index and binding.next_case == index,
            'EXACT_FIRST_CASE_ORACLE_CONNECTION')
        require(type(original.projector) is FunctionType, 'ORIGINAL_FULL_ORACLE_PROJECTOR')
        batch = self
        def projector(generator, supplied_binding, complete_budget, checkpoint, *, mechanics_projection=None):
            batch.check()
            require(supplied_binding is binding and type(generator) is FunctionType,
                'SAME_BOUND_ORACLE_AND_GENERATOR')
            env = generator.__globals__
            metadata_scope = env['original'].scope
            observed = NS(whole_scope_checks=0, checker_calls=0)
            def extend(required, added):
                checkpoint()
                joined = metadata_scope.extend(required, added)
                selected = batch._closed_oracle_scope(joined, binding, index)
                observed.whole_scope_checks += 1
                return selected
            metadata = NS(**{**vars(metadata_scope), 'extend': extend})
            private = FunctionType(generator.__code__, dict(env,
                original=NS(**{**vars(env['original']), 'scope': metadata})),
                argdefs=generator.__defaults__, closure=generator.__closure__)
            private.__kwdefaults__ = generator.__kwdefaults__
            project, state = original.projector(private, binding, complete_budget, checkpoint,
                mechanics_projection=mechanics_projection)
            def closed_project(raw, row, listing, body):
                # Reaching the generator itself before closing is forbidden;
                # otherwise a generator without extend() could bypass the gate.
                batch._closed_oracle_case(index)
                before = observed.whole_scope_checks
                try:
                    check, proof = project(raw, row, listing, body)
                    require(observed.whole_scope_checks > before, 'INDEPENDENT_WHOLE_SCOPE_MUST_BE_CHECKED')
                except BaseException:
                    batch.phase = 'BROKEN'
                    raise
                def execute(candidate, current_listing, old_body, fresh, guard):
                    try:
                        batch._closed_oracle_case(index)
                        observed.checker_calls += 1
                        return check(candidate, current_listing, old_body, fresh, guard)
                    except BaseException:
                        batch.phase = 'BROKEN'
                        raise
                return execute, dict(proof, approved_batch_preservation_policy_connected=True,
                    independent_whole_expectations_checked_before_current_selection=True,
                    whole_batch_boundaries_and_original_case_commit_required=True,
                    candidate_row_or_counters_rewritten=False, queue_acceptance_authorized=False)
            return closed_project, NS(original=state, batch=observed)
        return NS(**{**vars(original), 'projector': projector})

    def summary(self):
        return dict(phase=self.phase, whole_inputs=len(self.whole), current_inputs=len(self.current),
            preservation_inputs=len(self.history), cases_with_original_Frame_checks=len(self.cases),
            whole_initial_complete=self.initial is not None, whole_final_complete=self.final is not None,
            metadata_reads=self.metadata_reads, prior_bootstrap_membership_checks=self.bootstrap_memberships,
            current_scope_selections=self.scope_selections, accepted_count_delta=0,
            exact_parent_frame_class_connected=self.parent_connection is not None,
            parent_lifecycle_connected=self.parent_connection is not None and self.parent_connection.lifecycle_connected,
            queue_advance_authorized=False, GO_authorized=False, product_execution_authorized=False,
            independent_product_and_acceptance_oracles_still_required=True)


def _constant_shape(value):
    from types import CodeType
    if isinstance(value, CodeType):
        return (CodeType, _code_shape(value))
    if type(value) in (tuple, frozenset):
        return (type(value), type(value)(_constant_shape(v) for v in value))
    return (type(value), value)


def _code_shape(code):
    return (code.co_code, tuple(_constant_shape(v) for v in code.co_consts),
        code.co_names, code.co_varnames, code.co_freevars, code.co_cellvars,
        code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount,
        code.co_flags, code.co_exceptiontable, code.co_stacksize, code.co_nlocals,
        code.co_name, code.co_qualname)


def prepare_engine_builder(raw, runtime, raw_runtime):
    """Prepare the full original builder for future165/010/162, never run it.

    Only three typed metadata slots and the private TASK/ROOT dependency change.
    Inverse checks are positional, so the existing numeric product10 constant
    is NOT accidentally changed when the run9 slot becomes10. Existing-result,
    identity, single construction, worker cleanup/state and product10 checks
    stay in the complete original body. This is not graph/transport admission.
    """
    require(type(raw) is bytes and len(raw) == 9522 and hashlib.sha256(raw).hexdigest() == ENGINE_SHA,
        'EXACT_ORIGINAL_ENGINE_SOURCE')
    require(type(raw_runtime) is bytes and hashlib.sha256(raw_runtime).hexdigest() == RUNTIME_SHA,
        'EXACT_ORIGINAL_FACTORY_SOURCE')
    runtime_node = next(node for node in ast.parse(raw_runtime).body
        if isinstance(node, ast.FunctionDef) and node.name == 'connect_factory')
    runtime_env = {}
    exec(compile(ast.Module(body=[runtime_node], type_ignores=[]), RUNTIME, 'exec'), runtime_env)
    actual = runtime.connect_factory
    require(type(actual) is FunctionType
        and _code_shape(actual.__code__) == _code_shape(runtime_env['connect_factory'].__code__)
        and actual.__defaults__ is None and actual.__closure__ is None, 'ENTIRE_ORIGINAL_RUNTIME_FACTORY')
    tree = ast.parse(raw)
    wanted = {'require', 'factory9', 'build'}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    require({node.name for node in nodes} == wanted and len(nodes) == len(wanted), 'ALL_THREE_ENGINE_FUNCTIONS')
    env = dict(FunctionType=FunctionType, NS=NS)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), ENGINE, 'exec'), env)
    original = dict(env)
    proofs = []
    for name, replacements in (('factory9', ((9, 10),)), ('build', ((69, 162), (9, 10)))):
        fn = original[name]
        values = list(fn.__code__.co_consts)
        slots = []
        for before, after in replacements:
            matches = [i for i, value in enumerate(values) if type(value) is int and value == before]
            require(len(matches) == 1, 'ONE_TYPED_ENGINE_METADATA_SLOT')
            slot = matches[0]
            values[slot] = after
            slots.append((slot, before, after))
        changed = fn.__code__.replace(co_consts=tuple(values))
        undo = list(changed.co_consts)
        for slot, before, after in slots:
            undo[slot] = before
        require(_code_shape(changed.replace(co_consts=tuple(undo))) == _code_shape(fn.__code__),
            'POSITIONAL_ENGINE_INVERSE_PRESERVES_PRODUCT10')
        projected = FunctionType(changed, env, argdefs=fn.__defaults__, closure=fn.__closure__)
        projected.__kwdefaults__ = fn.__kwdefaults__
        env[name] = projected
        proofs.append(dict(function=name, slots=slots, entire_positional_inverse=True))
    task = 'case165-current-r010-tests'
    receipt = 'implementation/p09/evidence/p09-361-case165-current-runtime-run010.v1.json'
    env.update(TASK=task, ROOT_RECEIPT=receipt)
    factory, factory_proof = env['factory9'](actual)
    return NS(build=env['build'], factory=factory, task=task, receipt=receipt,
        proof=dict(target_case=165, target_physical_run=10, target_descriptors=162,
            task=task, root_receipt=receipt, engine_metadata_inverses=proofs, factory_bound_inverse=factory_proof,
            existing_result_guard_retained=True, original_product10_retained=True,
            current_reference_graph_or_packet_relabelled=False, actual_engine_constructed=False,
            new_identity_graph_transport_or_worker_qualified=False, GO_authorized=False, accepted_count_delta=0))


from batch_worker_entry import identity_wire, prepare_worker_transport, reconstruct as reconstruct_worker_entry, transport_graph


def construct_runtime(root, reader, prepared, planned, inherited, known, a):
    """Actual engine/checker construction, never body, process, or acceptance.

    The historical default initializer is read-only and observed by the SAME
    owning checkpoint. Every project open is declared/pinned before its normal
    read; bytecode caches cannot substitute for the admitted source. No source
    namespace or historical result is modified. Whole Native admission remains
    separate, and the unfinished metadata callback is explicitly unavailable.
    """
    import importlib
    import sys
    from pathlib import Path
    audit_state = dict(active=True, checking=False, opens=0, pyc=0)
    observed = set()
    require(sys.getprofile() is None, 'NO_EXISTING_PROFILE_REPLACED')
    def audit(event, args):
        if not audit_state['active'] or audit_state['checking'] or event != 'open' or not args or not isinstance(args[0], (str, bytes)):
            return
        path = Path(os.fsdecode(args[0])).absolute()
        if not path.is_relative_to(root):return
        mode, flags = args[1:3]
        require(not (isinstance(mode, str) and any(c in mode for c in 'wax+'))
            and not (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)), 'READ_ONLY_RUNTIME_CONSTRUCTION')
        if path.suffix in ('.pyc','.pyo'):
            audit_state['pyc'] += 1
            raise OSError('QUALIFIED_SOURCE_REQUIRED_NOT_BYTECODE_CACHE')
        name = path.relative_to(root).as_posix()
        if name not in known:
            prepared.missing_construction_input = name
        require(name in known, 'CONSTRUCTION_INPUT_EXPLICITLY_DECLARED')
        audit_state['checking'] = True
        try:
            reader.checkpoint()
            a.exact(reader.pin(name), known[name], 'ACTUAL_CONSTRUCTION_INPUT_PIN')
            observed.add(name);audit_state['opens'] += 1
        finally:audit_state['checking'] = False
    def profile(frame, event, arg):
        if event == 'call' and not audit_state['checking'] and 'tools/p09/' in frame.f_code.co_filename.replace('\\','/'):
            reader.checkpoint()
    sys.addaudithook(audit)
    sys.setprofile(profile)
    try:
        envelope = importlib.import_module('flat_current_queue_envelope_runtime_v25')
        pins = [known['tools/p09/'+name+'.py'] for name in
            ('post_product_recovery_connection_v1','post_product_recovery_window_v1')]
        libraries, _ = prepared.loader.load(root, pins, {})
        recovery, window_tool = libraries.post_product_recovery_connection_v1, libraries.post_product_recovery_window_v1
        original_window = envelope.prior
        # Only this original source open is routed through the owner's paced
        # reader. All existence checks still use the REAL root/path/receipt.
        class WindowSource:
            def read_bytes(self):
                actual, data = reader._read(window_tool.WINDOW_PIN['path'], parse=True)
                reader._bind(actual['path'], actual)
                a.exact(actual, window_tool.WINDOW_PIN, 'ORIGINAL_WINDOW_SOURCE_BYTES')
                return bytes(data)
        class Root:
            def __fspath__(self):return os.fspath(root)
            def __truediv__(self, name):
                return WindowSource() if name == window_tool.WINDOW_PIN['path'] else root/name
        built = prepared.future_engine.build(Root(), prepared.loader, prepared.api, prepared.admitted_entry.graph,
            original_window, recovery, window_tool, reader.checkpoint)
        execution = Batch(plain(planned.whole), plain(planned.current), plain(planned.history),
            first_index=165, checkpoint=reader.checkpoint)
        # No graph report has been published yet; do not smuggle an old009
        # report into the new010 metadata path or allow an accidental body run.
        def metadata_unavailable(q):
            reader.checkpoint();require(False, 'RUN010_PARENT_GRAPH_REPORT_NOT_PUBLISHED')
        built.engine.run_owned.__globals__['binding'] = metadata_unavailable
        parent, parent_state = execution.connect_parent(built.engine, prepared.admitted_entry.graph)
        graph = NS(**{**vars(prepared.admitted_entry.graph), 'full_oracle':execution.connect_full_oracle(
            prepared.admitted_entry.graph.full_oracle, prepared.admitted_entry.graph.binding, index=165)})
        proxy = NS(**{**vars(envelope), 'namespace_bundle':prepared.loader})
        legacy_lib, _ = prepared.loader.load(root, [known['tools/p09/case160_run007_controller.py']],
            {'flat_current_queue_envelope_runtime_v25':proxy, 'sys':NS(**{**vars(sys),'argv':[]})})
        legacy = legacy_lib.case160_run007_controller
        require(legacy.NATIVE == 7 and legacy.CURRENT is not None, 'ORIGINAL_HISTORICAL_VALIDATOR_FAMILY')
        a.fields(vars(built.window.M.base.CONFIG), dict(index=165,before=158), 'CURRENT_CONSTRUCTION_STEP_UNCHANGED')
        oracle_lib, _ = prepared.loader.load(root, [known['tools/p09/current_queue_successor_oracle.py']],
            {'current_queue_successor_connections':prepared.api.metadata})
        raw = WindowSource().read_bytes()
        connect = recovery.connect_oracle(oracle_lib.current_queue_successor_oracle.connect, window_tool, raw)
        checker, oracle_proof = connect(legacy.CURRENT, graph, built.window.M.base.CONFIG, built.names, inherited, reader.checkpoint)
        checker.environment['only159']()
        require(built.state.attempts == built.state.calls == parent_state.attempts == 0 and parent_state.frames == []
            and built.window.WINDOW.SECONDS == checker.environment['prior'].WINDOW.SECONDS == 10,
            'ACTUAL_CONSTRUCTION_NO_WORKER_FRAME_OR_WINDOW_RELAXATION')
        return NS(built=built, parent=parent, checker=checker, batch=execution,
            proof=dict(actual_engine_constructed=True, historical_validator_family_connected=True,
                parent_exact_Frame_and_batch_hooks_installed=True, real_identity_run=10, descriptors=162,
                worker_attempts=0, worker_calls=0, parent_attempts=0, Frame_instances=0,
                original_worker_retained=parent.worker is built.original_worker, parent_and_checker_product_seconds=10,
                observed_declared_project_inputs=len(observed), original_project_opens=audit_state['opens'],
                bytecode_reads_denied=audit_state['pyc'], shared_original_guard_used_during_import=True,
                parent_metadata_admission_or_current_closure_or_cost_qualified=False,
                parent_metadata_blocked_until_new_graph_report=True, product_or_process_executed=False,
                GO_authorized=False, accepted_count_delta=0))
    finally:
        sys.setprofile(None)
        audit_state['active'] = False


class PacedNamespaceLoader:
    """Keep the original loader body; source opens use its owner's paced IO.

    Each open reads fresh bytes with the original reader. A bounded per-open
    BytesIO is consumed by the unchanged loader and then discarded; no source,
    parsed tree or hash cache survives an open. No OS/global Path is patched.
    """
    def __init__(self, original, reader, allowed):
        self.original = original
        self.reader = reader
        self.allowed = scope.pins(list(allowed.values()))
        self.owner = (os.getpid(), threading.get_ident())
        self.calls = self.source_reads = 0
        self.sources = {}
        self.api = NS(**{**vars(original), 'load': self.load})

    def load(self, root, pins, reuse):
        import io
        self.reader.checkpoint()
        require((os.getpid(), threading.get_ident()) == self.owner, 'SERIAL_NAMESPACE_READER_OWNER')
        require(os.path.normcase(os.fspath(root)) == os.path.normcase(os.fspath(self.reader.root)), 'EXACT_NAMESPACE_ROOT')
        requested = scope.pins(pins)
        for name, pin in requested.items():
            require(name.endswith('.py') and pin['bytes'] <= 65536 and self.allowed.get(name) == pin,
                'EXACT_DECLARED_NAMESPACE_SOURCE_REQUEST')
        reader, holder = self.reader, self
        class Source:
            def __init__(self, name):
                self.name = name
            def __fspath__(self):
                return os.fspath(root / self.name)
            def open(self, mode):
                require(mode == 'rb' and self.name in requested, 'NAMESPACE_READ_ONLY_DECLARED_SOURCE')
                expected = requested[self.name]
                before = reader.maximum_parse_bytes
                try:
                    reader.maximum_parse_bytes = min(before, expected['bytes'] + 1)
                    actual, raw = reader._read(self.name, parse=True)
                    reader._bind(self.name, actual)
                finally:
                    reader.maximum_parse_bytes = before
                require(actual == expected and type(raw) in (bytes, bytearray)
                    and len(raw) == expected['bytes'], 'FRESH_NAMESPACE_SOURCE_BYTES')
                holder.sources[self.name] = dict(actual)
                holder.source_reads += 1
                return io.BytesIO(raw)
        class Root:
            def __fspath__(self):
                return os.fspath(root)
            def __truediv__(self, name):
                scope.pins([dict(path=name, bytes=1, sha256='0'*64)])
                return Source(name)
        self.calls += 1
        return self.original.load(Root(), pins, reuse)


def connect_preparation(root, reader, evidence, manifest, hint, declared, batch, a, bytes_policy):
    """Connect the real fixed162 graph and batch scope, without engine/GO.

    This reuses the sealed qualification/declaration, not a chain of former
    qualification runners. Only the actual bounded graph construction is run.
    """
    import importlib
    # The small preparation receipt does not enumerate default loader imports.
    # Resolve their exact pins from the complete saved declaration as well;
    # every requested program is still freshly read and hash checked here.
    known = scope.extend(declared.logical, scope.pins(evidence['source_pins']))
    entry = 'tools/p09/batch_worker_entry.py'
    known = scope.extend(known, {entry:dict(batch.current[entry])})
    package = 'tools/p09/batch_preparation_package.py'
    known = scope.extend(known, {package:dict(batch.current[package])})
    def verified(name):
        require(name in known, 'DECLARED_PREPARATION_PROGRAM')
        a.exact(reader.pin(name), known[name], 'CURRENT_PREPARATION_PROGRAM')
        return known[name]
    loader_name = 'tools/p09/runtime_envelope_namespace_bundle_v1.py'
    verified(loader_name)
    original_loader = importlib.import_module('runtime_envelope_namespace_bundle_v1')
    initial = PacedNamespaceLoader(original_loader, reader, known)
    clone_pin = known['tools/p09/ast_clone_namespace_v1.py']
    copy_pin = known['tools/p09/ast_copy_namespace_connection_v1.py']
    libraries, _ = initial.api.load(root, [clone_pin, copy_pin], {})
    optimized, _ = libraries.ast_copy_namespace_connection_v1.connect(original_loader,
        libraries.ast_clone_namespace_v1)
    paced = PacedNamespaceLoader(optimized, reader, known)
    constructor = known['tools/p09/native009_full72_construction_v1.py']
    libraries, _ = paced.api.load(root, [constructor], {})
    loader, runtime_import_proof = libraries.native009_full72_construction_v1.private_runtime_imports(paced.api)
    names = ('fixed162_worker_transport_v1', 'receipt_xz_envelope_v1', 'bounded_successor_capsule_wire_v2')
    libraries, _ = loader.load(root, [known['tools/p09/'+name+'.py'] for name in names], {})
    api = libraries.fixed162_worker_transport_v1.connect(root, loader, scope, bytes_policy,
        libraries.receipt_xz_envelope_v1, libraries.bounded_successor_capsule_wire_v2, reader.checkpoint, a.exact)
    wire_pin = evidence['wire_pin']
    actual, wire = reader._read(wire_pin['path'], parse=True)
    reader._bind(actual['path'], actual)
    a.exact(actual, wire_pin, 'CURRENT_ACTUAL162_PREPARATION_PACKET')
    graph, construction = api.reconstruct(hint, bytes(wire), reader.checkpoint)
    a.exact(graph.binding.descriptors(), manifest['descriptors'], 'CURRENT_REAL162_GRAPH_DESCRIPTOR_TABLE')
    raw_pin, raw = reader._read(RUNTIME, parse=True)
    reader._bind(raw_pin['path'], raw_pin)
    a.exact(raw_pin, known[RUNTIME], 'ACTUAL_ORIGINAL_SCOPE_FOR_BATCH_INSTALLATION')
    private_runtime, scope_proof = install_scope(api.runtime, bytes(raw), batch)
    private_api = NS(**{**vars(api), 'runtime': private_runtime})
    engine_pin, engine_raw = reader._read(ENGINE, parse=True)
    reader._bind(engine_pin['path'], engine_pin)
    a.exact(engine_pin, known[ENGINE], 'CURRENT_ORIGINAL_ENGINE_PREPARATION_SOURCE')
    future_engine = prepare_engine_builder(bytes(engine_raw), private_runtime, bytes(raw))
    future_transport = prepare_worker_transport(root, loader, known, api,
        libraries.bounded_successor_capsule_wire_v2, bytes_policy, graph, hint, evidence, bytes(wire), reader.checkpoint, a.exact)
    prototype_name = 'implementation/p09/evidence/p09-361-case165-successor-worker-bootstrap010.v1.json'
    prototype_pin = dict(path=prototype_name, bytes=len(future_transport.bootstrap),
        sha256=hashlib.sha256(future_transport.bootstrap).hexdigest())
    prototype_wire = 'implementation/p09/evidence/p09-361-case165-successor-worker-capsule010.compact.v1.json'
    prototype_data = {prototype_name:future_transport.bootstrap, prototype_wire:future_transport.wire}
    entry_reads = []
    def read_entry(pin, limit):
        require(limit == 16384, 'ORIGINAL_ENTRY_READ_LIMIT')
        entry_reads.append(pin['path'])
        if pin['path'] in prototype_data:
            return prototype_data[pin['path']]  # Explicit in-memory prototype, never labelled fresh file IO.
        require(pin in (evidence['bootstrap_pin'], evidence['wire_pin']), 'EXACT_ORIGINAL_REFERENCE_INPUT')
        before = reader.maximum_parse_bytes
        try:
            reader.maximum_parse_bytes = min(before, limit+1)
            actual, data = reader._read(pin['path'], parse=True)
            reader._bind(actual['path'], actual)
        finally:reader.maximum_parse_bytes = before
        a.exact(actual, pin, 'FRESH_ENTRY_REFERENCE_SOURCE_BYTES')
        return bytes(data)
    def reference_factory(prior, packet, checkpoint):
        return api.reconstruct(prior, packet, checkpoint)
    def transport_factory(reference, step, checkpoint):
        return transport_graph(root, loader, known, api, libraries.bounded_successor_capsule_wire_v2,
            bytes_policy, reference, step, checkpoint)
    admitted = reconstruct_worker_entry(future_transport.proof['task'], prototype_pin, read_entry,
        reference_factory, transport_factory, reader.checkpoint)
    a.exact(admitted.graph.binding.descriptors(), manifest['descriptors'], 'ACTUAL_ENTRY_COMPLETE162_DECLARATION')
    require(len(entry_reads) == 4, 'EXACT_ENTRY_METADATA_READS_NO_REENCODER_OR_TESTS')
    # Keep the independently declared WHOLE inherited scope in the unchanged
    # successor connector. Only its full oracle's explicit extend dependency
    # selects current inputs, after actual closing witnesses are available.
    original_oracle = graph.full_oracle
    graph = NS(**{**vars(graph), 'full_oracle': batch.connect_full_oracle(
        original_oracle, graph.binding, index=hint['step']['index'])})
    oracle_pin = known['tools/p09/current_queue_successor_oracle.py']
    oracle_library, _ = loader.load(root, [oracle_pin], {'current_queue_successor_connections': api.metadata})
    original_connect = oracle_library.current_queue_successor_oracle.connect
    def connect_oracle(legacy, step, identity, inherited, checkpoint):
        return original_connect(legacy, graph, step, identity, inherited, checkpoint)
    # Reference-only negative admission: invoke no checker/generator/candidate.
    def never_generate(*args):
        raise ValueError('BATCH_VERIFY_REFERENCE_ORACLE_MUST_NOT_EXECUTE')
    generator = FunctionType(never_generate.__code__, dict(never_generate.__globals__,
        original=NS(scope=scope), ORACLE_SCOPE=scope, mechanics_projection=lambda node: node))
    before = reader.read_passes
    project, oracle_state = graph.full_oracle.projector(generator, graph.binding,
        never_generate, reader.checkpoint)
    try:
        project(b'', {}, {}, {})
    except ValueError as error:
        if error.args != ('BATCH_VERIFY_COMPLETE_WHOLE_BOUNDARIES_BEFORE_ORACLE',):
            raise
    else:
        require(False, 'UNAUDITED_ORACLE_MUST_STOP')
    require(reader.read_passes == before and oracle_state.original.observed['generator_calls'] == 0,
        'PREAUDIT_ORACLE_DENIED_BEFORE_IO_OR_GENERATOR')
    # Check the real Binding, not a mock, can retain all162 constructors while
    # projecting only current physical inputs. Old history injection is fatal.
    extra = {n: dict(p) for n, p in batch.whole.items() if n not in declared.physical}
    logical = scope.extend(declared.logical, extra) if extra else dict(declared.logical)
    current = {n: p for n, p in logical.items() if n not in batch.history}
    normalized, _ = graph.binding.semantic_union(current, reader.checkpoint)
    a.exact(normalized, current, 'REAL_BINDING_MUST_NOT_REINJECT_HISTORY')
    projected, _ = graph.binding.project(current, reader.checkpoint)
    a.exact(plain(projected.physical_pins), plain(batch.current), 'REAL_BINDING_CURRENT_PHYSICAL_SCOPE')
    before = reader.read_passes
    try:
        private_runtime.current_input_scope(reader, graph, hint['step'], evidence['manifest_pin'],
            evidence['manifest_pin'], dict(reader.snapshots))
    except ValueError as error:
        if error.args != ('BATCH_VERIFY_READY_METADATA_OWNER_ONLY',):
            raise
    else:
        require(False, 'UNAUDITED_BATCH_METADATA_MUST_STOP')
    require(reader.read_passes == before and batch.phase == 'NEW', 'PREAUDIT_REJECTION_BEFORE_ANY_METADATA_IO')
    # Exercise the REAL parent class factory with an unexecutable reference
    # body. No product engine build, frame instance/acquisition or run_owned.
    # This diagnostic batch is not reusable as an execution batch afterwards.
    import json
    def never_execute(*args, **kwargs):
        raise ValueError('BATCH_VERIFY_REFERENCE_PARENT_MUST_NOT_EXECUTE')
    reference_body = FunctionType(never_execute.__code__, dict(never_execute.__globals__,
        native=NS(frames=phased.frames), runtime_budget=never_execute, binding=never_execute,
        json=json, c=NS(ROOT=root)))
    reference_engine = NS(run_owned=reference_body, worker=never_execute)
    reference_parent, reference_state = batch.connect_parent(reference_engine, graph)
    require(reference_state.attempts == 0 and reference_state.frames == []
        and reference_parent.worker is never_execute, 'REFERENCE_PARENT_NO_BODY_OR_FRAME_EXECUTION')
    sources = scope.extend(initial.sources, paced.sources)
    return NS(api=private_api, graph=graph, loader=loader, source_pins=sources, connect_oracle=connect_oracle,
        future_engine=future_engine,
        future_transport=future_transport,
        admitted_entry=admitted,
        bounded_wire=libraries.bounded_successor_capsule_wire_v2, reference_wire=bytes(wire),
        proof=dict(real_descriptor_count=len(graph.binding.descriptors()),
            real_current_logical_inputs=len(current), real_current_physical_inputs=len(projected.physical_pins),
            metadata_adapter_installed_in_private_runtime=True,
            old_whole_history_reinjection_detected_and_absent=True,
            preaudit_metadata_blocked_before_IO=True, batch_phase=batch.phase,
            declared_source_programs_read_fresh=len(sources), paced_source_read_calls=initial.source_reads+paced.source_reads,
            namespace_load_calls=initial.calls+paced.calls, decoder_reconstruction=construction,
            original_runtime_import_proof_count=len(runtime_import_proof),
            scope_adapter=scope_proof, reference_graph_context=9,
            real_parent_factory_exact_class_connected_with_unexecutable_reference_body=True,
            reference_parent_attempts=reference_state.attempts, reference_parent_frame_instances=len(reference_state.frames),
            actual_product_engine_constructed=False, real_parent_lifecycle_adapter_installed=True,
            real_full_oracle_policy_dependency_installed=True,
            real_successor_oracle_connector_loaded_original_body=True,
            preaudit_full_oracle_blocked_before_generator_and_IO=True,
            actual_legacy_full_validator_family_connected=False, actual_candidate_checker_executed=False,
            future010_162_engine_builder_prepared_only=True,
            future010_in_memory_transport=future_transport.proof,
            future010_in_process_entry=admitted.proof,
            entry_prototype_memory_inputs=2, entry_fresh_existing_file_inputs=2,
            current009_graph_or_wire_changed=False, future010_engine_or_transport_qualified=False,
            parent_metadata_admission_executed=False, engine_or_Job_Frame_worker_process_executed=False,
            actual_metadata_Frame_shared_decoder5_qualified=False, current_runtime_manifest_qualified=False,
            GO_authorized=False, accepted_count_delta=0))


def reconstruct_declared_scope(native, history, packet, current, manifest, checkpoint):
    """Rebuild the saved3305 declaration without old constructors or byte IO.

    Callers pin the five input records. All original logical pins remain; only
    exact existing representation pairs normalize physical aliases. Matching
    saved counts/bytes/directories is a declaration check, not fresh runtime
    source, decoder, environment, product or acceptance qualification.
    """
    from pathlib import PurePosixPath
    checkpoint()
    rows = manifest['descriptors']
    require(type(rows) is list and len(rows) == 162, 'COMPLETE_CURRENT162_MANIFEST')
    originals = {}
    carriers = {}
    reverse = {}
    def add_alias(original, physical):
        checked = scope.pins([original, physical])
        require(len(checked) == 2, 'DISTINCT_LOGICAL_AND_PHYSICAL_PAIR')
        name, path = original['path'], physical['path']
        require(path not in reverse or reverse[path] == (original, physical), 'NO_PHYSICAL_ALIAS_CONFLICT')
        reverse[path] = (dict(original), dict(physical))
    for row in rows:
        checkpoint()
        old, new = row['semantic_original_pin'], row['physical_envelope_pin']
        require(old['path'] not in originals and new['path'] not in carriers, 'UNIQUE_COMPLETE162_PAIRS')
        add_alias(old, new)
        originals[old['path']] = dict(old)
        carriers[new['path']] = dict(new)
    previous = native['source_input_representation']['descriptors']
    require(type(previous) is list and len(previous) == 75, 'EXACT_NATIVE009_OLD75_TABLE')
    for row in previous:
        old, physical = row['semantic_original_pin'], row['physical_envelope_pin']
        require(originals.get(old['path']) == old, 'EVERY_OLD75_LOGICAL_PIN_UNCHANGED')
        add_alias(old, physical)
    def normalize(rows):
        result = {}
        for name, pin in scope.pins(rows).items():
            checkpoint()
            if name in reverse:
                old, physical = reverse[name]
                require(pin == physical, 'EXACT_OLD_OR_CURRENT_PHYSICAL_ALIAS_HASH')
                pin = old
                name = old['path']
            if name in originals:
                require(pin == originals[name], 'EXACT_DECLARED_LOGICAL_SOURCE')
            require(name not in result or result[name] == pin, 'NO_DECLARATION_CONFLICT_REBASE')
            result[name] = dict(pin)
        return result
    logical = normalize(native['source_input_representation']['semantic_source_freeze'])
    stages = []
    for row, count in ((history, 3280), (packet, 3297), (current, 3305)):
        logical = scope.extend(logical, normalize(row['source_pins']))
        require(type(row['declared_semantic_inputs']) is int
            and row['declared_semantic_inputs'] == len(logical) == count, 'EXACT_SAVED_DECLARATION_STAGE')
        stages.append(count)
    require(all(logical.get(n) == p for n, p in originals.items()), 'ALL162_ORIGINALS_RETAINED')
    by_original = {row['semantic_original_pin']['path']: row['physical_envelope_pin'] for row in rows}
    physical = {}
    for name, pin in logical.items():
        value = by_original.get(name, pin)
        require(value['path'] not in physical or physical[value['path']] == value, 'NO_FINAL_PHYSICAL_COLLISION')
        physical[value['path']] = dict(value)
    cost = current['complete_prototype_runtime_budget']
    binary = sum(p['bytes'] for n, p in physical.items() if n.lower().endswith('.exe'))
    other = sum(p['bytes'] for n, p in physical.items() if not n.lower().endswith('.exe'))
    directories = len({p.as_posix() for n in physical for p in PurePosixPath(n).parents})
    require((len(logical), sum(p['bytes'] for p in logical.values()), len(physical), binary, other, directories)
        == (cost['semantic_input_count'], cost['semantic_input_bytes'], cost['inputs'],
            cost['binary_bytes'], cost['other_bytes'], cost['directories']), 'EXACT_SAVED_SCOPE_COUNTS_BYTES_AND_DIRECTORIES')
    return NS(logical=logical, physical=physical, normalize=normalize,
        to_physical=lambda pins: {by_original.get(n, p)['path']: dict(by_original.get(n, p))
            for n, p in normalize(pins).items()},
        proof=dict(saved_declaration_stages=stages, logical_inputs=len(logical), physical_inputs=len(physical),
            logical_bytes=sum(p['bytes'] for p in logical.values()), physical_bytes=binary+other,
            directories=directories, original_constructors_or_decoders_reexecuted=False,
            current_runtime_source_bytes_qualified=False, GO_authorized=False))


def install_scope(runtime, raw, batch):
    """Return a private namespace, never mutate original modules/functions.

    This changes policy, not merely speed. It is opt-in and does not construct
    an engine, qualify a dependency closure, execute Native or authorize GO.
    """
    require(type(raw) is bytes and hashlib.sha256(raw).hexdigest() == RUNTIME_SHA, 'EXACT_ORIGINAL_SCOPE_SOURCE')
    original = runtime.current_input_scope
    require(type(original) is FunctionType and original.__closure__ is None, 'EXACT_ORIGINAL_FUNCTION_FAMILY')
    found = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == 'current_input_scope']
    require(len(found) == 1 and not found[0].decorator_list, 'ONE_ORIGINAL_SCOPE_FUNCTION')
    node = copy.deepcopy(found[0])
    untouched = ast.dump(node, include_attributes=False)
    baseline_env = dict(original.__globals__)
    exec(compile(ast.Module(body=[copy.deepcopy(node)], type_ignores=[]), RUNTIME, 'exec'), baseline_env)
    require(_code_shape(baseline_env['current_input_scope'].__code__) == _code_shape(original.__code__),
        'NO_PRIOR_FUNCTION_PATCH_SILENTLY_DISCARDED')
    old_loop = ast.parse('for pin in prior["bootstrap_metadata"]["input_pins"]:\n'
        ' a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_INITIAL_BOOTSTRAP_SOURCES")').body[0]
    inherited = ast.parse('required=bindings.inherited_scope(scope,representation,authority["fresh_input_pins"],q.snapshots,q.checkpoint)').body[0]
    normalize = ast.parse('required,aliases=graph.binding.semantic_union(required,q.checkpoint)').body[0]
    changes = []
    rewritten = []
    for statement in node.body:
        shape = ast.dump(statement, include_attributes=False)
        if shape == ast.dump(old_loop, include_attributes=False):
            replacement = ast.parse('_batch.require_preserved(prior["bootstrap_metadata"]["input_pins"],graph.binding)').body[0]
            replacement._batch_original = statement
            rewritten.append(replacement)
            changes.append('bootstrap_boundary')
        else:
            rewritten.append(statement)
            if shape == ast.dump(inherited, include_attributes=False):
                selected = ast.parse('required=_batch.seed_scope_declaration(required,graph.binding)').body[0]
                selected._batch_added = True
                rewritten.append(selected)
                changes.append('declaration_seed')
            if shape == ast.dump(normalize, include_attributes=False):
                selected = ast.parse('required=_batch.select_current(required,q,graph.binding)').body[0]
                selected._batch_added = True
                rewritten.append(selected)
                changes.append('current_scope')
    require(changes == ['bootstrap_boundary', 'declaration_seed', 'current_scope'], 'EXACT_THREE_EXPLICIT_POLICY_SLOTS')
    wrapper = ast.parse('with _batch.metadata_reader(q,graph.binding): pass').body[0]
    wrapper.body = rewritten
    wrapper._batch_wrapper = True
    node.body = [wrapper]

    class Undo(ast.NodeTransformer):
        def visit(self, value):
            if hasattr(value, '_batch_original'):
                return copy.deepcopy(value._batch_original)
            if hasattr(value, '_batch_added'):
                return None
            return super().visit(value)
        def visit_With(self, value):
            self.generic_visit(value)
            return value.body if hasattr(value, '_batch_wrapper') else value
    require(ast.dump(Undo().visit(copy.deepcopy(node)), include_attributes=False) == untouched,
        'ALL_OTHER_ORIGINAL_CHECKS_PRESERVED_INVERSE')
    env = dict(original.__globals__, _batch=batch)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), RUNTIME, 'exec'), env)
    projected = env['current_input_scope']
    return NS(**{**vars(runtime), 'current_input_scope': projected}), dict(
        previous_bootstrap_checks_moved_to_batch_boundaries=True,
        full_preservation_scope_retained=True, current_scope_selected_only_after_batch_start=True,
        original_function_or_module_mutated=False, exact_original_AST_inverse=True,
        metadata_preservation_and_unknown_reads_fail_closed=True,
        actual_parent_worker_or_Native_connected=False, GO_authorized=False)
