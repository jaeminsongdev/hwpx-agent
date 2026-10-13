"""One unchanged r8 profile rerun; retain only closed failure locations/kinds."""
import json
import re
from unittest.mock import patch

import run_output_stage_profile as subject
from audit_evidence_io import AuditEvidenceReader

SELF = "tools/p09/diagnose_output_stage_profile.py"
FAILURE_NAMES = frozenset({"Source", "Selection", "Protection", "NoTargets", "NoChange", "Limit",
    "Patch", "Writer", "Preservation", "Readback"})


def main():
    windows = subject.maintenance.Windows()
    expected, names, modules = subject.load_binding(windows, subject.TASK)
    reader = AuditEvidenceReader(subject.maintenance.ROOT, lambda: None)
    expected[SELF] = reader.pin(SELF)
    reader.finish()
    destination = subject.scoped_path(
        "implementation/p09/evidence/p09-149-output-stage-profile.actual-run03.v1.json", fresh=True)
    original_capture, original_dump = subject.bounded.BoundedProcessCapture, json.dump
    diagnostics = []
    class DiagnosticCapture(original_capture):
        def communicate(self, timeout):
            output, errors = super().communicate(timeout)
            if self.process.returncode != 0:
                text = output + "\n" + errors
                kinds = sorted(set(re.findall(r"(?m)^Error: ([A-Za-z]+)\s*$", text)) & FAILURE_NAMES)
                locations = sorted(set(re.findall(r"(?:crates[/\\]hwpx-package[/\\])?src[/\\]document_import[/\\]fields[/\\]semantics[/\\]evaluation[/\\]output\.rs:([0-9]+):([0-9]+)", text)))[:8]
                diagnostics.append({"allowed_error_kinds": kinds,
                    "panic_locations": [{"path": subject.SOURCE, "line": int(line), "column": int(column)}
                        for line, column in locations],
                    "borrow_panic_observed": bool(re.search(r"already (?:mutably )?borrowed", text)),
                    "assertion_panic_observed": "assertion" in text,
                    "expected_test_failure_observed": bool(re.search(r"(?m)^test " + re.escape(subject.NAME) + r" \.\.\. FAILED$", text)),
                    "raw_output_persisted": False})
            return output, errors
    def dump(result, stream, **kwargs):
        result["closed_failure_diagnostic"] = diagnostics[-1] if diagnostics else None
        result["diagnostic_wrapper"] = SELF
        return original_dump(result, stream, **kwargs)
    with patch.object(subject.bounded, "BoundedProcessCapture", DiagnosticCapture), patch.object(json, "dump", dump):
        return subject.run_owned(destination, expected, names, modules, subject.TASK, 180)


if __name__ == "__main__":
    raise SystemExit(main())
