"""Native011 zlib binding namespace; reuse data qualification, never results.

Original descriptor table, decoder, history roles and generic full constructor
are retained. Fresh source/data admission and a new package publication remain
the caller's duties. No worker or product is started by this module.
"""
import hashlib
from types import FunctionType, SimpleNamespace as NS
import native011_worker_transport as transport

SELF = 'tools/p09/native011_zlib_binding.py'
SOURCE = dict(path='tools/p09/batch_zlib_binding.py', bytes=21213,
    sha256='7c7aacf250f549a1afa8313395e100fb17b2bfe2bad3ada0c538d60516c9d33d')
MANIFEST = transport.PREFIX + 'successor-run011-zlib-manifest001.v1.json'
WIRE = transport.PREFIX + 'successor-worker-capsule011.compact.zlib.v1.json'
BOOTSTRAP = transport.PREFIX + 'successor-worker-bootstrap011.zlib.v1.json'


def connect(raw):
    """Create a distinct full-constructor family from exact source bytes."""
    transport.require(type(raw) is bytes and len(raw) == SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest() == SOURCE['sha256'], 'ZLIB_ORIGINAL_SOURCE_BYTES')
    original = dict(__name__='_p09_native011_original_zlib', __file__=SOURCE['path'])
    exec(compile(raw, SOURCE['path'], 'exec', dont_inherit=True), original)
    transport.require(original.get('SELF') == SOURCE['path'] and len(original['HISTORY_KEYS']) == 8,
        'ZLIB_ORIGINAL_IDENTITY_AND_HISTORY')
    env = dict(original, SELF=SELF, MANIFEST=MANIFEST, WIRE=WIRE, BOOTSTRAP=BOOTSTRAP)
    unchanged = []
    for name, fn in original.items():
        if type(fn) is FunctionType and fn.__globals__ is original:
            clone = FunctionType(fn.__code__,env,name=fn.__name__,argdefs=fn.__defaults__,closure=fn.__closure__)
            clone.__kwdefaults__ = fn.__kwdefaults__
            env[name] = clone
            unchanged.append(name)
    env['manifest'], manifest_proof = transport._project(original['manifest'],env, {
        10:11, 'hwpx-agent.p09-run010-zlib-manifest/v1':'hwpx-agent.p09-run011-zlib-manifest/v1'})
    env['preparation_hint'], hint_proof = transport._project(original['preparation_hint'],env,{10:11})
    # The new transport already admits run011; change only its two path slots
    # to the zlib files. Reference009 constructor inputs remain unchanged.
    env['entry_reconstructor'], entry_proof = transport._project(original['entry_reconstructor'],env, {
        'successor-worker-bootstrap010.v1.json':'successor-worker-bootstrap011.v1.json',
        'successor-worker-capsule010.compact.v1.json':'successor-worker-capsule011.compact.v1.json'})
    selected = ('canonical','digest','pin','declared_rows','historical_context','manifest','connect',
        'worker_graph','entry_reconstructor','preparation_hint')
    return NS(**{name:env[name] for name in selected}, MANIFEST=MANIFEST,WIRE=WIRE,BOOTSTRAP=BOOTSTRAP,
        HISTORY_KEYS=original['HISTORY_KEYS'],proof=dict(source_pin=dict(SOURCE),
            manifest=manifest_proof,hint=hint_proof,entry=entry_proof,
            unchanged_function_bodies=sorted(set(unchanged)-{'manifest','preparation_hint','entry_reconstructor'}),
            original_descriptor_table_decoder_constructor_and_eight_history_roles_retained=True,
            data_qualification_reexecution=False,Native_or_GO_qualified=False,accepted_count_delta=0))
