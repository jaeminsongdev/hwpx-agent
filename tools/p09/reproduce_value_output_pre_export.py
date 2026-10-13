#!/usr/bin/env python3
"""Physical bounded original-library replay, never a current-source/native PASS."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_value_output as old

ROOT = old.ROOT
public, q, oracle = old.public, old.q, old.oracle
LIB = "crates/hwpx-package/src/lib.rs"
ARCHIVE = "implementation/p09/source-archive/p09-41-pre-value-output-export/lib.rs"
OLD_LIB = old.SHARED[LIB]
CAPSULE = "implementation/p09/evidence/p09-40-native-form-value-output-component.current-2020.v1.json"
CAPSULE_SHA = "0d9a426de31e04b27a48c63ab30e1813827b3fc73822c516d336cc64136abce8"
LIMIT_FILES, LIMIT_BYTES = 1800, 64*1024*1024
SOURCE_BYTES = 16*1024*1024
EXCLUDED = {"crates/hwpx-package/tests/native_form_value_output_public.rs", "tools/p09/qualify_native_form_value_public_export.py", "tools/p09/reproduce_value_output_pre_export.py", "tools/p09/tests/test_native_form_value_public_export.py"}
BAD_PARTS = {".git", "target", "node_modules", "__pycache__"}


def relative(value):
    path = Path(value)
    oracle.require(not path.anchor and not path.is_absolute() and path.parts and not any(p in ("", ".", "..") for p in path.parts) and not any(p in BAD_PARTS for p in path.parts), "value_public_view_relative_path")
    return path


def select(root=ROOT):
    # Copy source/manifests only; no target/node_modules/Git/user config/private tree.
    paths = {"Cargo.toml", "Cargo.lock", "rust-toolchain.toml", old.oracle.CAPTURE,
             "implementation/p09/tools/run-hancom-2020-field-auto-number-target.ps1"}
    for base in ("crates", "protocol/generated/rust", "tools/xtask"):
        for path in (root / base).rglob("*"):
            rel = path.relative_to(root)
            if not any(p in BAD_PARTS for p in rel.parts) and path.is_file() and (path.suffix in (".rs", ".proto") or path.name == "Cargo.toml"):
                paths.add(rel.as_posix())
    paths.add("crates/hwpx-package/src/hancom_2020_minimal_header.xml")
    for base, suffixes in (("tools/p08", {".py"}), ("tools/p09", {".py"}),
                           ("protocol/private", {".json"}), ("protocol/migrations", {".md"}),
                           ("implementation/p08", {".json", ".md", ".rs", ".py"}),
                           ("implementation/p09", {".json", ".md", ".rs", ".py"})):
        for path in (root / base).rglob("*"):
            rel = path.relative_to(root)
            if not any(p in BAD_PARTS or p == "private" for p in rel.parts[2:]) and path.is_file() and path.suffix in suffixes:
                paths.add(rel.as_posix())
    for optional in ("tools/__init__.py", "protocol/generated/rust/build.rs", ".cargo/config.toml", ".cargo/config"):
        if (root / optional).is_file(): paths.add(optional)
    # Original contracts also check official document source locks. Admit only
    # their explicit repository-relative files, never a general document tree.
    for path in (root / "protocol/private").glob("p0[89]-*.json"):
        contract = json.loads(public.bounded_bytes(path, 2*1024*1024), object_pairs_hook=oracle.duplicate_guard)
        locks = contract.get("source_locks", [])
        if type(locks) is not list:
            continue  # Other contract versions use evidence labels, not source paths.
        for lock in locks:
            name = lock["path"]
            relative(name)
            oracle.require(("private" not in Path(name).parts or name.startswith("protocol/private/")) and Path(name).suffix in (".md", ".csv", ".json", ".rs", ".py"), "value_public_view_official_source_kind")
            if (root / name).is_file():
                paths.add(name)
    # Exact dependencies of the seven original legacy rows found by the actual
    # physical-view audit. Scripts are copied as source, NEVER executed here.
    from tools.p08 import build_object_automation_binding_overlay as binding
    from tools.p08 import finalize_object_automation_v2_qualification as automation
    from tools.p09 import validate_field_auto_number_hwpx_contract as numbering
    from tools.p09 import validate_field_object_caption_hwpx_contract as caption
    for path in (root / "implementation/p08/tools").glob("*.ps1"):
        paths.add(path.relative_to(root).as_posix())
    for module, names in ((binding,("ACTION_RECORDS","CANDIDATE_GRAPH","CATALOG","PRIVATE_REVIEW","PRIVATE_OVERLAY")),
                          (automation,("QUALIFIED_OVERLAY","CAPABILITY_CONTRACTS"))):
        paths.update(getattr(module,name).as_posix() for name in names)
    def add_checked(name, digest):
        public.checked(root / name, digest, SOURCE_BYTES)
        paths.add(name)
    add_checked(numbering.FIXTURE,numbering.FIXTURE_SHA256)
    paths.add(numbering.FIXTURE_AUTHORITY)
    for path,digest in {**numbering.OFFICIAL_SHA256,**caption.OFFICIAL_SHA256}.items():
        add_checked(caption.OFFICIAL_BASE + "/" + path,digest)
    receipt = json.loads(public.bounded_bytes(root / automation.PUBLIC_RECEIPT,2*1024*1024),object_pairs_hook=oracle.duplicate_guard)
    locks = receipt["source_locks"]
    add_checked((automation.PASS_RUN/"runtime-receipt.json").as_posix(),locks["runtime_receipt_sha256"])
    for feature in automation.ISOLATION_PASS_IDS:
        add_checked((automation.PASS_RUN/(feature.lower()+"-trace.private.json")).as_posix(),locks["trace_sha256_by_feature"][feature])
    # The original finalizer validates these exact negative/timeout files; they
    # are copied unchanged and bound by this view's complete raw manifest.
    for feature,run in automation.NEGATIVE_RUNS.items():
        paths.update(((run/"runtime-receipt.json").as_posix(),(run/(feature.lower()+"-trace.private.json")).as_posix()))
    paths.add((automation.TIMEOUT_RUN/"runtime-receipt.json").as_posix())
    # Only the immutable named historical artifacts, not the broader private folder.
    previous = q.shared.lifecycle.checked_json(root / old.prior.current.prior.PREDECESSOR, old.prior.current.prior.PREDECESSOR_SHA)
    paths.update(previous["historical_trace_and_artifact_sha256"])
    bridge = q.shared.lifecycle.checked_json(root / "implementation/p09/evidence/p09-34-native-root-manifest-public-export-source.current-2020.r02.v5.json", "fca4d66f3f23e75c7348daf327b92b1fd8f590ab446c43cacbe871cc56993ce4")
    for receipt in bridge["historical_source_checks"].values():
        for record in receipt.values():
            public.checked(root / (ARCHIVE if record["checked_path"] == LIB else record["checked_path"]), record["sha256"])
            paths.add(record["checked_path"])
    for base in ("fixtures/target-build/p09-32-native-form-target-20261002-01/output", "fixtures/target-build/p09-35-native-form-diagnostics-01/output"):
        for path in (root / base).iterdir():
            if path.is_file(): paths.add(path.relative_to(root).as_posix())
    paths.difference_update(EXCLUDED)
    paths = {p for p in paths if "p09-41-" not in p.lower() and "P09-41_" not in p}
    oracle.require(len(paths) <= LIMIT_FILES, "value_public_view_file_limit")
    values, total = {}, 0
    for name in sorted(paths):
        relative(name)
        actual = ARCHIVE if name == LIB else name
        try:
            raw = public.bounded_bytes(root / actual, SOURCE_BYTES)
        except (OSError, ValueError) as error:
            raise ValueError("value_public_view_source_unavailable:" + name) from error
        total += len(raw)
        oracle.require(total <= LIMIT_BYTES, "value_public_view_byte_limit")
        values[name] = raw
    oracle.require(q.sha(values[LIB]) == OLD_LIB, "value_public_view_original_library_identity")
    return values


def inventory(directory, names):
    return {name: q.sha(public.bounded_bytes(directory / name, SOURCE_BYTES)) for name in names}


def diagnose_legacy(root=ROOT):
    """Actual unchanged current legacy audit in the physical original-library view."""
    copied = select(root)
    base = (root / "fixtures/target-build").resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="p09-41-source-view-", dir=base) as temporary:
        directory = Path(temporary)
        oracle.no_links(directory)
        oracle.require(directory.resolve().parent == base and not any(directory.iterdir()), "value_public_view_root_boundary")
        for name, raw in copied.items():
            path = directory / relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream: stream.write(raw)
        environment = dict(os.environ)
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", old.ENVIRONMENT): environment.pop(key,None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        code = """import sys,json
sys.path.insert(0,sys.argv[1])
from tools.p09 import qualify_legacy_domain_contract_regression as p
q=p.current
a=q.audit_legacy()
b=q.q.shared.lifecycle.checked_json(q.ROOT/p.CAPSULE,p.CAPSULE_SHA)['actual_legacy_current_validators']
print(json.dumps([{'path':x['path'],'expected_state':y['state'],'actual_state':x['state'],'expected_errors':y['errors'],'actual_errors':x['errors'],'other_fields_equal':{k:v for k,v in x.items() if k not in ('state','errors')}=={k:v for k,v in y.items() if k not in ('state','errors')}} for x,y in zip(a,b,strict=True) if x!=y]))
"""
        process = subprocess.run([sys.executable,"-E","-B","-c",code,str(directory)],cwd=directory,env=environment,capture_output=True,timeout=180,
                                 creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        oracle.require(process.returncode == 0 and len(process.stdout)<=64*1024,"value_public_view_legacy_diagnosis_failed")
        result = json.loads(process.stdout,object_pairs_hook=oracle.duplicate_guard)
    oracle.require(not Path(temporary).exists(),"value_public_view_scratch_not_cleaned")
    return result


def reproduce(root=ROOT):
    public.checked(root / ARCHIVE, OLD_LIB)
    capsule = q.shared.lifecycle.checked_json(root / CAPSULE, CAPSULE_SHA)
    for name, digest in capsule["source_sha256"].items(): public.checked(root / name, digest)
    copied = select(root)
    manifest = {name: q.sha(raw) for name, raw in copied.items()}
    base = (root / "fixtures/target-build").resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="p09-41-source-view-", dir=base) as temporary:
        directory = Path(temporary)
        oracle.no_links(directory)
        oracle.require(directory.resolve().parent == base and not any(directory.iterdir()), "value_public_view_root_boundary")
        for name, raw in copied.items():
            path = directory / relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream: stream.write(raw)
        (directory / "fixtures/target-build").mkdir(parents=True, exist_ok=True)
        oracle.require(inventory(directory, manifest) == manifest, "value_public_view_copy_identity")
        environment = dict(os.environ)
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", old.ENVIRONMENT): environment.pop(key, None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        # Dedicated ordinary D: build cache, outside the source view. No C: clone.
        environment["CARGO_TARGET_DIR"] = str(root / "target/p09-41-pre-export-view")
        process = subprocess.run([sys.executable, "-E", "-B", str(directory / "tools/p09/qualify_native_form_value_output.py"), "--verify", str(directory / CAPSULE)], cwd=directory, env=environment, capture_output=True, timeout=600, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        oracle.require(len(process.stdout) <= 128*1024 and len(process.stderr) <= 1024*1024, "value_public_view_process_output_limit")
        if process.returncode:
            # Diagnostic names only; never echo child logs, document values or paths.
            diagnostic = subprocess.run([sys.executable, "-E", "-B", "-c", "import sys; sys.path.insert(0,sys.argv[1]); from tools.p09 import qualify_native_form_value_output as q; q.qualify()", str(directory)], cwd=directory, env=environment, capture_output=True, timeout=600, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            last = diagnostic.stderr.decode("utf-8", errors="replace").splitlines()[-1:] if diagnostic.stderr else []
            if last and last[0].startswith("ModuleNotFoundError:"):
                print(json.dumps({"diagnostic":last[0]}))
            elif last and last[0].startswith("FileNotFoundError:"):
                print(json.dumps({"diagnostic":"source_view_dependency_file_missing"}))
            elif last and last[0].startswith("ValueError:"):
                print(json.dumps({"diagnostic":last[0]}))
            frames = diagnostic.stderr.decode("utf-8", errors="replace").splitlines()
            import re
            print(json.dumps({"diagnostic_frames": [Path(m.group(1)).name + ":" + m.group(2) for line in frames if (m := re.fullmatch(r'  File "([^"]+)", line (\d+), in .+', line))]}))
            print(json.dumps({"diagnostic_codes": [line for line in frames if re.fullmatch(r"ValueError: [a-z0-9_:.\-/]+", line)]}))
        try:
            result = json.loads(process.stdout.decode("utf-8", errors="strict"), object_pairs_hook=oracle.duplicate_guard)
        except (ValueError, UnicodeError) as error:
            raise ValueError("value_public_view_result_protocol") from error
        oracle.require(process.returncode == 0 and result == {"state":"pass", "qualification_sha256":CAPSULE_SHA,"compiled_component_tests":25,"independent_complete_output_pairs":5,"native_session_started":False,"green_rows":0}, "value_public_view_full_reproduction_failed")
        oracle.require(inventory(directory, manifest) == manifest, "value_public_view_source_changed")
    oracle.require(not Path(temporary).exists(), "value_public_view_scratch_not_cleaned")
    oracle.require(inventory(root, [p for p in manifest if p != LIB]) == {p:d for p,d in manifest.items() if p != LIB} and q.sha(public.checked(root / ARCHIVE, OLD_LIB)) == OLD_LIB, "value_public_view_original_sources_changed")
    return {"scope":"physical_pre_export_source_view_not_current_verifier_or_native_pass", "capsule_sha256":CAPSULE_SHA,"complete_capsule_byte_exact_reproduction":True,
            "files":len(manifest),"bytes":sum(map(len,copied.values())),"source_sha256":manifest,
            "original_library_checked_path":ARCHIVE,"original_library_sha256":OLD_LIB,
            "python_environment_ignored_no_bytecode":True,"installed_user_and_system_site_dependencies_enabled":True,"no_function_root_test_or_lock_override":True,"scratch_cleaned":True,"native_session_started":False}


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["--diagnose-legacy"]:
            print(json.dumps({"actual_original_view_legacy_differences":diagnose_legacy()})); raise SystemExit(0)
        value = reproduce()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"value_public_original_view_reproduction_failed"})); raise SystemExit(2)
    print(json.dumps({"state":"pass","capsule_sha256":value["capsule_sha256"],"files":value["files"],"bytes":value["bytes"],"scratch_cleaned":True,"native_session_started":False}))
