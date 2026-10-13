"""Exact r4 baseline or declared fresh reconstruction candidate; no SQL/native/publication.

기존 maintenance 실행기 원문을 바꾸지 않는다. 동일 Job/GO/중단/closing/정리 절차에
한 번에 한 개의 전체 integration-test target만 결합한다. 현재 Rust842/helper29 byte
계약과 선택한 전체 테스트 이름을 확인한다. fixture를 native/운영 storage로 승격하지 않는다.
"""
import argparse
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as maintenance
import bounded_process_progress as bounded
import issuer_sql_build_contract as contract
from audit_evidence_io import AuditEvidenceReader
from bounded_container_absence import observed_sample
from sql_owned_execution import scoped_path

SELF = "tools/p09/run_stored_comment_regression.py"
TEST = "tools/p09/tests/test_stored_comment_regression.py"
TASK = "stored-comment-tests"
CARGO_ARGUMENTS = ["test", "-p", "hwpx-agent-cli", "--test", "stored_comment_provider"]
TEST_FILES = {
    "crates/product-cli/tests/stored_comment_provider.rs": "",
}
EXPECTED_COUNT = 24
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-stored-regression-form-targets/source-preimages.v1.json"
CLEAN_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-stored-regression-unused-imports/source-preimages.v1.json"
RECURSIVE_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-stored-regression-recursive-inventory/source-preimages.v1.json"
SYNTAX_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-stored-regression-module-syntax-repair/source-preimages.v1.json"
OBSERVATION_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-stored-regression-runtime-observation-state/source-preimages.v1.json"
PROGRESS_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-stored-regression-runtime-progress/source-preimages.v1.json"
RECONSTRUCTION_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-form-reconstruction-sharing-r1/source-preimages.v1.json"
RECONSTRUCTION_CANDIDATE = "implementation/p09/evidence/p09-149-form-reconstruction-source-candidate.run02.v1.json"
FORMAT_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-form-reconstruction-format-r1/source-preimages.v1.json"
STORED_RECONSTRUCTION_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-stored-reconstruction-sharing-r2/source-preimages.v1.json"
STORED_RECONSTRUCTION_CANDIDATE = "implementation/p09/evidence/p09-149-stored-reconstruction-source-candidate.run01.v1.json"
RECONSTRUCTION_PARENT_PIN = {"path": RECONSTRUCTION_CANDIDATE, "bytes": 1828,
    "sha256": "bdb58b9dfff5d752e3955fb3534247203c8dbc10ffc87a93e79a0a10a1316483"}
RECONSTRUCTION_DELTAS = frozenset({
    "crates/hwpx-package/src/document_import/forms.rs",
    "crates/hwpx-package/src/document_import/fields.rs",
    "crates/hwpx-package/src/document_import/fields/semantics.rs",
    "crates/hwpx-package/tests/document_import_field_semantics.rs",
})
STORED_RECONSTRUCTION_DELTAS = RECONSTRUCTION_DELTAS | frozenset({
    "crates/product-cli/src/form_stored_provider/actual_import.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/field_ranges.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/field_semantics.rs",
})
FORMULA_RECONSTRUCTION_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-formula-output-reconstruction-r3/source-preimages.v1.json"
FORMULA_RECONSTRUCTION_CANDIDATE = "implementation/p09/evidence/p09-149-formula-reconstruction-source-candidate.run02.v1.json"
FORMULA_RECONSTRUCTION_PARENT_PIN = {"path": STORED_RECONSTRUCTION_CANDIDATE, "bytes": 2844,
    "sha256": "6b2df2e72a406c7e0938a5975dac6eda0b7acd4a4dac860a5db4243b6912b85a"}
FORMULA_RECONSTRUCTION_DELTAS = frozenset({
    "crates/hwpx-package/src/document_import/fields/semantics/evaluation.rs",
    "crates/hwpx-package/src/document_import/fields/semantics/evaluation/output.rs",
    "crates/hwpx-package/tests/document_import_formula_output.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output.rs",
    "crates/product-cli/src/form_stored_provider/actual_import/field_ranges/semantics/evaluation/output/outcome.rs",
    "crates/product-cli/tests/form_stored_provider/actual_import/formula_output.rs",
})
ANCHOR_PREFIX_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-source-anchor-prefix-sharing-r4/source-preimages.v1.json"
ANCHOR_PREFIX_CANDIDATE = "implementation/p09/evidence/p09-149-source-anchor-prefix-candidate.run01.v1.json"
ANCHOR_PREFIX_PARENT_PIN = {"path": FORMULA_RECONSTRUCTION_CANDIDATE, "bytes": 3449,
    "sha256": "24fd2df9dfb82f03639f7a199520b1d3a5b2a32c5aed4d65f2882562229a1330"}
