"""Run010 transport and input admission; no process, GO or product launcher."""
import copy
import hashlib
from types import FunctionType, SimpleNamespace as NS

SELF = 'tools/p09/batch_worker_entry.py'
RUNTIME = 'tools/p09/current_queue_successor_runtime.py'


def require(ok, code):
    if not ok:
        raise ValueError('BATCH_VERIFY_' + code)


def identity_wire(worker, checkpoint):
    """Bind run010 to the unchanged complete inner wire; keep BOTH hashes."""
    import json
    require(worker.TASK == 'case165-current-r010-tests' and worker.MAX_BYTES == 16384, 'EXACT_FUTURE_WIRE_CONTEXT')
    magic = b'P09I10\n'
    schema = 'hwpx-agent.p09-run010-identity-wire/v1'
    canonical = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=True,
        separators=(',', ':'), allow_nan=False).encode('ascii')
    pin = lambda data: dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    def encode(binding, authority, prior, guard):
        checkpoint(); guard()
        inner, expected = worker.encode(binding, authority, prior, guard)
        require(expected == pin(inner), 'ORIGINAL_INNER_WIRE_PIN')
        header = canonical(dict(schema_version=schema, index=165, run=10, task=worker.TASK, inner_pin=expected))
        require(0 < len(header) <= 2048, 'BOUNDED_IDENTITY_HEADER')
        data = magic + ('%04d\n' % len(header)).encode('ascii') + header + inner
        require(0 < len(data) <= 16384, 'UNCHANGED_IDENTITY_WIRE16K')
        return data, pin(data)
    def decode(data, expected, guard):
        checkpoint(); guard()
        require(type(data) is bytes and 0 < len(data) <= 16384, 'BOUNDED_IDENTITY_WIRE16K')
        require(type(expected) is dict and expected == pin(data), 'IDENTITY_TRANSPORT_HASH')
        require(data.startswith(magic), 'IDENTITY_MAGIC_NOT_OLD009_WIRE')
        size = data[len(magic):len(magic)+5]
        require(len(size) == 5 and size[:4].isdigit() and size[-1:] == b'\n', 'IDENTITY_HEADER_LENGTH')
        length = int(size[:4]); start = len(magic)+5
        require(0 < length <= 2048 and start+length < len(data), 'BOUNDED_IDENTITY_HEADER')
        raw = data[start:start+length]
        header = json.loads(raw.decode('ascii'))
        require(type(header) is dict and set(header) == {'schema_version','index','run','task','inner_pin'}
            and canonical(header) == raw, 'CANONICAL_CLOSED_IDENTITY_HEADER')
        require(header['schema_version'] == schema and type(header['index']) is int and header['index'] == 165
            and type(header['run']) is int and header['run'] == 10 and header['task'] == worker.TASK,
            'EXACT_IDENTITY_TASK_CASE_AND_RUN')
        inner = data[start+length:]
        require(type(header['inner_pin']) is dict and header['inner_pin'] == pin(inner), 'INNER_IDENTITY_HASH')
        bound, proof = worker.decode(inner, header['inner_pin'], guard)
        return bound, dict(proof, identity_transport_bytes=len(data), identity_header_bytes=length,
            outer_transport_hash_and_exact_run010_checked=True, original_inner_byte_counter_not_relabelled=True)
    return NS(**{**vars(worker), 'encode': encode, 'decode': decode})


