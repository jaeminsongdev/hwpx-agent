"""Construct a fresh Native011 package, without files, launches or GO.

The owner must supply fresh admitted sources/reference data under its original
resource guard. No historical qualification suite runs here. The original full
Binding constructor, encoder, decoder and entry admission all run in order.
"""
import json
from types import SimpleNamespace as NS
import native011_worker_transport as transport

SELF = 'tools/p09/native011_package.py'


def prepare(root, loader, known, constructor_api, bounded, bytes_policy, reference, previous,
            declaration, mapping, bindings, binding_api, worker_api, checkpoint):
    """Return bounded new payloads only after full entry round-trip.

    In-memory re-admission verifies the package being constructed; it is NOT a
    substitute for the dispatcher's later first/closing physical reads.
    """
    check = transport.require
    checkpoint()
    check(worker_api.TASK == transport.TASK, 'PACKAGE_NEW_TASK')
    check(dict(reference.binding.manifest_pin) == dict(declaration.REFERENCE_MANIFEST),
        'PACKAGE_ORIGINAL009_REFERENCE')
    prepared = binding_api.connect(root,loader,reference.binding_module.source.scope,
        reference,declaration,mapping,bindings,checkpoint)
    check(prepared.manifest_pin['path'] == binding_api.MANIFEST, 'PACKAGE_NEW_MANIFEST_PATH')
    selected = binding_api.worker_graph(root,loader,known,constructor_api,bounded,bytes_policy,
        prepared,previous['step'],declaration,worker_api,checkpoint)
    graph, runtime = selected.graph, selected.runtime
    check(graph.worker.TASK == transport.TASK, 'PACKAGE_ACTUAL_GRAPH_TASK')
    wire, wire_pin = graph.worker.encode(prepared.binding,previous['step']['prior_queue_pin'],
        previous['step']['prior_candidate_pin'],checkpoint)
    core = binding_api.preparation_hint(previous,prepared,wire_pin)
    check(runtime.validate_worker_hint(core,transport.TASK) == (165,11), 'PACKAGE_FULL_HINT_ADMISSION')
    bootstrap = dict(schema_version='hwpx-agent.p09-run011-worker-preparation/v1',execution=core,
        reference_bootstrap_pin=dict(declaration.REFERENCE_BOOTSTRAP),reference_wire_pin=dict(declaration.REFERENCE_WIRE),
        reference_is_constructor_data_not_product_replay=True,GO_authorized=False)
    payloads = ((binding_api.MANIFEST,prepared.manifest_raw,262144),
        (binding_api.WIRE,wire,16384),(binding_api.BOOTSTRAP,binding_api.canonical(bootstrap),16384))
    check(len({name for name,_,_ in payloads}) == 3, 'PACKAGE_DISTINCT_PATHS')
    pins = []
    current = {}
    for name, raw, maximum in payloads:
        checkpoint()
        check(type(raw) is bytes and 0 < len(raw) <= maximum, 'PACKAGE_ALL_PAYLOAD_BOUNDS')
        current[name] = raw
        pins.append(binding_api.pin(name,raw))
    check(pins[0] == prepared.manifest_pin and pins[1] == core['capsule_pin'], 'PACKAGE_ACTUAL_PAYLOAD_PINS')
    # Only reference constructor bytes may be fetched from the owning reader.
    # Fresh physical admission of the new files must happen after publication.
    reference_reads = []
    def read(pin, maximum):
        checkpoint()
        check(maximum == 16384, 'PACKAGE_ENTRY_READ_LIMIT')
        if pin['path'] in current:
            check(binding_api.pin(pin['path'],current[pin['path']]) == pin, 'PACKAGE_MEMORY_BYTES_PIN')
            return current[pin['path']]
        check(pin in (declaration.REFERENCE_BOOTSTRAP,declaration.REFERENCE_WIRE),
            'PACKAGE_ONLY_ORIGINAL_REFERENCE_READS')
        reference_reads.append(dict(pin))
        return constructor_api.read_reference(pin,maximum)
    def construct(prior, packet, guard):
        # Admission must also independently reconstruct the reference; do not
        # return the already prepared Binding as if a decoder had produced it.
        actual_reference, proof = constructor_api.reconstruct(prior,packet,guard)
        check(dict(actual_reference.binding.manifest_pin) == dict(declaration.REFERENCE_MANIFEST),
            'PACKAGE_FRESH_ORIGINAL009_REFERENCE')
        new = binding_api.connect(root,loader,actual_reference.binding_module.source.scope,
            actual_reference,declaration,mapping,bindings,guard)
        return new,proof
    def reconstruct_graph(new, step, guard):
        candidate = binding_api.worker_graph(root,loader,known,constructor_api,bounded,bytes_policy,
            new,step,declaration,worker_api,guard)
        return candidate.graph,candidate.runtime
    rebuild = binding_api.entry_reconstructor(worker_api,constructor_api.metadata)
    entry = rebuild(transport.TASK,pins[2],read,construct,reconstruct_graph,checkpoint)
    check(entry.graph.binding is not prepared.binding, 'PACKAGE_FRESH_DECODED_BINDING')
    check(entry.graph.binding.descriptors() == prepared.binding.descriptors()
        and len(entry.graph.binding.descriptors()) == 162, 'PACKAGE_COMPLETE162_RECONSTRUCTED')
    check(entry.graph.binding.manifest_pin == prepared.manifest_pin, 'PACKAGE_RECONSTRUCTED_MANIFEST')
    check(reference_reads == [dict(declaration.REFERENCE_BOOTSTRAP),dict(declaration.REFERENCE_WIRE)],
        'PACKAGE_EXACT_TWO_REFERENCE_BYTE_READS')
    check(entry.proof['metadata_byte_admissions'] == 4 and entry.proof['GO_authorized'] is False,
        'PACKAGE_ORIGINAL_ENTRY_NOT_GO')
    checkpoint()
    return NS(payloads=payloads,pins=pins,entry=entry,proof=dict(
        state='CONSTRUCTED_NATIVE011_PACKAGE_IN_MEMORY_NOT_PHYSICAL_OR_NATIVE_QUALIFICATION',
        descriptor_count=162,entry_metadata_byte_admissions=4,reference_constructor_byte_reads=2,
        original_constructor_and_inner_decoder_required=True,historical_suite_replayed=False,
        fresh_physical_new_file_IO_claimed=False,files_published=False,GO_authorized=False,
        product_executed=False,accepted_count_delta=0))
