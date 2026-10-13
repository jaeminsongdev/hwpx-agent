"""P147 absence batch source delta and four synthetic identities; no Docker/audit run."""
import ast
import base64
import copy
import hashlib
import unittest
from unittest.mock import Mock

from audit_evidence_io import AuditEvidenceReader
from bounded_container_absence import validate_absence, references_checked
import verify_formula_issuer_live_current as subject

ARCHIVE = "implementation/p09/source-archive/p09-149-pre-live-bounded-absence/source-preimages.v1.json"
NEW_PINS = ("tools/p09/bounded_container_absence.py", "tools/p09/tests/test_bounded_container_absence.py",
    "tools/p09/bounded_process_progress.py", "tools/p09/tests/test_live_absence_integration.py",
    "tools/p09/verify_live_absence_light.py", ARCHIVE)
REFS = ["a"*64, "hwpx-p146-12345678-1234-1234-1234-123456789abc",
    "b"*64, "hwpx-p146-23456789-1234-1234-1234-123456789abc"]


def dump(node):
    return ast.dump(node, include_attributes=False)


def require(ok):
    if not ok:
        raise ValueError("live_absence_undeclared_delta")


def function(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def read_baseline(reader):
    archive = reader.json(ARCHIVE)
    rows = [row for row in archive["files"] if row["path"] == subject.SELF]
    require(archive["schema_version"] == "hwpx-agent.source-preimages/v1" and len(rows) == 1)
    row = rows[0]
    raw = base64.b64decode("".join(row["base64_chunks"]), validate=True)
    require((len(raw), hashlib.sha256(raw).hexdigest()) == (row["bytes"], row["sha256"]))
    return ast.parse(raw.decode("utf-8"))


def case_loop(audit):
    loops = [n for n in audit.body if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple)
        and [t.id for t in n.target.elts] == ["number", "mode", "outcome"]]
    require(len(loops) == 1)
    return loops[0]


def normalize_live_absence_audit(original, current):
    """Invert only exact batching, dependency pins, and additive guards; keep all else exact."""
    normalized = copy.deepcopy(current)
    initialization = ast.parse("current_references = []").body[0]
    matches = [n for n in normalized.body if dump(n) == dump(initialization)]
    require(len(matches) == 1)
    normalized.body.remove(matches[0])
    first_pin = next(n for n in normalized.body if isinstance(n, ast.For)
        and isinstance(n.target, ast.Name) and n.target.id == "path")
    additions = [n.value for n in first_pin.iter.elts if isinstance(n, ast.Constant) and n.value in NEW_PINS]
    require(tuple(additions) == NEW_PINS)
    first_pin.iter.elts = [n for n in first_pin.iter.elts if not isinstance(n, ast.Constant) or n.value not in NEW_PINS]
    old_loop, new_loop = case_loop(original), case_loop(normalized)
    collection = ast.parse('current_references.extend((run["container_id"], run["container_name"]))').body[0]
    matches = [n for n in new_loop.body if dump(n) == dump(collection)]
    old_queries = [n for n in old_loop.body if isinstance(n, ast.For)
        and isinstance(n.target, ast.Name) and n.target.id == "reference"]
    require(len(matches) == len(old_queries) == 1)
    new_loop.body[new_loop.body.index(matches[0])] = copy.deepcopy(old_queries[0])
    batch = ast.parse('absence = inspect_absence(docker, current_references, checkpoint, "owned_container_present")').body[0]
    matches = [n for n in normalized.body if dump(n) == dump(batch)]
    require(len(matches) == 1 and normalized.body.index(matches[0]) == normalized.body.index(new_loop)+1)
    normalized.body.remove(matches[0])
    for module, name in (("tests.test_bounded_container_absence", "BoundedContainerAbsenceTests"),
            ("tests.test_live_absence_integration", "LiveAbsenceIntegrationTests")):
        expected = ast.parse(f"from {module} import {name}").body[0]
        imports = [n for n in normalized.body if dump(n) == dump(expected)]
        require(len(imports) == 1)
        normalized.body.remove(imports[0])
    loops = [n for n in normalized.body if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple)
        and [t.id for t in n.target.elts] == ["cls", "count"]]
    require(len(loops) == 1)
    expected = ast.parse("((BoundedContainerAbsenceTests, 21), (LiveAbsenceIntegrationTests, 5))", mode="eval").body
    require([dump(n) for n in loops[0].iter.elts[-2:]] == [dump(n) for n in expected.elts])
    loops[0].iter.elts = loops[0].iter.elts[:-2]
    require(dump(normalized) == dump(original))
    return normalized


