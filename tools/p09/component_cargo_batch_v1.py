"""One opt-in Cargo dependency graph for exact P09 component cases only.

No process creation, cached PASS, Native authorization or resource-policy change.
The existing owned launcher/capture/guard must execute command() and preserve the
complete bounded stdout before validate_stdout(). Multiple -p selections unify
dependency features: https://doc.rust-lang.org/cargo/reference/resolver.html#features
"""
import re
from pathlib import PureWindowsPath

PROFILE = "p09.component-cargo-exact-batch/v1"
TARGETS = {
    "document_import_reference_targets": "hwpx-package",
    "reference_source_product": "hwpx-agent-cli",
    "reference_validation_product": "hwpx-agent-cli",
}
MAX_ARGUMENTS = 64
MAX_ARGUMENT_BYTES = 24000
MAX_OUTPUT_BYTES = 32768
CASE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)*")
CASE_LINE = re.compile(r"test (\S+) \.\.\. (ok|FAILED|ignored)")
RUNNING = re.compile(r"running ([0-9]+) tests?")
SUMMARY = re.compile(
    r"test result: (ok|FAILED)\. ([0-9]+) passed; ([0-9]+) failed; "
    r"([0-9]+) ignored; ([0-9]+) measured; ([0-9]+) filtered out; "
    r"finished in [0-9]+(?:\.[0-9]+)?s"
)


def require(ok, code):
    if not ok:
        raise ValueError("COMPONENT_BATCH_" + code)


def normalize(spec):
    require(type(spec) is dict and 1 <= len(spec) <= len(TARGETS), "SPEC")
    require(all(type(target) is str and target in TARGETS for target in spec), "TARGET")
    result = []
    seen = set()
    for target in sorted(spec):
        cases = spec[target]
        require(type(cases) in (list, tuple) and 1 <= len(cases) <= MAX_ARGUMENTS, "CASES")
        for case in cases:
            require(type(case) is str and 1 <= len(case) <= 512 and CASE.fullmatch(case), "CASE_ID")
            require(case not in seen, "DUPLICATE_CASE")
            seen.add(case)
        result.append((target, tuple(sorted(cases))))
    require(len(seen) <= MAX_ARGUMENTS, "CASE_COUNT")
    return tuple(result)


def command(cargo, spec, *, no_run=False):
    """Exact filters are libtest positional OR filters, never substring matches.

    no_run is for a separate build-cache observation only, not test acceptance.
    No shell, alternate targets, all-features, workspace or guard overrides.
    """
    require(type(cargo) is str and "\0" not in cargo and PureWindowsPath(cargo).is_absolute()
            and PureWindowsPath(cargo).name.lower() == "cargo.exe", "CARGO_PATH")
    require(type(no_run) is bool, "MODE")
    normalized = normalize(spec)
    args = [cargo, "test", "--offline", "--locked", "-j", "1"]
    for package in sorted({TARGETS[target] for target, _ in normalized}):
        args.extend(("-p", package))
    for target, _ in normalized:
        args.extend(("--test", target))
    if no_run:
        args.append("--no-run")
    else:
        args.extend(("--", "--exact", "--test-threads=1", "--format=pretty", "--color=never"))
        args.extend(case for _, cases in normalized for case in cases)
    require(len(args) <= MAX_ARGUMENTS, "ARGUMENT_COUNT")
    require(sum(len(arg.encode("utf-16-le")) for arg in args) <= MAX_ARGUMENT_BYTES, "ARGUMENT_BYTES")
    return tuple(args)


def validate_stdout(output, spec):
    """Bind every complete serial harness group to one exact declared case set.

    No empty target, ignored result, duplicate, extra, missing, failed, partial or
    invented summary can preserve a PASS. Original source verification is external.
    """
    require(type(output) is str, "OUTPUT_TYPE")
    require(len(output.encode("utf-8")) <= MAX_OUTPUT_BYTES, "OUTPUT_BYTES")
    normalized = normalize(spec)
    expected = {frozenset(cases): target for target, cases in normalized}
    require(len(expected) == len(normalized), "AMBIGUOUS_GROUP")
    found = {}
    rows = None
    declared = None
    for line in output.splitlines():
        if not line:
            continue
        if match := RUNNING.fullmatch(line):
            require(rows is None, "UNCLOSED_GROUP")
            declared = int(match[1])
            require(1 <= declared <= MAX_ARGUMENTS, "RUNNING_COUNT")
            rows = []
            continue
        if match := CASE_LINE.fullmatch(line):
            require(rows is not None and match[2] == "ok", "CASE_STATUS")
            require(CASE.fullmatch(match[1]) and len(rows) < declared, "CASE_ROW")
            rows.append(match[1])
            continue
        if match := SUMMARY.fullmatch(line):
            require(rows is not None and match[1] == "ok", "SUMMARY_STATUS")
            passed, failed, ignored, measured, filtered = map(int, match.groups()[1:])
            require(passed == declared == len(rows) and failed == ignored == measured == 0,
                    "SUMMARY_COUNTS")
            require(len(set(rows)) == len(rows), "DUPLICATE_RESULT")
            target = expected.get(frozenset(rows))
            require(target is not None and target not in found, "GROUP_SCOPE")
            found[target] = dict(cases=tuple(rows), passed=passed, filtered=filtered)
            rows = None
            declared = None
            continue
        require(False, "UNEXPECTED_OUTPUT")
    require(rows is None and set(found) == {target for target, _ in normalized}, "COMPLETE_GROUPS")
    return dict(profile=PROFILE, groups={target: found[target] for target in sorted(found)},
                passed=sum(row["passed"] for row in found.values()),
                native_authority=False, acceptance_delta=0,
                exact_case_sets_and_complete_summaries=True)