def transport_graph(root, loader, known, api, bounded, bytes_policy, reference, step, checkpoint):
    """Construct the original worker codec once; never run qualification cases."""
    paths = ('tools/p09/current_queue_successor_connections.py', RUNTIME,
        'tools/p09/current_queue_successor_binding.py')
    names, _ = loader.load(root, [known[name] for name in paths], {})
    metadata, runtime = names.current_queue_successor_connections, names.current_queue_successor_runtime
    def upper10(fn):
        values = list(fn.__code__.co_consts)
        slots = [i for i, value in enumerate(values) if type(value) is int and value == 8]
        require(len(slots) == 1, 'ONE_FUTURE_TRANSPORT_BOUND_SLOT')
        slot = slots[0]; values[slot] = 10
        code = fn.__code__.replace(co_consts=tuple(values))
        undo = list(code.co_consts); undo[slot] = 8
        require(code.replace(co_consts=tuple(undo)) == fn.__code__, 'FUTURE_TRANSPORT_BOUND_INVERSE')
        result = FunctionType(code, fn.__globals__, argdefs=fn.__defaults__, closure=fn.__closure__)
        result.__kwdefaults__ = fn.__kwdefaults__
        return result
    original = upper10(metadata.worker_api); check = require
    def only10(worker, compact, binding, step, run):
        check(type(run) is int and run == 10 and type(step) is dict and step['index'] == 165
            and step['before'] == 158, 'ONLY_NEW165_RUN010_TRANSPORT')
        return original(worker, compact, binding, step, run)
    strict = FunctionType(only10.__code__, metadata.worker_api.__globals__, closure=only10.__closure__)
    metadata.worker_api.__globals__['worker_api'] = strict; metadata.worker_api = strict
    bounded.install(metadata, checkpoint)
    validator = upper10(runtime.validate_worker_hint)
    runtime.validate_worker_hint.__globals__['validate_worker_hint'] = validator
    runtime.validate_worker_hint = validator
    graph, construction = metadata.connect(root, loader, bytes_policy, reference.binding_module,
        reference.binding, step, 10, checkpoint)
    worker, _ = api.binary.connect(graph.worker, checkpoint)
    worker = identity_wire(worker, checkpoint)
    return NS(**{**vars(graph), 'worker':worker}), runtime


def prepare_worker_transport(root, loader, known, api, bounded, bytes_policy, reference, hint, evidence, reference_wire,
                             checkpoint, exact):
    """Real162 encode/decode in memory only; no worker entry, file or GO."""
    import json
    graph, runtime = transport_graph(root, loader, known, api, bounded, bytes_policy, reference, hint['step'], checkpoint)
    worker = graph.worker
    wire, transport_pin = worker.encode(reference.binding, hint['step']['prior_queue_pin'],
        hint['step']['prior_candidate_pin'], checkpoint)
    bound, decoder = worker.decode(wire, transport_pin, checkpoint)
    exact(bound.descriptors(), reference.binding.descriptors(), 'ALL162_FUTURE_IDENTITY_ROUNDTRIP')
    exact(dict(bound.manifest_pin), dict(reference.binding.manifest_pin), 'UNCHANGED_MANIFEST_TABLE_PROVENANCE')
    core = {name: copy.deepcopy(hint[name]) for name in ('schema_version','index','run','step','capsule_pin',
        'manifest_pin','first_descriptor','historical_pairs','historical_provenance')}
    core['run'] = 10
    core['manifest_pin'] = dict(reference.binding.manifest_pin)
    core['capsule_pin'] = dict(path='implementation/p09/evidence/p09-361-case165-successor-worker-capsule010.compact.v1.json', **transport_pin)
    exact(runtime.validate_worker_hint(core, worker.TASK), (165,10), 'EXACT_FUTURE_BOOTSTRAP_TASK')
    bootstrap = dict(schema_version='hwpx-agent.p09-run010-worker-preparation/v1', execution=core,
        reference_bootstrap_pin=evidence['bootstrap_pin'], reference_wire_pin=evidence['wire_pin'],
        reference_is_constructor_data_not_product_replay=True, GO_authorized=False)
    bootstrap_raw = (json.dumps(bootstrap, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(',', ':'))+'\n').encode('ascii')
    require(0 < len(bootstrap_raw) <= 16384, 'UNCHANGED_FUTURE_BOOTSTRAP16K')
    bad_task = wire.replace(b'case165-current-r010-tests', b'case165-current-r009-tests', 1)
    challenges = ((reference_wire, dict(bytes=len(reference_wire), sha256=hashlib.sha256(reference_wire).hexdigest()),
        'BATCH_VERIFY_IDENTITY_MAGIC_NOT_OLD009_WIRE'), (wire, dict(transport_pin, sha256='0'*64),
        'BATCH_VERIFY_IDENTITY_TRANSPORT_HASH'), (bad_task, dict(bytes=len(bad_task), sha256=hashlib.sha256(bad_task).hexdigest()),
        'BATCH_VERIFY_EXACT_IDENTITY_TASK_CASE_AND_RUN'))
    for data, expected, code in challenges:
        try:worker.decode(data, expected, checkpoint)
        except ValueError as error:
            require(error.args == (code,), 'EXACT_FUTURE_IDENTITY_NEGATIVE_NOT_RESOURCE_STOP')
        else:require(False, 'FUTURE_IDENTITY_NEGATIVE_MUST_STOP')
    return NS(graph=NS(**{**vars(graph), 'worker':worker, 'binding':bound}), runtime=runtime,
        wire=wire, bootstrap=bootstrap_raw, proof=dict(task=worker.TASK, run=10, descriptors=len(bound.descriptors()),
            wire_bytes=len(wire), bootstrap_bytes=len(bootstrap_raw), identity_negative_checks=3,
            whole_original_inner_decoder_completed=True, all162_and_manifest_provenance_preserved=True,
            worker_entry_or_process_or_engine_connected=False, external_future_files_written=False,
            parent_source_Frame_shared_decoder_or_dispatch_qualified=False, GO_authorized=False, accepted_count_delta=0))


