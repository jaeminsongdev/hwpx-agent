"""Whole-AST proof of the explicit build-contract delta, not a permissive projection."""
import ast
import base64
import copy
import hashlib

import conservative_maintenance as c
from audit_evidence_io import AuditEvidenceReader
from issuer_sql_build_contract import ARCHIVE

DRIVERS = ("tools/p09/run_formula_issuer_live_sql_probe.py", "tools/p09/run_formula_issuer_authority_sql_probe.py")


def originals():
    reader = AuditEvidenceReader(c.ROOT, lambda: None)
    result = {}
    for row in reader.json(ARCHIVE)["files"]:
        raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        c.require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "SQL_BUILD_DRIVER_PREIMAGE_DRIFT")
        if row["path"] in DRIVERS:
            result[row["path"]] = ast.parse(raw.decode("utf-8"))
    reader.finish()
    c.require(set(result) == set(DRIVERS), "SQL_BUILD_DRIVER_PREIMAGE_CLOSURE")
    return result


def expected_driver(old):
    expected = copy.deepcopy(old)
    index = next(i for i, node in enumerate(expected.body) if isinstance(node, ast.ImportFrom)
        and node.module == "live_sql_evidence_reader")
    expected.body.insert(index+1, ast.parse("from issuer_sql_build_contract import bind_probe_build, consumer_sources").body[0])
    main = next(node for node in expected.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    first = next(i for i, node in enumerate(main.body) if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "build_file" for t in node.targets))+1
    last = next(i for i, node in enumerate(main.body) if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "historical_build_path" for t in node.targets))
    c.require(last-first == 6, "SQL_BUILD_DRIVER_ORIGINAL_GUARD_INVENTORY")
    coverage = copy.deepcopy(main.body[first+3])
    main.body[first:last] = ast.parse("build, crypto_executable, build_binding = bind_probe_build(reader, build_file)").body+[coverage]
    additions = next(node.value for node in main.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "additions" for t in node.targets))
    additions.elts += ast.parse("[*consumer_sources(build_binding)]", mode="eval").body.elts
    receipt = next(node.value for node in main.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "receipt" for t in node.targets))
    index = next(i for i, key in enumerate(receipt.keys) if key.value == "protected_executables_exact_after")+1
    receipt.keys.insert(index, ast.Constant(value="compiled_build_binding"))
    receipt.values.insert(index, ast.Name(id="build_binding", ctx=ast.Load()))
    return expected


def restore_build_contract_driver_changes(tree, name):
    from tests.sql_runtime_driver_delta import restore_runtime_driver_changes
    try:
        tree = restore_runtime_driver_changes(tree, name)
    except ValueError as error:
        if str(error) != "SQL_RUNTIME_NONRESOURCE_AST_CHANGED":
            raise
        raise ValueError("SQL_BUILD_NONBINDING_AST_CHANGED") from None
    old = originals()[name]
    c.require(ast.dump(tree, include_attributes=False) == ast.dump(expected_driver(old), include_attributes=False),
        "SQL_BUILD_NONBINDING_AST_CHANGED")
    return copy.deepcopy(old)