ANCHOR_PREFIX_DELTAS = frozenset({
    "crates/hwpx-package/src/document_import.rs",
    "crates/hwpx-package/tests/document_import_source.rs",
})
SOURCE_VARIANTS = ("current-r4", "reconstruction-r1", "reconstruction-r2", "reconstruction-r3", "anchor-prefix-r4")
DURATION_ARCHIVE = "implementation/p09/source-archive/p09-149-pre-stored-reconstruction-duration-scope/source-preimages.v1.json"
CASES = {
    TASK: (CARGO_ARGUMENTS, TEST_FILES, EXPECTED_COUNT),
    "import-source-tests": (["test", "-p", "hwpx-package", "--test", "document_import_source"], {
        "crates/hwpx-package/tests/document_import_source.rs": "",
    }, 12),
    "form-value-tests": (["test", "-p", "hwpx-agent-cli", "--test", "form_value_operation"], {
        "crates/product-cli/tests/form_value_operation.rs": "",
    }, 18),
    "stored-form-tests": (["test", "-p", "hwpx-agent-cli", "--test", "form_stored_provider"], {
        "crates/product-cli/tests/form_stored_provider.rs": "",
    }, 249),
    "import-forms-tests": (["test", "-p", "hwpx-package", "--test", "document_import_forms"], {
        "crates/hwpx-package/tests/document_import_forms.rs": "",
    }, 10),
    "import-fields-tests": (["test", "-p", "hwpx-package", "--test", "document_import_fields"], {
        "crates/hwpx-package/tests/document_import_fields.rs": "",
    }, 12),
    "import-meanings-tests": (["test", "-p", "hwpx-package", "--test", "document_import_field_semantics"], {
        "crates/hwpx-package/tests/document_import_field_semantics.rs": "",
    }, 13),
    "import-formula-evaluation-tests": (["test", "-p", "hwpx-package", "--test", "document_import_formula_evaluation"], {
        "crates/hwpx-package/tests/document_import_formula_evaluation.rs": "",
    }, 10),
    "import-formula-output-tests": (["test", "-p", "hwpx-package", "--test", "document_import_formula_output"], {
        "crates/hwpx-package/tests/document_import_formula_output.rs": "",
    }, 6),
}
LIST_TASKS = {"stored-form-list": "stored-form-tests"}
MODULE_LIMIT = 100
DEPTH_LIMIT = 16


def case_task(task):
    result = LIST_TASKS.get(task, task)
    maintenance.require(result in CASES, "REGRESSION_TASK_SCOPE")
    return result


def module_path(parent, relative):
    # Normalize literal Rust #[path] without following filesystem links. The byte
    # reader checks the file; every ancestor is checked before reading live input.
    maintenance.require(isinstance(relative, str) and re.fullmatch(r"[A-Za-z0-9_./-]+", relative)
        and not relative.startswith("/"), "REGRESSION_MODULE_PATH_SCOPE")
    parts = parent.split("/")[:-1]
    for part in relative.split("/"):
        if part == "..":
            maintenance.require(bool(parts), "REGRESSION_MODULE_PATH_SCOPE")
            parts.pop()
        elif part not in ("", "."):
            parts.append(part)
    maintenance.require(parts and parts[0] == "crates" and parts[-1].endswith(".rs"),
        "REGRESSION_MODULE_PATH_SCOPE")
    return "/".join(parts)


def recursive_names(read_text, task=TASK):
    task = case_task(task)
    _, roots, count = CASES[task]
    maintenance.require(len(roots) == 1 and list(roots.values()) == [""], "REGRESSION_ROOT_INVENTORY")
    names, modules = [], []
    def visit(name, prefix, ancestors):
        maintenance.require(name not in ancestors, "REGRESSION_MODULE_CYCLE")
        maintenance.require(len(modules) < MODULE_LIMIT and len(ancestors) <= DEPTH_LIMIT,
            "REGRESSION_MODULE_BUDGET")
        text = read_text(name)
        maintenance.require(isinstance(text, str) and "#[ignore" not in text, "REGRESSION_IGNORED_TEST_FORBIDDEN")
        modules.append({"path": name, "prefix": prefix})
        found = re.findall(r"#\[test\]\s*fn ([a-z][a-z0-9_]*)\s*\(", text)
        maintenance.require(len(found) == len(re.findall(r"#\[test\]", text)), "REGRESSION_TEST_ATTRIBUTE_UNSUPPORTED")
        names.extend(prefix+value for value in found)
        children = re.findall(r'#\[path\s*=\s*"([^"\r\n]+)"\]\s*'
            r'(?:pub(?:\((?:crate|super|self)\))?\s+)?mod\s+([a-z][a-z0-9_]*)\s*;', text)
        maintenance.require(len(children) == len(re.findall(r"(?m)^\s*(?:pub(?:\([^\n]*\))?\s+)?mod\s+", text)),
            "REGRESSION_MODULE_DECLARATION_UNSUPPORTED")
        maintenance.require(len({child for _, child in children}) == len(children), "REGRESSION_DUPLICATE_MODULE")
        for relative, child in children:
            visit(module_path(name, relative), prefix+child+"::", ancestors+(name,))
    visit(next(iter(roots)), "", ())
    maintenance.require(len(names) == count and len(set(names)) == len(names), "REGRESSION_EXACT_TEST_COUNT")
    return sorted(names), modules


