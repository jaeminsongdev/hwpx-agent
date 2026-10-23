"""Closed Native011 transport/entry adapter; no publisher, launcher or GO.

The immutable run010 source is constructor code, not a reusable run result.
Only declared identity literals are projected in a private namespace. The
complete inverse must recover the original code, including nested byte guards.
This does not qualify a new manifest, source closure, worker or product run.
"""
import hashlib
from types import CodeType, FunctionType, SimpleNamespace as NS

SELF = 'tools/p09/native011_worker_transport.py'
SOURCE = dict(path='tools/p09/batch_worker_entry.py', bytes=14451,
    sha256='6dbafe54b4b2f72df9519541efd299a77fceb94ee3247c995a6bc9d6826810fe')
TASK = 'case165-current-r011-tests'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
BOOTSTRAP = PREFIX + 'successor-worker-bootstrap011.v1.json'
WIRE = PREFIX + 'successor-worker-capsule011.compact.v1.json'


def require(ok, code):
    if not ok:
        raise ValueError('NATIVE011_TRANSPORT_' + code)


def _project(fn, env, pairs):
    """Typed closed literals, recursive inverse, original defaults/closure."""
    require(type(fn) is FunctionType and type(pairs) is dict and pairs, 'FUNCTION_AND_CLOSED_SLOTS')
    require(all(type(k) is type(v) and type(k) in (int, str, bytes) for k, v in pairs.items()),
        'TYPED_IDENTITY_LITERALS')
    require(len(set(pairs.values())) == len(pairs) and not set(pairs) & set(pairs.values()),
        'BIJECTIVE_DISJOINT_LITERALS')
    seen = {k: 0 for k in pairs}
    def replace(value, mapping, counts=None):
        if type(value) is CodeType:
            return value.replace(co_consts=tuple(replace(v, mapping, counts) for v in value.co_consts))
        if type(value) is tuple:
            return tuple(replace(v, mapping, counts) for v in value)
        if type(value) is frozenset:
            return frozenset(replace(v, mapping, counts) for v in value)
        if type(value) in (int, str, bytes) and value in mapping:
            require(type(value) is type(mapping[value]), 'NO_BOOL_INTEGER_ALIAS')
            if counts is not None:
                counts[value] += 1
            return mapping[value]
        return value
    projected = replace(fn.__code__, pairs, seen)
    require(all(n > 0 for n in seen.values()), 'EVERY_DECLARED_SLOT_PRESENT')
    require(replace(projected, {v: k for k, v in pairs.items()}) == fn.__code__,
        'ENTIRE_RECURSIVE_CODE_INVERSE')
    result = FunctionType(projected, env, name=fn.__name__, argdefs=fn.__defaults__, closure=fn.__closure__)
    result.__kwdefaults__ = fn.__kwdefaults__
    return result, dict(exact_recursive_inverse=True, projected_literal_occurrences=sum(seen.values()),
        defaults_and_closure_retained=True)


def connect(raw):
    """Accept fresh pinned source bytes, construct only three private APIs.

    Owning paced source readers remain responsible for both fresh reads and
    closing hashes. No data files are read and no package is published here.
    """
    require(type(raw) is bytes and len(raw) == SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest() == SOURCE['sha256'], 'ORIGINAL_SOURCE_BYTES')
    original = dict(__name__='_p09_native011_original_transport', __file__=SOURCE['path'])
    exec(compile(raw, SOURCE['path'], 'exec', dont_inherit=True), original)
    require(original.get('SELF') == SOURCE['path'], 'ORIGINAL_MODULE_IDENTITY')
    env = dict(original)
    identity, wire_proof = _project(original['identity_wire'], env, {
        'case165-current-r010-tests': TASK, 10: 11, b'P09I10\n': b'P09I11\n',
        'hwpx-agent.p09-run010-identity-wire/v1': 'hwpx-agent.p09-run011-identity-wire/v1',
        'outer_transport_hash_and_exact_run010_checked': 'outer_transport_hash_and_exact_run011_checked'})
    env['identity_wire'] = identity
    graph, graph_proof = _project(original['transport_graph'], env, {10: 11})
    env['transport_graph'] = graph
    entry, entry_proof = _project(original['reconstruct'], env, {
        'case165-current-r010-tests': TASK, 10: 11,
        PREFIX + 'successor-worker-bootstrap010.v1.json': BOOTSTRAP,
        PREFIX + 'successor-worker-capsule010.compact.v1.json': WIRE,
        'hwpx-agent.p09-run010-worker-preparation/v1': 'hwpx-agent.p09-run011-worker-preparation/v1',
        'RECONSTRUCTED_RUN010_ENTRY_INPUTS_NOT_PROCESS_OR_GO': 'RECONSTRUCTED_RUN011_ENTRY_INPUTS_NOT_PROCESS_OR_GO'})
    # Never expose run010's preparer, file reader, imports or mutable globals.
    return NS(TASK=TASK, BOOTSTRAP=BOOTSTRAP, WIRE=WIRE, identity_wire=identity,
        transport_graph=graph, reconstruct=entry, proof=dict(source_pin=dict(SOURCE),
            wire=wire_proof, graph=graph_proof, entry=entry_proof,
            original_reference009_paths_retained=True, source_module_changed=False,
            preparation_suite_replayed=False, Native_or_GO_qualified=False,
            accepted_count_delta=0))
