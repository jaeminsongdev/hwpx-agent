"""Exact whole-AST runtime resource delta before older build/IO/Job guards."""
import ast
import base64
import copy
import hashlib

import conservative_maintenance as c
from audit_evidence_io import AuditEvidenceReader
from sql_runtime_supervision import ARCHIVE
from tests.sql_build_driver_delta import DRIVERS


def originals():
    reader = AuditEvidenceReader(c.ROOT, lambda: None)
    rows = {}
    for row in reader.json(ARCHIVE)["files"]:
        raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        c.require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "SQL_RUNTIME_PREIMAGE_DRIFT")
        if row["path"] in DRIVERS:
            rows[row["path"]] = ast.parse(raw.decode("utf-8"))
    reader.finish()
    c.require(set(rows) == set(DRIVERS), "SQL_RUNTIME_PREIMAGE_CLOSURE")
    return rows


def expected_driver(old):
    expected = copy.deepcopy(old)
    index = next(i for i, node in enumerate(expected.body) if isinstance(node, ast.ImportFrom)
        and node.module == "sql_percentage_resources")
    imported = expected.body[index]
    c.require([(a.name, a.asname) for a in imported.names] ==
        [("PercentageResources", "IdleResources"), ("admit", None), ("resource_policy", None)],
        "SQL_RUNTIME_ORIGINAL_IMPORT_SCOPE")
    imported.names = imported.names[1:]
    expected.body.insert(index+1, ast.parse(
        "from sql_runtime_supervision import SQLRuntimeResources as IdleResources, finish_watcher, LocalDockerJobFactory as OwnedSQLJobFactory").body[0])
    job_import = next(node for node in expected.body if isinstance(node, ast.ImportFrom) and node.module == "owned_sql_job")
    c.require([(a.name, a.asname) for a in job_import.names] ==
        [("OwnedSQLJobFactory", None), ("OwnedSQLJobFailure", None), ("record_owned_jobs", None)],
        "SQL_RUNTIME_ORIGINAL_JOB_IMPORT_SCOPE")
    job_import.names = job_import.names[1:]
    main = next(node for node in expected.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    command = next(node for node in main.body if isinstance(node, ast.FunctionDef) and node.name == "command")
    checkpoint = next(node for node in command.body if isinstance(node, ast.FunctionDef) and node.name == "checkpoint")
    c.require(len(checkpoint.body) == 1 and isinstance(checkpoint.body[0], ast.If)
        and len(checkpoint.body[0].body) == 2, "SQL_RUNTIME_ORIGINAL_CHECKPOINT_SCOPE")
    checkpoint.body[0].body.append(ast.parse("resources.checkpoint_io()").body[0])
    additions = next(node.value for node in main.body if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "additions" for t in node.targets))
    additions.elts.append(ast.Constant(value="tools/p09/sql_runtime_supervision.py"))
    # 선언된 helper가 서로 겹쳐도 입력은 누락하지 않고 최초 순서로 결합한다.
    # compiled source 중복 및 원래 coverage require는 그대로 남긴다.
    extension = next(node for node in main.body if isinstance(node, ast.AugAssign)
        and isinstance(node.target, ast.Name) and node.target.id == "sources")
    c.require(ast.dump(extension, include_attributes=False) == ast.dump(
        ast.parse("sources += [path for path in additions if path not in sources]").body[0],
        include_attributes=False), "SQL_RUNTIME_ORIGINAL_SOURCE_UNION_SCOPE")
    extension.value = ast.parse(
        "list(dict.fromkeys(path for path in additions if path not in sources))", mode="eval").body
    outer = next(node for node in main.body if isinstance(node, ast.Try) and node.finalbody)
    c.require(ast.dump(ast.Module(body=outer.finalbody[:2], type_ignores=[]), include_attributes=False) ==
        ast.dump(ast.parse("resources.done.set()\nif resources.thread.is_alive():\n    resources.thread.join(timeout=3)"),
            include_attributes=False), "SQL_RUNTIME_ORIGINAL_FINALLY_SCOPE")
    outer.finalbody[:2] = ast.parse("finish_watcher(resources, receipt)").body
    return expected


def restore_runtime_driver_changes(tree, name):
    old = originals()[name]
    c.require(ast.dump(tree, include_attributes=False) == ast.dump(expected_driver(old), include_attributes=False),
        "SQL_RUNTIME_NONRESOURCE_AST_CHANGED")
    return copy.deepcopy(old)