def test_names(texts, task=TASK):
    maintenance.require(isinstance(texts, dict), "REGRESSION_TEST_FILE_INVENTORY")
    def read(name):
        maintenance.require(name in texts, "REGRESSION_TEST_FILE_INVENTORY")
        return texts[name]
    names, modules = recursive_names(read, task)
    maintenance.require(set(texts) == {item["path"] for item in modules}, "REGRESSION_TEST_FILE_INVENTORY")
    return names


def validate_listing(output, expected, task):
    count = CASES[case_task(task)][2]
    maintenance.require(isinstance(output, str) and len(output.encode("utf-8")) <= bounded.LIMIT,
        "REGRESSION_OUTPUT_BUDGET")
    names, summaries = [], 0
    for line in output.splitlines():
        if line == "":
            continue
        match = re.fullmatch(r"([a-z][a-z0-9_:]*): test", line)
        if match:
            names.append(match[1])
        elif line == f"{count} tests, 0 benchmarks":
            summaries += 1
        else:
            raise ValueError("REGRESSION_COMPILED_LISTING_PROTOCOL")
    maintenance.require(len(expected) == count and len(set(expected)) == count
        and sorted(names) == sorted(expected) and summaries <= 1, "REGRESSION_COMPILED_LISTING_INVENTORY")


class RuntimeProgress:
    """Only source-whitelisted libtest names/statuses; no log/path/exception text.

    Times are first parent observations, not exact test start/end durations.
    Uses the existing bounded pipe snapshots; no new child, thread or file polling.
    """
    def __init__(self, expected, clock=time.monotonic):
        maintenance.require(len(expected) == len(set(expected)) and len(expected) <= 249
            and all(re.fullmatch(r"[a-z][a-z0-9_:]*", name) for name in expected),
            "REGRESSION_PROGRESS_SCOPE")
        self.expected = frozenset(expected)
        self.clock = clock
        self.started = self.last = clock()
        maintenance.require(type(self.started) in (int, float) and math.isfinite(self.started),
            "REGRESSION_PROGRESS_CLOCK")
        self.completed = {}
        self.events = []
        self.pending = None
        self.pending_since = None
        self.observations = 0

    def observe(self, output):
        maintenance.require(isinstance(output, str) and len(output.encode("utf-8")) <= bounded.LIMIT,
            "REGRESSION_PROGRESS_OUTPUT_BUDGET")
        now = self.clock()
        maintenance.require(type(now) in (int, float) and math.isfinite(now) and now >= self.last,
            "REGRESSION_PROGRESS_CLOCK")
        self.last = now
        self.observations += 1
        seen = {}
        for line in output.splitlines():
            match = re.fullmatch(r"test ([a-z][a-z0-9_:]*) \.\.\. (ok|FAILED|ignored)", line)
            if not match or match[1] not in self.expected:
                continue
            name, outcome = match.groups()
            maintenance.require(name not in seen, "REGRESSION_PROGRESS_DUPLICATE_NAME")
            seen[name] = outcome
            maintenance.require(name not in self.completed or self.completed[name] == outcome,
                "REGRESSION_PROGRESS_STATUS_DRIFT")
            if name not in self.completed:
                self.completed[name] = outcome
                self.events.append({"name": name, "outcome": outcome,
                    "first_observed_at_seconds": round(now-self.started, 3),
                    "pending_observed_seconds_at_completion": round(now-self.pending_since, 3)
                        if name == self.pending else None})
        maintenance.require(set(self.completed).issubset(seen), "REGRESSION_PROGRESS_BUFFER_REGRESSION")
        tail = output.rsplit("\n", 1)[-1]
        match = re.fullmatch(r"test ([a-z][a-z0-9_:]*) \.\.\. ?", tail)
        pending = match[1] if match and match[1] in self.expected and match[1] not in seen else None
        if pending != self.pending:
            self.pending, self.pending_since = pending, now if pending else None

    def snapshot(self):
        return {"scope": "source_whitelisted_libtest_progress_not_full_runtime_pass",
            "timing": "parent_first_observation_not_exact_test_execution_time",
            "expected_tests": len(self.expected), "completed_observed": len(self.completed),
            "passed_observed": sum(value == "ok" for value in self.completed.values()),
            "failed_observed": sum(value == "FAILED" for value in self.completed.values()),
            "ignored_observed": sum(value == "ignored" for value in self.completed.values()),
            "pending_test": self.pending,
            "pending_observed_seconds": round(self.last-self.pending_since, 3) if self.pending else None,
            "observations": self.observations, "events": [dict(event) for event in self.events]}