def normalize_live_absence_module(original, current):
    normalized = copy.deepcopy(current)
    audit = function(normalized, "audit")
    normalized.body[normalized.body.index(audit)] = normalize_live_absence_audit(function(original, "audit"), audit)
    expected_import = ast.parse("from bounded_container_absence import inspect_absence").body[0]
    imports = [n for n in normalized.body if dump(n) == dump(expected_import)]
    require(len(imports) == 1)
    normalized.body.remove(imports[0])
    archives = next(n for n in normalized.body if isinstance(n, ast.Assign)
        and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "ARCHIVES")
    require(archives.value.elts[-1].value == "p09-149-pre-live-bounded-absence")
    archives.value.elts.pop()
    require(dump(normalized) == dump(original))
    return normalized


class LiveAbsenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = AuditEvidenceReader(subject.ROOT, lambda: None)
        try:
            cls.before = read_baseline(cls.reader)
            cls.after = ast.parse(cls.reader.text(subject.SELF))
        except BaseException:
            cls.reader = cls.before = cls.after = None
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            cls.reader.finish()
        finally:
            cls.reader = cls.before = cls.after = None

    def test_whole_module_and_all_other_case_requirements_are_preserved(self):
        normalize_live_absence_module(self.before, self.after)

    def test_one_batch_and_original_two_case_identity_inventory_are_exact(self):
        audit = function(self.after, "audit")
        calls = [n for n in ast.walk(audit) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name) and n.func.id == "inspect_absence"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(dump(calls[0]), dump(ast.parse(
            'inspect_absence(docker, current_references, checkpoint, "owned_container_present")', mode="eval").body))
        self.assertEqual(dump(case_loop(audit).iter), dump(case_loop(function(self.before, "audit")).iter))
        self.assertEqual(len(case_loop(audit).iter.elts), 2)
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess"
            and n.func.attr in {"run", "Popen", "call"} for n in ast.walk(audit)))

    def test_checked_collection_and_batch_keep_all_four_references_in_order(self):
        audit = function(self.after, "audit")
        collection = next(n for n in case_loop(audit).body if isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
            and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == "current_references")
        batch = next(n for n in audit.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id == "absence")
        expected = [{"reference": value, "absent": True} for value in REFS]
        inspect = Mock(return_value=expected)
        checkpoint = Mock()
        scope = {"current_references": [], "docker": "C:/fixture/docker.exe",
            "checkpoint": checkpoint, "inspect_absence": inspect}
        for index in (0, 2):
            scope["run"] = {"container_id": REFS[index], "container_name": REFS[index+1]}
            exec(compile(ast.Module(body=[copy.deepcopy(collection)], type_ignores=[]), "<checked-collection>", "exec"), scope)
        self.assertEqual(scope["current_references"], REFS)
        exec(compile(ast.Module(body=[copy.deepcopy(batch)], type_ignores=[]), "<checked-batch>", "exec"), scope)
        inspect.assert_called_once_with(scope["docker"], REFS, checkpoint, "owned_container_present")
        self.assertIs(scope["absence"], expected)

    def test_p146_batch_requires_exact_missing_set_and_no_present_or_daemon_output(self):
        missing = lambda values: "".join(f"Error: No such object: {value}\n" for value in values)
        self.assertEqual(references_checked(REFS), REFS)
        result = validate_absence(1, "", missing(list(reversed(REFS))), REFS, "owned_container_present")
        self.assertEqual(result, [{"reference": value, "absent": True} for value in REFS])
        for errors in (missing(REFS[:-1]), missing([REFS[0]]*4), missing(REFS[:3]+["c"*64]),
                "Cannot connect to Docker daemon", missing(REFS)+"extra-fixture-diagnostic\n"):
            with self.assertRaisesRegex(ValueError, "^owned_container_present$"):
                validate_absence(1, "", errors, REFS, "owned_container_present")
        for code, output in ((0, ""), (1, "existing-id\n")):
            with self.assertRaisesRegex(ValueError, "^owned_container_present$"):
                validate_absence(code, output, missing(REFS), REFS, "owned_container_present")

    def test_removed_reference_case_requirement_or_gate_mutations_are_rejected(self):
        for mutation in ("reference", "case", "predicate", "gate"):
            changed = copy.deepcopy(self.after)
            audit = function(changed, "audit")
            if mutation == "reference":
                call = next(n for n in ast.walk(audit) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "inspect_absence")
                call.args[1] = ast.List(elts=[], ctx=ast.Load())
            elif mutation == "case":
                case_loop(audit).iter.elts.pop()
            elif mutation == "predicate":
                call = next(n for n in ast.walk(audit) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "require"
                    and isinstance(n.args[-1], ast.Constant) and n.args[-1].value == "current_case_pin_inventory")
                call.args[0] = ast.Constant(value=True)
            else:
                result = next(n for n in audit.body if isinstance(n, ast.Return)).value
                index = next(i for i, key in enumerate(result.keys) if key.value == "P09_gate")
                result.values[index] = ast.Constant(value="PASS")
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "^live_absence_undeclared_delta$"):
                normalize_live_absence_module(self.before, changed)


if __name__ == "__main__":
    unittest.main()
