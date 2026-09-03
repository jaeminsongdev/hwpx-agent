from __future__ import annotations

import base64
import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_ROOT = ROOT / "protocol" / "json-schema"


def load(name: str) -> dict:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


def valid_payload() -> dict:
    return {
        "schema_version": "hwpx-agent.p10-06-binding-bundle/v1",
        "bundle_id": "hancom.synthetic.v1",
        "sequence": 1,
        "source_registry_sha256": "a" * 64,
        "capability_registry_sha256": "b" * 64,
        "target": {
            "profile_id": "hancom-hangul-2020-secondary",
            "product_build": "11.0.0.9136",
            "locale": "ko-KR",
            "process_architecture": "x86",
            "executable_sha256": "c" * 64,
        },
        "authorization": {
            "execution_enabled": True,
            "source_registry_routing_enabled": False,
            "scope": "current_pc_exact_target_only",
            "minimum_probe_state": "runtime_verified_current_target",
        },
        "bindings": [
            {
                "capability_id": "edit.synthetic_noop",
                "action_id": "SyntheticAction",
                "parameter_set_id": None,
                "probe_evidence_sha256": "d" * 64,
                "target_mode": "document_global",
                "parameters": [],
            },
            {
                "capability_id": "layout.synthetic_typed",
                "action_id": "SyntheticTypedAction",
                "parameter_set_id": "SyntheticSet",
                "probe_evidence_sha256": "e" * 64,
                "target_mode": "document_global",
                "parameters": [
                    {
                        "argument_id": "count",
                        "item_name": "Count",
                        "source_value_type": "integer",
                        "target_value_type": "int32",
                        "required": True,
                        "minimum": 0,
                        "maximum": 100,
                        "maximum_utf8_bytes": None,
                        "scale_numerator": 2,
                        "scale_denominator": 1,
                        "rounding": "exact",
                        "enum_values": None,
                    }
                ],
            },
        ],
    }


def main() -> int:
    envelope_schema = load("hancom-signed-binding-envelope-v1.schema.json")
    bundle_schema = load("hancom-binding-bundle-v1.schema.json")
    Draft202012Validator.check_schema(envelope_schema)
    Draft202012Validator.check_schema(bundle_schema)
    envelope_validator = Draft202012Validator(envelope_schema)
    bundle_validator = Draft202012Validator(bundle_schema)

    envelope = {
        "schema_version": "hwpx-agent.p10-06-signed-binding-envelope/v1",
        "algorithm": "Ed25519",
        "key_id": "ed25519-sha256-" + "1" * 64,
        "public_key_sha256": "2" * 64,
        "payload_sha256": "3" * 64,
        "payload_base64": base64.b64encode(b"{}").decode("ascii"),
        "signature_base64": base64.b64encode(bytes(64)).decode("ascii"),
    }
    envelope_validator.validate(envelope)

    payload = valid_payload()
    bundle_validator.validate(payload)
    invalid_cases: list[dict] = []

    value = copy.deepcopy(payload)
    value["bindings"][0]["parameter_set_id"] = "UnexpectedSet"
    invalid_cases.append(value)

    value = copy.deepcopy(payload)
    value["bindings"][1]["parameter_set_id"] = None
    invalid_cases.append(value)

    value = copy.deepcopy(payload)
    value["bindings"][1]["parameters"][0]["target_value_type"] = "boolean"
    invalid_cases.append(value)

    value = copy.deepcopy(payload)
    value["bindings"][0]["capability_id"] = "haction.synthetic"
    invalid_cases.append(value)

    value = copy.deepcopy(payload)
    value["bindings"][0]["action_id"] = "Synthetic\u0001Action"
    invalid_cases.append(value)

    value = copy.deepcopy(payload)
    value["unexpected"] = True
    invalid_cases.append(value)

    rejected = sum(not bundle_validator.is_valid(value) for value in invalid_cases)
    result = {
        "schema_version": "hwpx-agent.p10-06-binding-schema-tests/v1",
        "state": "pass" if rejected == len(invalid_cases) else "failed",
        "meta_schemas_valid": True,
        "valid_fixtures": 2,
        "negative_rejected": rejected,
        "negative_total": len(invalid_cases),
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["state"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