def validate_output(output, expected, task=TASK):
    maintenance.require(task in CASES, "REGRESSION_TASK_SCOPE")
    count = CASES[task][2]
    maintenance.require(isinstance(output, str) and len(output.encode("utf-8")) <= bounded.LIMIT,
        "REGRESSION_OUTPUT_BUDGET")
    names = re.findall(r"(?m)^test ([a-z][a-z0-9_:]*) \.\.\. ok\r?$", output)
    summary = re.findall(r"(?m)^test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out;", output)
    maintenance.require(len(expected) == count and len(set(expected)) == count
        and sorted(names) == sorted(expected) and len(summary) == 1
        and tuple(map(int, summary[0])) == (count, 0, 0, 0, 0), "REGRESSION_EXACT_RUNTIME_TEST_INVENTORY")


def reconstruction_sources(candidate, archive, sources):
    maintenance.require(isinstance(candidate, dict) and candidate.get("schema_version") ==
        "hwpx-agent.p09-form-reconstruction-source-candidate/v1"
        and candidate.get("qualification") == "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE"
        and candidate.get("baseline_build_pin") == contract.CURRENT_BUILD_PIN
        and candidate.get("preimage_archive") == RECONSTRUCTION_ARCHIVE,
        "REGRESSION_RECONSTRUCTION_CANDIDATE_SCOPE")
    deltas = contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas) == RECONSTRUCTION_DELTAS
        and all(name in sources and deltas[name] != sources[name] for name in deltas),
        "REGRESSION_RECONSTRUCTION_DELTA_SCOPE")
    maintenance.require(isinstance(archive, dict) and archive.get("schema_version") ==
        "hwpx-agent.p09-stored-regression-source-preimages/v1", "REGRESSION_RECONSTRUCTION_ARCHIVE_SCOPE")
    originals = {}
    for original in archive["files"]:
        name = original["path"]
        maintenance.require(name not in originals, "REGRESSION_RECONSTRUCTION_ARCHIVE_SCOPE")
        data = base64.b64decode(original["base64"], validate=True)
        maintenance.require(len(data) == original["bytes"] and hashlib.sha256(data).hexdigest() == original["sha256"],
            "REGRESSION_RECONSTRUCTION_ARCHIVE_DRIFT")
        originals[name] = {key: original[key] for key in ("path", "bytes", "sha256")}
    maintenance.require(set(originals) == RECONSTRUCTION_DELTAS|{SELF, TEST}
        and all(originals[name] == sources[name] for name in RECONSTRUCTION_DELTAS),
        "REGRESSION_RECONSTRUCTION_BASELINE_DRIFT")
    return {**sources, **deltas}


def stored_reconstruction_sources(candidate, archive, parent_sources):
    # Chain exact r4 -> reviewed r1 -> reviewed r2; never fabricate r4 preimages
    # for sources already changed in r1 or qualify historical SQL as current.
    maintenance.require(isinstance(candidate, dict) and candidate.get("schema_version") ==
        "hwpx-agent.p09-stored-reconstruction-source-candidate/v1"
        and candidate.get("qualification") == "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE"
        and candidate.get("baseline_build_pin") == contract.CURRENT_BUILD_PIN
        and candidate.get("parent_candidate_pin") == RECONSTRUCTION_PARENT_PIN
        and candidate.get("preimage_archive") == STORED_RECONSTRUCTION_ARCHIVE,
        "REGRESSION_STORED_RECONSTRUCTION_CANDIDATE_SCOPE")
    deltas = contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas) == STORED_RECONSTRUCTION_DELTAS
        and all(name in parent_sources and deltas[name] != parent_sources[name] for name in deltas),
        "REGRESSION_STORED_RECONSTRUCTION_DELTA_SCOPE")
    maintenance.require(isinstance(archive, dict) and archive.get("schema_version") ==
        "hwpx-agent.p09-stored-regression-source-preimages/v1"
        and archive.get("parent_candidate_pin") == RECONSTRUCTION_PARENT_PIN
        and archive.get("baseline_build_pin") == contract.CURRENT_BUILD_PIN,
        "REGRESSION_STORED_RECONSTRUCTION_ARCHIVE_SCOPE")
    originals = {}
    for original in archive["files"]:
        name = original["path"]
        maintenance.require(name not in originals, "REGRESSION_STORED_RECONSTRUCTION_ARCHIVE_SCOPE")
        data = base64.b64decode(original["base64"], validate=True)
        maintenance.require(len(data) == original["bytes"] and hashlib.sha256(data).hexdigest() == original["sha256"],
            "REGRESSION_STORED_RECONSTRUCTION_ARCHIVE_DRIFT")
        originals[name] = {key: original[key] for key in ("path", "bytes", "sha256")}
    maintenance.require(set(originals) == STORED_RECONSTRUCTION_DELTAS | {SELF, TEST}
        and all(originals[name] == parent_sources[name] for name in STORED_RECONSTRUCTION_DELTAS),
        "REGRESSION_STORED_RECONSTRUCTION_PARENT_DRIFT")
    return {**parent_sources, **deltas}