def reconstruct(task, bootstrap_pin, read, reference_factory, transport_factory, checkpoint):
    """Actual entry admission, with IO/constructors supplied by its owner.

    No encoder, qualification suite, dispatcher, GO or product callback is
    reachable here. File reads must be fresh and bounded; raw bytes are held
    only through this admission. A later owned launcher still must connect
    the original worker's GO/Job/resource/cleanup path.
    """
    import json
    checkpoint()
    require(task == 'case165-current-r010-tests', 'ENTRY_EXACT_TASK_BEFORE_IO')
    require(callable(read) and callable(reference_factory) and callable(transport_factory), 'ENTRY_OWNED_DEPENDENCIES')
    expected_bootstrap = 'implementation/p09/evidence/p09-361-case165-successor-worker-bootstrap010.v1.json'
    require(type(bootstrap_pin) is dict and bootstrap_pin.get('path') == expected_bootstrap, 'ENTRY_EXACT_BOOTSTRAP_PATH')
    opened = []
    def fresh(pin):
        checkpoint()
        require(type(pin) is dict and set(pin) == {'path','bytes','sha256'}
            and type(pin['bytes']) is int and 0 < pin['bytes'] <= 16384, 'ENTRY_EXACT_BOUNDED_PIN')
        data = read(dict(pin), 16384)
        require(type(data) is bytes and len(data) == pin['bytes']
            and hashlib.sha256(data).hexdigest() == pin['sha256'], 'ENTRY_FRESH_BYTES_MATCH_PIN')
        checkpoint(); opened.append(pin['path'])
        return data
    def unique(pairs):
        row = {}
        for name, value in pairs:
            require(name not in row, 'ENTRY_DUPLICATE_JSON_KEY')
            row[name] = value
        return row
    row = json.loads(fresh(bootstrap_pin).decode('ascii'), object_pairs_hook=unique)
    require(type(row) is dict and set(row) == {'schema_version','execution','reference_bootstrap_pin',
        'reference_wire_pin','reference_is_constructor_data_not_product_replay','GO_authorized'}
        and row['schema_version'] == 'hwpx-agent.p09-run010-worker-preparation/v1'
        and row['reference_is_constructor_data_not_product_replay'] is True
        and row['GO_authorized'] is False, 'ENTRY_CLOSED_NO_GO_BOOTSTRAP')
    core = row['execution']
    require(type(core) is dict and type(core.get('index')) is int and core['index'] == 165
        and type(core.get('run')) is int and core['run'] == 10, 'ENTRY_EXACT_CASE_AND_RUN')
    require(row['reference_bootstrap_pin'].get('path') ==
        'implementation/p09/evidence/p09-361-case165-successor-worker-bootstrap009.v6.json'
        and row['reference_wire_pin'].get('path') ==
        'implementation/p09/evidence/p09-361-case165-successor-worker-capsule009.compact.v6.json'
        and core['capsule_pin'].get('path') ==
        'implementation/p09/evidence/p09-361-case165-successor-worker-capsule010.compact.v1.json', 'ENTRY_CLOSED_REFERENCE_AND_WIRE_PATHS')
    prior = json.loads(fresh(row['reference_bootstrap_pin']).decode('ascii'), object_pairs_hook=unique)
    require(type(prior.get('run')) is int and prior['run'] == 9 and prior.get('index') == 165
        and prior['capsule_pin'] == row['reference_wire_pin'] and prior['step'] == core['step'], 'ENTRY_REFERENCE_CONSTRUCTOR_CONTEXT')
    reference_wire = fresh(row['reference_wire_pin'])
    current_wire = fresh(core['capsule_pin'])
    reference, reference_proof = reference_factory(prior, reference_wire, checkpoint)
    graph, runtime = transport_factory(reference, core['step'], checkpoint)
    require(runtime.validate_worker_hint(core, task) == (165,10) and graph.worker.TASK == task,
        'ENTRY_ORIGINAL_HINT_AND_TASK_VALIDATION')
    bound, decoder = graph.worker.decode(current_wire, {k:core['capsule_pin'][k] for k in ('bytes','sha256')}, checkpoint)
    require(bound.descriptors() == reference.binding.descriptors() and len(bound.descriptors()) == 162
        and dict(bound.manifest_pin) == core['manifest_pin']
        and bound.descriptors()[0] == core['first_descriptor'], 'ENTRY_COMPLETE162_NOT_SUBSET_OR_REBASE')
    return NS(graph=NS(**{**vars(graph), 'binding':bound}), runtime=runtime, core=core,
        proof=dict(state='RECONSTRUCTED_RUN010_ENTRY_INPUTS_NOT_PROCESS_OR_GO', metadata_byte_admissions=len(opened),
            fresh_physical_IO_claimed_by_entry=False,
            descriptor_count=162, original_reference_constructor_completed=True,
            original_inner_decoder_completed=True, encoder_or_negative_qualification_cases_run=False,
            product_or_worker_body_or_process_executed=False, GO_authorized=False, accepted_count_delta=0))


def file_reader(root, checkpoint):
    """Original direct ancestor/file/read16K boundary, with owning guard."""
    import os
    import threading
    allowed = {'implementation/p09/evidence/p09-361-case165-'+suffix for suffix in (
        'successor-worker-bootstrap010.v1.json', 'successor-worker-capsule010.compact.v1.json',
        'successor-worker-bootstrap009.v6.json', 'successor-worker-capsule009.compact.v6.json')}
    owner = (os.getpid(), threading.get_ident())
    def read(pin, limit):
        checkpoint()
        require((os.getpid(), threading.get_ident()) == owner and limit == 16384
            and pin['path'] in allowed, 'ENTRY_ORIGINAL_DIRECT_READ_SCOPE')
        path = root / pin['path']
        for parent in (path.parent, *path.parent.parents):
            require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(), 'ENTRY_DIRECT_ANCESTORS')
            if parent == root:break
        require(path.is_file() and not path.is_symlink() and not path.is_junction(), 'ENTRY_DIRECT_METADATA_FILE')
        with path.open('rb') as stream:
            data = stream.read(limit+1)
        require(0 < len(data) <= limit, 'ENTRY_ORIGINAL_READ16K')
        checkpoint()
        return data
    return read

