"""Explicit batch preservation policy; no process/GO/queue execution.

Whole history is freshly hashed at batch start/end. Each product case still
needs the original live Frame and its two complete CURRENT-input boundaries.
No per-case acceptance is granted before batch closing. A metadata read of a
preservation-only/undeclared file fails before its original IO.

The opt-in scope adapter changes two policy slots in the exact original body:
prior-bootstrap freshness -> checked batch membership; whole -> current scope.
Every other AST statement is retained, with a lossless inverse check.
"""
import ast
import copy
from contextlib import contextmanager
import hashlib
import os
import threading
from types import FunctionType, MappingProxyType, SimpleNamespace as NS

import current_stored_runtime_scope as scope
import historical_receipt_batch_partition_v1 as partition
import phased_preservation_read_gate_v2 as phased

SELF = 'tools/p09/batch_verification.py'
TEST = 'tools/p09/tests/test_batch_verification.py'
RUNTIME = 'tools/p09/current_queue_successor_runtime.py'
RUNTIME_SHA = '523fbe57dc31f73612651cf44dbca9a85fe706a40e563f391ccade2aa0cf63df'
MAX_CASES = 8


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
        self.metadata_reads = self.bootstrap_memberships = self.scope_selections = 0

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
        declared = scope.pins(bootstrap_rows)
        normalized, _ = binding.semantic_union(declared, self.checkpoint)
        require(all(self.initial.get(n) == p for n, p in normalized.items()), 'EVERY_PRIOR_BOOTSTRAP_PIN_PRESERVED')
        self.bootstrap_memberships += 1

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

    def case_started(self, index, frame):
        self.check()
        require(self.phase == 'READY' and not self.metadata_reader_active and self.active is None, 'SERIAL_CASE_START')
        require(type(index) is int and index == self.first_index + len(self.cases)
            and index <= 249 and len(self.cases) < MAX_CASES, 'BOUNDED_ORDERED_CASE_NO_REPLAY')
        gate = phased.Gate(plain(self.whole), plain(self.current), plain(self.history), identity=self.identity)
        try:
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

    def summary(self):
        return dict(phase=self.phase, whole_inputs=len(self.whole), current_inputs=len(self.current),
            preservation_inputs=len(self.history), cases_with_original_Frame_checks=len(self.cases),
            whole_initial_complete=self.initial is not None, whole_final_complete=self.final is not None,
            metadata_reads=self.metadata_reads, prior_bootstrap_membership_checks=self.bootstrap_memberships,
            current_scope_selections=self.scope_selections, accepted_count_delta=0,
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
            if shape == ast.dump(normalize, include_attributes=False):
                selected = ast.parse('required=_batch.select_current(required,q,graph.binding)').body[0]
                selected._batch_added = True
                rewritten.append(selected)
                changes.append('current_scope')
    require(changes == ['bootstrap_boundary', 'current_scope'], 'EXACT_TWO_EXPLICIT_POLICY_SLOTS')
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