def formula_reconstruction_sources(candidate, archive, parent_sources):
    maintenance.require(isinstance(candidate, dict) and candidate.get("schema_version") ==
        "hwpx-agent.p09-formula-reconstruction-source-candidate/v1"
        and candidate.get("qualification") == "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE"
        and candidate.get("baseline_build_pin") == contract.CURRENT_BUILD_PIN
        and candidate.get("parent_candidate_pin") == FORMULA_RECONSTRUCTION_PARENT_PIN
        and candidate.get("preimage_archive") == FORMULA_RECONSTRUCTION_ARCHIVE,
        "REGRESSION_FORMULA_RECONSTRUCTION_CANDIDATE_SCOPE")
    deltas = contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas) == FORMULA_RECONSTRUCTION_DELTAS
        and not (FORMULA_RECONSTRUCTION_DELTAS & STORED_RECONSTRUCTION_DELTAS)
        and all(name in parent_sources and deltas[name] != parent_sources[name] for name in deltas),
        "REGRESSION_FORMULA_RECONSTRUCTION_DELTA_SCOPE")
    maintenance.require(isinstance(archive, dict) and archive.get("schema_version") ==
        "hwpx-agent.p09-stored-regression-source-preimages/v1"
        and archive.get("parent_candidate_pin") == FORMULA_RECONSTRUCTION_PARENT_PIN
        and archive.get("baseline_build_pin") == contract.CURRENT_BUILD_PIN,
        "REGRESSION_FORMULA_RECONSTRUCTION_ARCHIVE_SCOPE")
    originals = {}
    for original in archive["files"]:
        name = original["path"]
        maintenance.require(name not in originals, "REGRESSION_FORMULA_RECONSTRUCTION_ARCHIVE_SCOPE")
        data = base64.b64decode(original["base64"], validate=True)
        maintenance.require(len(data) == original["bytes"] and hashlib.sha256(data).hexdigest() == original["sha256"],
            "REGRESSION_FORMULA_RECONSTRUCTION_ARCHIVE_DRIFT")
        originals[name] = {key: original[key] for key in ("path", "bytes", "sha256")}
    maintenance.require(set(originals) == FORMULA_RECONSTRUCTION_DELTAS | {SELF, TEST}
        and all(originals[name] == parent_sources[name] for name in FORMULA_RECONSTRUCTION_DELTAS),
        "REGRESSION_FORMULA_RECONSTRUCTION_PARENT_DRIFT")
    return {**parent_sources, **deltas}


def anchor_prefix_sources(candidate, archive, parent_sources):
    maintenance.require(isinstance(candidate, dict) and candidate.get("schema_version") ==
        "hwpx-agent.p09-source-anchor-prefix-candidate/v1"
        and candidate.get("qualification") == "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE"
        and candidate.get("baseline_build_pin") == contract.CURRENT_BUILD_PIN
        and candidate.get("parent_candidate_pin") == ANCHOR_PREFIX_PARENT_PIN
        and candidate.get("preimage_archive") == ANCHOR_PREFIX_ARCHIVE,
        "REGRESSION_ANCHOR_PREFIX_CANDIDATE_SCOPE")
    deltas = contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas) == ANCHOR_PREFIX_DELTAS
        and not (ANCHOR_PREFIX_DELTAS & (STORED_RECONSTRUCTION_DELTAS | FORMULA_RECONSTRUCTION_DELTAS))
        and all(name in parent_sources and deltas[name] != parent_sources[name] for name in deltas),
        "REGRESSION_ANCHOR_PREFIX_DELTA_SCOPE")
    maintenance.require(isinstance(archive, dict) and archive.get("schema_version") ==
        "hwpx-agent.p09-stored-regression-source-preimages/v1"
        and archive.get("parent_candidate_pin") == ANCHOR_PREFIX_PARENT_PIN
        and archive.get("baseline_build_pin") == contract.CURRENT_BUILD_PIN,
        "REGRESSION_ANCHOR_PREFIX_ARCHIVE_SCOPE")
    originals = {}
    for original in archive["files"]:
        name = original["path"]
        maintenance.require(name not in originals, "REGRESSION_ANCHOR_PREFIX_ARCHIVE_SCOPE")
        data = base64.b64decode(original["base64"], validate=True)
        maintenance.require(len(data) == original["bytes"] and hashlib.sha256(data).hexdigest() == original["sha256"],
            "REGRESSION_ANCHOR_PREFIX_ARCHIVE_DRIFT")
        originals[name] = {key: original[key] for key in ("path", "bytes", "sha256")}
    maintenance.require(set(originals) == ANCHOR_PREFIX_DELTAS | {SELF, TEST}
        and all(originals[name] == parent_sources[name] for name in ANCHOR_PREFIX_DELTAS),
        "REGRESSION_ANCHOR_PREFIX_PARENT_DRIFT")
    return {**parent_sources, **deltas}


