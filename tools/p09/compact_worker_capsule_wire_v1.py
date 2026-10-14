"""Compact wire for the same complete worker capsule and original checkers.

동일 descriptor context와 pin 필드명을 한 번만 저장한다. 모든 값은
복원하며 원 encoder/decoder/worker 코드와 16KiB 제한을 바꾸지 않는다.
"""
import json
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/compact_worker_capsule_wire_v1.py"
TEST="tools/p09/tests/test_compact_worker_capsule_wire_v1.py"
SCHEMA="hwpx-agent.p09-compact-worker-capsule-wire/v1"
MAX_BYTES=16384
MAX_BINDINGS=249

def require(ok,label):
    if not ok:raise ValueError("COMPACT_WORKER_CAPSULE_"+label)

def pin_pack(pin):
    require(type(pin) is dict and set(pin)=={"path","bytes","sha256"},"CLOSED_PIN")
    require(type(pin["path"]) is str and pin["path"] and type(pin["bytes"]) is int and pin["bytes"]>0
        and type(pin["sha256"]) is str and len(pin["sha256"])==64
        and all(c in "0123456789abcdef" for c in pin["sha256"]),"EXACT_PIN_TYPES")
    return [pin["path"],pin["bytes"],pin["sha256"]]

def pin_unpack(values):
    require(type(values) is list and len(values)==3,"PIN_TRIPLE")
    pin=dict(zip(("path","bytes","sha256"),values));pin_pack(pin);return pin

def pack(row):
    require(type(row) is dict and set(row)=={"schema_version","next_case","accepted_count_before",
        "manifest_pin","descriptors","authority_pin","prior_runtime_pin"},"CLOSED_CURRENT_CAPSULE")
    require(type(row["schema_version"]) is str and row["schema_version"]
        and type(row["next_case"]) is int and row["next_case"]==160
        and type(row["accepted_count_before"]) is int and row["accepted_count_before"]==153,"CURRENT160_CONTEXT")
    rows=row["descriptors"]
    require(type(rows) is list and 0<len(rows)<=MAX_BINDINGS,"ALL_BOUNDED_DESCRIPTOR_ROWS")
    common=None;bindings=[]
    for item in rows:
        require(type(item) is dict and set(item)=={"schema_version","next_case","semantic_original_pin","physical_envelope_pin"},"CLOSED_DESCRIPTOR")
        require(type(item["schema_version"]) is str and item["schema_version"]
            and type(item["next_case"]) is int and item["next_case"]==row["next_case"],"EXACT_DESCRIPTOR_CONTEXT")
        context=[item["schema_version"],item["next_case"]]
        if common is None:common=context
        require(common==context,"NO_MIXED_DESCRIPTOR_CONTEXT")
        bindings.append([pin_pack(item["semantic_original_pin"]),pin_pack(item["physical_envelope_pin"])])
    return dict(schema_version=SCHEMA,context=[row["schema_version"],row["next_case"],row["accepted_count_before"]],
        descriptor_context=common,manifest=pin_pack(row["manifest_pin"]),authority=pin_pack(row["authority_pin"]),
        prior=pin_pack(row["prior_runtime_pin"]),bindings=bindings)

def unpack(wire):
    require(type(wire) is dict and set(wire)=={"schema_version","context","descriptor_context","manifest","authority","prior","bindings"}
        and wire["schema_version"]==SCHEMA,"CLOSED_COMPACT_WIRE")
    context=wire["context"];common=wire["descriptor_context"];bindings=wire["bindings"]
    require(type(context) is list and len(context)==3 and type(common) is list and len(common)==2
        and type(bindings) is list and 0<len(bindings)<=MAX_BINDINGS,"BOUNDED_COMPACT_SHAPE")
    rows=[]
    for pair in bindings:
        require(type(pair) is list and len(pair)==2,"EXACT_DESCRIPTOR_PAIR")
        rows.append(dict(schema_version=common[0],next_case=common[1],
            semantic_original_pin=pin_unpack(pair[0]),physical_envelope_pin=pin_unpack(pair[1])))
    row=dict(schema_version=context[0],next_case=context[1],accepted_count_before=context[2],
        manifest_pin=pin_unpack(wire["manifest"]),authority_pin=pin_unpack(wire["authority"]),
        prior_runtime_pin=pin_unpack(wire["prior"]),descriptors=rows)
    require(pack(row)==wire,"EXACT_CANONICAL_INVERSE")
    return row

class JSON:
    @staticmethod
    def dumps(row,**options):
        data=json.dumps(pack(row),**options)
        require(0<len(data.encode("ascii"))<=MAX_BYTES,"ORIGINAL16K_WIRE_LIMIT")
        return data
    @staticmethod
    def loads(data,**options):
        require(type(data) is str and 0<len(data.encode("ascii"))<=MAX_BYTES,"ORIGINAL16K_INPUT_LIMIT")
        return unpack(json.loads(data,**options))

def connect(api):
    require(api.MAX_BYTES==MAX_BYTES,"UNCHANGED_ORIGINAL16K")
    functions={}
    for name in ("encode","decode"):
        fn=getattr(api,name);require(type(fn) is FunctionType and fn.__globals__.get("json") is json,"EXACT_ORIGINAL_JSON_FUNCTION")
        private=dict(fn.__globals__,json=JSON)
        revised=FunctionType(fn.__code__,private,argdefs=fn.__defaults__,closure=fn.__closure__)
        revised.__kwdefaults__=fn.__kwdefaults__;functions[name]=revised
    return NS(**{**vars(api),**functions}),dict(original_encode_decode_code_defaults_closure_retained=True,
        original_semantic_schema_context_binding_and_hash_checks_retained=True,
        original_worker_body_not_replaced=True,original_namespace_not_mutated=True,
        maximum_wire_bytes=MAX_BYTES,all_descriptor_rows_reconstructed=True,
        wire_schema=SCHEMA,actual_worker_Native_or_GO_qualified=False)
