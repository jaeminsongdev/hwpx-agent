#!/usr/bin/env python3
"""Actual product-library preparation proof, never form publication/native authority."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_value_public_export as prior

ROOT = prior.ROOT
oracle, public = prior.oracle, prior.public
LIB = "crates/product-cli/src/lib.rs"
ARCHIVE = "implementation/p09/source-archive/p09-42-pre-form-value-preparation/lib.rs"
OLD_LIB = "abdbd01ceed773fb6d9d3d9afc11a807da9435b37156093852d4955d295fdb7a"
DELTA = b"pub mod form_value_preparation;\n\n"
PREDECESSOR = "implementation/p09/evidence/p09-41-native-form-value-public-export.current-2020.v1.json"
PREDECESSOR_SHA = "b7e8dea0362469d1df0166042083bf4aa27a04bc1568e1db13e0b70b3e89ea71"
CAPSULE = "implementation/p09/evidence/p09-42-product-form-value-preparation.current-2020.v1.json"
FIXTURE = "fixtures/target-build/p09-42-product-form-values-01/output"
MANIFEST_SHA = "8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e"
SOURCES = (
    LIB, ARCHIVE, "crates/product-cli/src/form_value_preparation.rs",
    "crates/product-cli/tests/form_value_preparation.rs",
    "tools/p09/prepare_product_form_value_fixture.py",
    "tools/p09/qualify_product_form_value_preparation.py",
    "tools/p09/tests/test_product_form_value_preparation.py",
    "implementation/p09/P09-42_PRODUCT_FORM_VALUE_PREPARATION_POLICY.md",
    "crates/product-cli/src/main.rs", "crates/product-cli/Cargo.toml",
    "Cargo.toml", "Cargo.lock", "rust-toolchain.toml",
)
INTEGRATION = {
    "actual_product_preparation_runs_public_sdk_and_rereads_complete_candidate_but_denies_route",
    "exact_retry_is_deterministic_and_canonical_request_is_distinct_from_raw_json",
    "fresh_access_revocation_and_digest_drift_reject_preparation_verification_and_route",
    "changed_caller_policy_map_source_and_limits_are_not_substituted_for_provider_snapshot",
    "malformed_duplicate_unknown_raw_path_coercion_and_stale_request_fail_closed",
    "request_limits_debug_and_public_receipts_never_leak_values_or_paths",
    "caller_default_reset_is_real_output_not_native_default_attestation",
    "no_op_wrong_kind_and_unqualified_date_do_not_return_partial_preparation",
    "all_five_types_required_radio_empty_text_defaults_and_clear_match_independent_predecessor_bytes",
    "partial_radio_and_external_validator_never_count_as_product_preparation",
}
PRIVATE = {
    "form_value_preparation::tests::private_binding_writer_checks_limit_before_hash_or_count_change",
    "form_value_preparation::tests::private_binding_writer_rejects_arithmetic_overflow_without_mutation",
}


def product_inverse(raw, archived):
    oracle.require(oracle.sha(archived) == OLD_LIB and raw.count(DELTA) == 1
                   and raw.replace(DELTA, b"", 1) == archived,
                   "product_preparation_complete_inverse_invalid")


def authority():
    raw = public.checked(ROOT / PREDECESSOR, PREDECESSOR_SHA, 2 * 1024 * 1024)
    capsule = json.loads(raw, object_pairs_hook=oracle.duplicate_guard)
    oracle.require(set(capsule["source_sha256"]) == set(prior.SOURCES),
                   "product_preparation_predecessor_sources")
    for name, digest in capsule["source_sha256"].items():
        public.checked(ROOT / name, digest)
    prior.project(public.checked(ROOT / prior.LIB, prior.CURRENT_LIB),
                  public.checked(ROOT / prior.ARCHIVE, prior.history.OLD_LIB))
    archived = public.checked(ROOT / ARCHIVE, OLD_LIB)
    product_inverse(public.bounded_bytes(ROOT / LIB, 2 * 1024 * 1024), archived)
    graph = capsule["physical_pre_export_original_reproduction"]["source_sha256"]
    oracle.require(len(graph) == 1443, "product_preparation_historical_graph_inventory")
    total = 0
    for logical, digest in graph.items():
        prior.history.relative(logical)
        actual = prior.ARCHIVE if logical == prior.LIB else ARCHIVE if logical == LIB else logical
        total += len(public.checked(ROOT / actual, digest, prior.history.SOURCE_BYTES))
        oracle.require(total <= prior.history.LIMIT_BYTES, "product_preparation_historical_graph_limit")
    return {
        "original_capsule_sha256": PREDECESSOR_SHA,
        "original_seven_sources_raw_exact": True,
        "original_physical_view_files": len(graph), "original_physical_view_bytes": total,
        "original_physical_view_manifest_sha256": oracle.sha(prior.q.shared.lifecycle.canonical_bytes(graph)),
        "graph_raw_bytes_preserved": True,
        "complete_original_capsule_reexecution_this_successor": False,
        "current_old_verifier_pass_claimed": False,
        "original_product_library_sha256": OLD_LIB,
        "new_product_complete_inverse_byte_exact": True,
    }


def snapshot():
    directory = ROOT / FIXTURE
    oracle.no_links(directory)
    files = {}
    for path in directory.iterdir():
        oracle.require(path.name.endswith((".hwpx", ".json")), "product_preparation_fixture_kind")
        files[path.name] = oracle.checked_bytes(path, 1024 * 1024)
    oracle.require(len(files) == 11 and sum(map(len, files.values())) == 167304
                   and oracle.sha(files["fixture-manifest.json"]) == MANIFEST_SHA,
                   "product_preparation_fixture_inventory")
    return files


def match_snapshot(files, fresh):
    oracle.require(files.keys() == fresh.keys()
                   and all(files[name] == fresh[name] for name in files),
                   "product_preparation_full_fixture_bytes_differ")


def qualify():
    before = {name: oracle.sha(public.bounded_bytes(ROOT / name, 2 * 1024 * 1024)) for name in SOURCES}
    guard, files = authority(), snapshot()
    code, stdout, _ = prior.run([
        "cargo", "test", "--offline", "--locked", "-p", "hwpx-agent-cli",
        "--test", "form_value_preparation",
    ])
    oracle.require(code == 0, "product_preparation_compiled_integration_failed")
    integration = prior.protocol(stdout, INTEGRATION, 10)
    code, stdout, _ = prior.run([
        "cargo", "test", "--offline", "--locked", "-p", "hwpx-agent-cli", "--lib",
        "form_value_preparation::tests::",
    ])
    oracle.require(code == 0, "product_preparation_actual_private_units_failed")
    private = prior.protocol(stdout, PRIVATE, 2, 1)
    bundles = []
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix="p09-40-component-", dir=ROOT / "fixtures/target-build") as temporary:
            directory = Path(temporary)
            bundles.append(prior.generate(directory))
            fresh = {path.name: oracle.checked_bytes(path, 1024 * 1024) for path in directory.iterdir()}
            match_snapshot(files, fresh)
        oracle.require(not Path(temporary).exists(), "product_preparation_owned_scratch_not_cleaned")
    oracle.require(bundles[0] == bundles[1], "product_preparation_fresh_public_bundles_differ")
    match_snapshot(files, snapshot())
    oracle.require(authority() == guard and before == {
        name: oracle.sha(public.bounded_bytes(ROOT / name, 2 * 1024 * 1024)) for name in SOURCES
    }, "product_preparation_source_drift")
    return {
        "schema_version": "hwpx-agent.p09-42-product-form-value-preparation/v1",
        "state": "actual_product_library_preparation_and_complete_output_parity_qualified_non_green",
        "source_sha256": before, "predecessor_preservation": guard,
        "actual_product_integration": integration, "actual_production_private_units": private,
        "actual_public_sdk_consumer_each_generation": bundles[0]["compiled_tests"],
        "two_fresh_public_sdk_generations_byte_exact": True,
        "whole_original_manifest_and_independent_zip_value_gap_oracle_parity": True,
        "fixture_snapshot": {
            "scope": "product_preparation_only_not_native_candidate", "files": len(files),
            "bytes": sum(map(len, files.values())), "manifest_sha256": MANIFEST_SHA,
            "file_sha256": {name: oracle.sha(raw) for name, raw in sorted(files.items())},
            "all_five_product_output_pairs_predecessor_byte_exact": True,
        },
        "claims": {
            "actual_product_library_preparation_connected": True,
            "current_signed_vs0_attestation_consulted_not_reused_for_forms": True,
            "form_route_publication_denied": True, "cli_form_action_enabled": False,
            "product_routing": False, "publication_cas_idempotency": False,
            "native_execution": False, "native_defaults": False, "native_protection": False,
            "native_date": False, "external_validation": False, "current_legacy_aggregate_pass": False,
            "render": "not_run", "product_differential": "not_run", "green_rows": 0, "p09_complete": False,
        },
        "privacy": {"raw_document_values_present": False, "absolute_private_paths_present": False,
                    "native_session_started": False, "trust_or_registry_changed": False},
    }


def evidence_path(path):
    target = path.absolute()
    oracle.require(target == ROOT / CAPSULE and ".." not in path.parts,
                   "product_preparation_evidence_boundary")
    oracle.no_links(target.parent)
    if target.exists(): oracle.no_links(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    try:
        output = evidence_path(args.output) if args.output else None
        verify = evidence_path(args.verify) if args.verify else None
        oracle.require(output is None or not output.exists(), "product_preparation_evidence_exists")
        value = qualify()
        raw = prior.q.shared.lifecycle.canonical_bytes(value)
        if output:
            with output.open("xb") as stream: stream.write(raw)
        if verify:
            oracle.require(public.bounded_bytes(verify, 2 * 1024 * 1024) == raw,
                           "product_preparation_capsule_reproduction_mismatch")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, prior.subprocess.SubprocessError):
        print(json.dumps({"state": "fail", "error_code": "product_preparation_qualification_failed"}))
        return 2
    print(json.dumps({"state": "pass", "qualification_sha256": oracle.sha(raw), "capsule_bytes": len(raw),
                      "source_pins": len(SOURCES), "actual_product_cases": 10, "production_private_units": 2,
                      "whole_output_pairs": 5, "form_route_denied": True, "native_session_started": False,
                      "green_rows": 0}))
    return 0


if __name__ == "__main__": raise SystemExit(main())
