"""Explicit lossless runtime-receipt physical/semantic source candidate.

This is NOT a Native factory, controller, writer or Gate acceptor. All semantic
pins remain; ordinary source/EXE/fixtures cannot be transformed. A future caller
must prove both fresh physical reads, locks, original reader semantics, complete
source checks and independent acceptance before adopting the physical projection.
No IO/cache/threads/metadata aliases or mutation of qualified original modules.
"""
import hashlib
import re
from types import MappingProxyType
import current_stored_runtime_scope as scope
import runtime_record_envelope_v2 as codec

SELF = "tools/p09/runtime_envelope_source_projection_v1.py"
TEST = "tools/p09/tests/test_runtime_envelope_source_projection_v1.py"
SCHEMA = "hwpx-agent.p09-lossless-runtime-source-projection/v1"
PREFIX = "implementation/p09/evidence/p361-lossless-runtime-inputs/"
MAX_BINDINGS = 249


def require(ok, code):
    if not ok:
        raise ValueError("RUNTIME_ENVELOPE_SOURCE_" + code)


def copy_pin(pin):
    result = scope.pins([pin])
    return result[pin["path"]]


def descriptor(original_pin, encoded_pin, *, next_case):
    require(type(next_case) is int and 116 <= next_case <= 249, "NEXT_CASE")
    original, encoded = copy_pin(original_pin), copy_pin(encoded_pin)
    match = re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json",
        original["path"])
    require(match is not None and 112 <= int(match[1]) < next_case and 1 <= int(match[2]) <= 999,
        "ONLY_PRIOR_RUNTIME_RECEIPT_NOT_SOURCE_OR_CURRENT_PRODUCT")
    require(original["bytes"] <= codec.MAX_BYTES, "ORIGINAL_DECODER_BUDGET")
    require(encoded["path"] == PREFIX + f"case{match[1]}-runtime-run{match[2]}.envelope.v1.json"
        and encoded["bytes"] <= codec.MAX_BYTES, "EXPLICIT_PHYSICAL_FORMAT_PATH")
    return dict(schema_version=SCHEMA, semantic_original_pin=original,
        physical_envelope_pin=encoded, next_case=next_case)


class Projection:
    """Immutable full semantic scope plus explicitly separate physical scope."""
    __slots__ = ("_semantic", "_physical", "_bindings", "next_case")

    def __init__(self, required, descriptors, *, next_case, checkpoint):
        require(callable(checkpoint), "CHECKPOINT")
        checkpoint()
        # validate every original pin, not just the transformed subset.
        require(type(required) is dict, "WHOLE_MAPPING")
        original = scope.pins(list(required.values()))
        require(original == required, "WHOLE_MAPPING_KEY_IDENTITY")
        require(type(descriptors) is list and 0 < len(descriptors) <= MAX_BINDINGS, "BOUNDED_DESCRIPTOR_COUNT")
        physical = {name: dict(pin) for name, pin in original.items()}
        bindings = {}
        for row in descriptors:
            checkpoint()
            require(type(row) is dict and set(row) == {"schema_version", "semantic_original_pin",
                "physical_envelope_pin", "next_case"}, "CLOSED_DESCRIPTOR")
            expected = descriptor(row["semantic_original_pin"], row["physical_envelope_pin"], next_case=next_case)
            require(row == expected, "DESCRIPTOR_EXACT_CONTEXT")
            logical, encoded = expected["semantic_original_pin"], expected["physical_envelope_pin"]
            name = logical["path"]
            require(original.get(name) == logical and name not in bindings, "EXACT_ORIGINAL_ONE_BINDING")
            require(encoded["path"] not in physical and encoded["path"] not in original, "NO_PHYSICAL_COLLISION")
            physical.pop(name)
            physical[encoded["path"]] = encoded
            bindings[name] = encoded
        require(len(original) == len(physical), "FULL_BIJECTIVE_INPUT_COUNT")
        require(set(original) == (set(physical) - {pin["path"] for pin in bindings.values()}) | set(bindings),
            "NO_UNMAPPED_INPUT_DROPPED")
        self._semantic = MappingProxyType({n: MappingProxyType(dict(p)) for n, p in original.items()})
        self._physical = MappingProxyType({n: MappingProxyType(dict(p)) for n, p in physical.items()})
        self._bindings = MappingProxyType({n: MappingProxyType(dict(p)) for n, p in bindings.items()})
        self.next_case = next_case
        checkpoint()

    @property
    def semantic_pins(self):
        return self._semantic

    @property
    def physical_pins(self):
        return self._physical

    def decode_fresh(self, semantic_name, actual_physical_pin, raw, checkpoint):
        # Every invocation validates physical bytes then independently decodes;
        # no prior pin/parsed JSON/content can stand in for a fresh caller read.
        require(callable(checkpoint), "CHECKPOINT")
        checkpoint()
        require(type(semantic_name) is str and semantic_name in self._bindings, "EXPLICIT_BOUND_LOGICAL_NAME")
        pin = self._bindings[semantic_name]
        require(type(raw) is bytes and 0 < len(raw) <= codec.MAX_BYTES, "BOUNDED_PHYSICAL_BYTES")
        require(copy_pin(actual_physical_pin) == pin and len(raw) == pin["bytes"]
            and hashlib.sha256(raw).hexdigest() == pin["sha256"], "FRESH_PHYSICAL_BYTES_AND_PIN")
        decoded = codec.decode(raw, checkpoint)
        original = self._semantic[semantic_name]
        require(len(decoded) == original["bytes"] and hashlib.sha256(decoded).hexdigest() == original["sha256"],
            "EXACT_SEMANTIC_ORIGINAL_BYTES_AND_HASH")
        checkpoint()
        return decoded

    def evidence(self):
        return dict(schema_version=SCHEMA, next_case=self.next_case,
            semantic_input_count=len(self._semantic), physical_input_count=len(self._physical),
            semantic_original_bytes=sum(p["bytes"] for p in self._semantic.values()),
            physical_encoded_bytes=sum(p["bytes"] for p in self._physical.values()),
            transformed_runtime_receipt_count=len(self._bindings),
            semantic_input_scope_reduced=False, original_files_rewritten=False,
            physical_scope_is_explicitly_different=True, fresh_IO_or_live_lock_proven=False,
            original_reader_and_independent_oracle_connected=False,
            Native_product_or_acceptance_executed=False, GO_authorized=False,
            queue_advance_authorized=False, P09_gate="OPEN")