def load_binding(windows, task=TASK, source_variant="current-r4"):
    task = case_task(task)
    hot = 0
    def checkpoint():
        nonlocal hot
        hot, reason = maintenance.decision(observed_sample(windows), hot)
        maintenance.require(reason is None, reason)
    reader = AuditEvidenceReader(maintenance.ROOT, checkpoint)
    maintenance.require(reader.pin(contract.CURRENT_BUILD_PIN["path"]) == contract.CURRENT_BUILD_PIN,
        "REGRESSION_BUILD_BYTE_DRIFT")
    build = reader.json(contract.CURRENT_BUILD_PIN["path"])
    sources, protected, helpers, _ = contract.build_contract(build, "current_r4")
    additional = {}
    maintenance.require(source_variant in SOURCE_VARIANTS, "REGRESSION_SOURCE_VARIANT_SCOPE")
    if source_variant != "current-r4":
        if source_variant in ("reconstruction-r2", "reconstruction-r3", "anchor-prefix-r4"):
            maintenance.require(reader.pin(RECONSTRUCTION_CANDIDATE) == RECONSTRUCTION_PARENT_PIN,
                "REGRESSION_STORED_RECONSTRUCTION_PARENT_BYTE_DRIFT")
        sources = reconstruction_sources(reader.json(RECONSTRUCTION_CANDIDATE),
            reader.json(RECONSTRUCTION_ARCHIVE), sources)
        additional = {name: reader.pin(name) for name in (RECONSTRUCTION_CANDIDATE, RECONSTRUCTION_ARCHIVE)}
    if source_variant in ("reconstruction-r2", "reconstruction-r3", "anchor-prefix-r4"):
        if source_variant in ("reconstruction-r3", "anchor-prefix-r4"):
            maintenance.require(reader.pin(STORED_RECONSTRUCTION_CANDIDATE) == FORMULA_RECONSTRUCTION_PARENT_PIN,
                "REGRESSION_FORMULA_RECONSTRUCTION_PARENT_BYTE_DRIFT")
        sources = stored_reconstruction_sources(reader.json(STORED_RECONSTRUCTION_CANDIDATE),
            reader.json(STORED_RECONSTRUCTION_ARCHIVE), sources)
        additional.update({name: reader.pin(name) for name in
            (STORED_RECONSTRUCTION_CANDIDATE, STORED_RECONSTRUCTION_ARCHIVE)})
    if source_variant in ("reconstruction-r3", "anchor-prefix-r4"):
        if source_variant == "anchor-prefix-r4":
            maintenance.require(reader.pin(FORMULA_RECONSTRUCTION_CANDIDATE) == ANCHOR_PREFIX_PARENT_PIN,
                "REGRESSION_ANCHOR_PREFIX_PARENT_BYTE_DRIFT")
        sources = formula_reconstruction_sources(reader.json(FORMULA_RECONSTRUCTION_CANDIDATE),
            reader.json(FORMULA_RECONSTRUCTION_ARCHIVE), sources)
        additional.update({name: reader.pin(name) for name in
            (FORMULA_RECONSTRUCTION_CANDIDATE, FORMULA_RECONSTRUCTION_ARCHIVE)})
    if source_variant == "anchor-prefix-r4":
        sources = anchor_prefix_sources(reader.json(ANCHOR_PREFIX_CANDIDATE),
            reader.json(ANCHOR_PREFIX_ARCHIVE), sources)
        additional.update({name: reader.pin(name) for name in (ANCHOR_PREFIX_CANDIDATE, ANCHOR_PREFIX_ARCHIVE)})
    # The established target is only a rebuildable test cache, not any protected EXE.
    maintenance.require(not any((maintenance.ROOT/name).is_relative_to(maintenance.TARGET)
        for name in protected), "REGRESSION_TARGET_OVERLAPS_PROTECTED")
    expected = {**sources, **helpers, **additional, contract.CURRENT_BUILD_PIN["path"]: contract.CURRENT_BUILD_PIN}
    def read(name):
        maintenance.require(name in sources, "REGRESSION_MODULE_SOURCE_NOT_BOUND")
        source = maintenance.ROOT/name
        for parent in (source, *source.parents):
            maintenance.require(not parent.is_symlink() and not parent.is_junction(), "REGRESSION_MODULE_LINK")
            if parent == maintenance.ROOT:
                break
        maintenance.require(reader.pin(name) == sources[name], "REGRESSION_TEST_SOURCE_DRIFT")
        return reader.text(name)
    names, modules = recursive_names(read, task)
    reader.finish()
    return expected, names, modules


def require_pins(actual, expected):
    inventory = contract.inputs.inventory(actual)
    maintenance.require(all(inventory.get(name) == pin for name, pin in expected.items()),
        "REGRESSION_CURRENT_SOURCE_OR_HELPER_DRIFT")
    return actual


def require_duration(task, source_variant, maximum_seconds):
    # Only the complete current 249-case stored suite gets a longer FINITE wall
    # budget. All CPU/RAM/GO/host pressure/cleanup controls remain unchanged.
    # Repeated 180s prefix timeouts are not whole-suite qualification.
    maximum = 1200 if task == "stored-form-tests" and source_variant in ("reconstruction-r2", "reconstruction-r3", "anchor-prefix-r4") else 180
    maintenance.require(type(maximum_seconds) is int and 30 <= maximum_seconds <= maximum,
        "REGRESSION_DURATION_SCOPE")


def run_owned(destination, expected, names, maximum_seconds, task=TASK, modules=(), source_variant="current-r4"):
    maintenance.require(source_variant in SOURCE_VARIANTS, "REGRESSION_SOURCE_VARIANT_SCOPE")
    selected = case_task(task)
    require_duration(task, source_variant, maximum_seconds)
    listing = task in LIST_TASKS
    original_pins, original_capture = maintenance.pins, bounded.BoundedProcessCapture
    original_dump = json.dump
    progress = RuntimeProgress(names) if not listing else None
    captures = []
    sources = list(dict.fromkeys(maintenance.SOURCES+list(expected)+[SELF, TEST, ARCHIVE, CLEAN_ARCHIVE,
        RECURSIVE_ARCHIVE, SYNTAX_ARCHIVE, OBSERVATION_ARCHIVE, PROGRESS_ARCHIVE, RECONSTRUCTION_ARCHIVE, FORMAT_ARCHIVE,
        STORED_RECONSTRUCTION_ARCHIVE, DURATION_ARCHIVE, FORMULA_RECONSTRUCTION_ARCHIVE, ANCHOR_PREFIX_ARCHIVE]))
    class ExactCapture(original_capture):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            captures.append(self)

        def observe_runtime(self):
            if progress is not None:
                with self.lock:
                    output = bytes(self.buffers["stdout"]).decode("utf-8", errors="replace")
                progress.observe(output)

        def progress(self):
            result = super().progress()
            self.observe_runtime()
            return result

        def communicate(self, timeout):
            output, errors = super().communicate(timeout)
            if self.process.returncode == 0:
                if listing:
                    validate_listing(output, names, task)
                else:
                    validate_output(output, names, selected)
            return output, errors
    def pins(checkpoint=None):
        return require_pins(original_pins(checkpoint), expected)
    def write_receipt(result, stream, **kwargs):
        maintenance.require(isinstance(result, dict) and result.get("task") == task, "REGRESSION_RECEIPT_SCOPE")
        result.update(execution_mode="compiled_inventory_only" if listing else "full_runtime_tests",
            source_variant=source_variant, baseline_build_qualification="HISTORICAL_R4_NOT_NEW_SQL_BUILD" if source_variant != "current-r4" else "CURRENT_R4",
            expected_test_count=len(names), source_test_names=names, source_module_instances=list(modules),
            compiled_inventory_exact=(result.get("state") == "PASS_SCOPED_NOT_GATE") if listing else None,
            runtime_tests_executed=False if listing else
                (True if result.get("state") == "PASS_SCOPED_NOT_GATE"
                    and result.get("tests_passed") == len(names) else None))
        if progress is not None:
            # Original cleanup has completed before receipt serialization. A final
            # snapshot catches bytes flushed during termination without changing
            # stop_reason/state or upgrading a partial run into PASS.
            try:
                if captures:
                    captures[-1].observe_runtime()
                result["runtime_progress"] = progress.snapshot()
            except ValueError as error:
                code = str(error)
                result["runtime_progress_error"] = code if re.fullmatch(r"REGRESSION_PROGRESS_[A-Z_]+", code) else "REGRESSION_PROGRESS_INVALID"
                result["runtime_progress"] = None
                if result.get("state") == "PASS_SCOPED_NOT_GATE":
                    result["state"], result["stop_reason"] = "STOPPED_NOT_ACCEPTED", "REGRESSION_PROGRESS_INVALID"
                    result["runtime_tests_executed"] = None
        return original_dump(result, stream, **kwargs)
    # Only waiting-worker entry and explicit source/task inventories are composed.
    # The original run()/worker(), cap/readback/admission/GO/cleanup are unchanged.
    with patch.object(maintenance, "__file__", str(maintenance.ROOT/SELF)), \
            patch.object(maintenance, "TASKS", {task: list(CASES[selected][0])}), \
            patch.object(maintenance, "SOURCES", sources), patch.object(maintenance, "pins", pins), \
            patch.object(bounded, "BoundedProcessCapture", ExactCapture), patch.object(json, "dump", write_receipt):
        return maintenance.run(task, destination, maximum_seconds)


def run_worker(task):
    selected = case_task(task)
    original_call = subprocess.call
    def list_call(arguments, **kwargs):
        expected = [*CASES[selected][0], "--locked", "--offline", "--jobs", "1",
            "--color=never", "--target-dir", str(maintenance.TARGET)]
        maintenance.require(isinstance(arguments, list) and arguments[1:] == expected
            and kwargs.get("cwd") == maintenance.ROOT and kwargs.get("stdin") == subprocess.DEVNULL
            and kwargs.get("env", {}).get("RUST_TEST_THREADS") == "1", "REGRESSION_LIST_WORKER_ARGUMENT_SCOPE")
        return original_call([*arguments, "--", "--list", "--format", "terse"], **kwargs)
    with patch.object(maintenance, "TASKS", {task: list(CASES[selected][0])}):
        if task in LIST_TASKS:
            with patch.object(subprocess, "call", list_call):
                return maintenance.worker(task)
        return maintenance.worker(task)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--maximum-seconds", type=int, default=120)
    parser.add_argument("--light", action="store_true")
    parser.add_argument("--task", choices=[*CASES, *LIST_TASKS], default=TASK)
    parser.add_argument("--source-variant", choices=SOURCE_VARIANTS, default="current-r4")
    args = parser.parse_args()
    maintenance.require(Path.cwd().resolve() == maintenance.ROOT,
        "REGRESSION_ROOT_OR_TIME_SCOPE")
    require_duration(args.task, args.source_variant, args.maximum_seconds)
    windows = maintenance.Windows()  # Limits before any target/hash input.
    kind = "light" if args.light else "actual"
    destination = scoped_path(f"implementation/p09/evidence/p09-149-stored-comment-regression.{kind}-run{args.run:02}.v1.json", fresh=True)
    if not args.light:
        expected, names, modules = load_binding(windows, args.task, args.source_variant)
        return run_owned(destination, expected, names, args.maximum_seconds, args.task, modules, args.source_variant)
    from tests.test_stored_comment_regression import StoredCommentRegressionTests
    reader = AuditEvidenceReader(maintenance.ROOT, lambda: None)
    freeze = [reader.pin(name) for name in (SELF, TEST, "tools/p09/conservative_maintenance.py",
        "tools/p09/bounded_process_progress.py", ARCHIVE, CLEAN_ARCHIVE, RECURSIVE_ARCHIVE, SYNTAX_ARCHIVE,
        OBSERVATION_ARCHIVE, PROGRESS_ARCHIVE, RECONSTRUCTION_ARCHIVE, FORMAT_ARCHIVE, STORED_RECONSTRUCTION_ARCHIVE,
        DURATION_ARCHIVE, FORMULA_RECONSTRUCTION_ARCHIVE, ANCHOR_PREFIX_ARCHIVE,
        *dict.fromkeys(name for _, files, _ in CASES.values() for name in files))]
    with patch("subprocess.Popen", side_effect=AssertionError("REGRESSION_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run", side_effect=AssertionError("REGRESSION_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start", side_effect=AssertionError("REGRESSION_LIGHT_THREAD_FORBIDDEN")):
        result = unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(StoredCommentRegressionTests))
    failed = sorted({test.id().split(".")[-1] for test, _ in result.failures+result.errors+result.skipped})
    reader.finish()
    passed = result.testsRun == 50 and result.wasSuccessful() and not result.skipped
    row = {"state": "PASS_STORED_COMMENT_RUNNER_CONTRACT_ONLY_NOT_RUST_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run": result.testsRun, "tests_passed": result.testsRun-len(failed), "failed_tests": failed,
        "source_freeze": freeze, "source_freeze_exact_after": True, "SQL_native_or_Cargo_executed": False,
        "product_complete": False, "P09_gate": "OPEN"}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests")}))
    return 0 if passed else 2


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"] and sys.argv[3] in (*CASES, *LIST_TASKS):
        raise SystemExit(run_worker(sys.argv[3]))
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Z_]+", str(error)) else "REGRESSION_OPERATION_FAILED"
        print(json.dumps({"state": "FAILED_BEFORE_RUN_OR_FINAL_NOT_ACCEPTED", "error_code": code}))
        raise SystemExit(2) from None
