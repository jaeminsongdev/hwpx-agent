#!/usr/bin/env python3
"""Actual original P09-42 CLI in a bounded physical pre-operation source view."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
if not __package__: sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_product_form_value_preparation as old

ROOT=old.ROOT
oracle,public=old.oracle,old.public
ARCHIVE="implementation/p09/source-archive/p09-43-pre-form-operation-plan/lib.rs"
OLD_LIB="b16d439bf1110754f7500677c257a1e7b83577ef2dea47c0d7092975383fbf86"
CAPSULE_SHA="c86a2d44b933cb34ac5462ddec77e8bdec94f800485040c73178fe567a1fbc48"
DELTA=b"pub mod form_value_operation;\n"
PUBLIC_P04_INPUTS={
    "implementation/p04/trust/p04-direct-route-attestation.json":"6362ab5dba0f6dbda4e59837c9e4ddcd967ae4f99760f9ebd0a6cce634dcfe00",
    "implementation/p04/trust/p04-direct-route-attestation.sig":"8737fa1cec45827bc87c3837b056cc36078a29b2aff22e4cf4ffdcaff0b215fb",
}


def original_product(raw,archived):
    oracle.require(oracle.sha(archived)==OLD_LIB and raw.count(DELTA)==1
                   and raw.replace(DELTA,b"",1)==archived,"form_operation_product_inverse_invalid")
    old.product_inverse(archived,public.checked(ROOT/old.ARCHIVE,old.OLD_LIB))


def select():
    raw=public.checked(ROOT/old.CAPSULE,CAPSULE_SHA,2*1024*1024)
    capsule=json.loads(raw,object_pairs_hook=oracle.duplicate_guard)
    before=public.checked(ROOT/ARCHIVE,OLD_LIB)
    original_product(public.bounded_bytes(ROOT/old.LIB,2*1024*1024),before)
    prior_raw=public.checked(ROOT/old.PREDECESSOR,old.PREDECESSOR_SHA,2*1024*1024)
    prior=json.loads(prior_raw,object_pairs_hook=oracle.duplicate_guard)
    manifest={**prior["physical_pre_export_original_reproduction"]["source_sha256"],
              **prior["source_sha256"],**capsule["source_sha256"],
              old.PREDECESSOR:old.PREDECESSOR_SHA,old.CAPSULE:CAPSULE_SHA}
    manifest.update({old.FIXTURE+"/"+name:digest for name,digest in capsule["fixture_snapshot"]["file_sha256"].items()})
    # Original compiled product library includes exactly these existing public
    # attestation/signature files. No issuer key, broader trust folder or DB.
    manifest.update(PUBLIC_P04_INPUTS)
    origins={name:ARCHIVE if name==old.LIB else name for name in manifest}
    oracle.require(set(capsule["source_sha256"])==set(old.SOURCES) and len(manifest)<=old.prior.history.LIMIT_FILES,
                   "form_operation_view_source_inventory")
    copied={}
    total=0
    for name,digest in sorted(manifest.items()):
        old.prior.history.relative(name)
        value=public.checked(ROOT/origins[name],digest,old.prior.history.SOURCE_BYTES)
        total+=len(value)
        oracle.require(total<=old.prior.history.LIMIT_BYTES,"form_operation_view_source_bytes")
        copied[name]=value
    return copied,manifest,origins


def inventory(root,manifest):
    return {name:oracle.sha(public.bounded_bytes(root/name,old.prior.history.SOURCE_BYTES)) for name in manifest}


def reproduce():
    copied,manifest,origins=select()
    base=ROOT/"fixtures/target-build"
    oracle.no_links(base)
    with tempfile.TemporaryDirectory(prefix="p09-43-source-view-",dir=base) as temporary:
        directory=Path(temporary)
        oracle.no_links(directory)
        oracle.require(directory.resolve().parent==base.resolve() and not any(directory.iterdir()),"form_operation_view_boundary")
        for name,value in copied.items():
            path=directory/old.prior.history.relative(name)
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("xb") as stream: stream.write(value)
        oracle.require(inventory(directory,manifest)==manifest,"form_operation_view_copy_identity")
        environment=dict(os.environ)
        for key in ("PYTHONPATH","PYTHONHOME","PYTHONSTARTUP",old.prior.old.ENVIRONMENT): environment.pop(key,None)
        environment["PYTHONDONTWRITEBYTECODE"]="1"
        environment["CARGO_TARGET_DIR"]=str(ROOT/"target/p09-43-pre-operation-view")
        process=subprocess.run([sys.executable,"-E","-B",str(directory/"tools/p09/qualify_product_form_value_preparation.py"),"--verify",str(directory/old.CAPSULE)],cwd=directory,env=environment,capture_output=True,timeout=600,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
        oracle.require(len(process.stdout)<=128*1024 and len(process.stderr)<=1024*1024,"form_operation_view_process_limit")
        result=json.loads(process.stdout.decode("utf-8",errors="strict"),object_pairs_hook=oracle.duplicate_guard)
        if process.returncode:
            diagnostic=subprocess.run([sys.executable,"-E","-B","-c","from tools.p09 import qualify_product_form_value_preparation as q; q.qualify()"],cwd=directory,env=environment,capture_output=True,timeout=600,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            frames=diagnostic.stderr.decode("utf-8",errors="replace").splitlines()
            print(json.dumps({"diagnostic_codes":[line for line in frames if re.fullmatch(r"ValueError: [a-z0-9_:.\-/]+",line)],
                              "diagnostic_frames":[Path(m.group(1)).name+":"+m.group(2) for line in frames if (m:=re.fullmatch(r'  File "([^\"]+)", line (\d+), in .+',line))]}))
        oracle.require(process.returncode==0 and result=={
            "state":"pass","qualification_sha256":CAPSULE_SHA,"capsule_bytes":8310,"source_pins":13,
            "actual_product_cases":10,"production_private_units":2,"whole_output_pairs":5,
            "form_route_denied":True,"native_session_started":False,"green_rows":0},"form_operation_view_full_original_reproduction_failed")
        oracle.require(inventory(directory,manifest)==manifest,"form_operation_view_sources_changed")
    oracle.require(not Path(temporary).exists(),"form_operation_view_owned_scratch_not_cleaned")
    for name,digest in manifest.items(): public.checked(ROOT/origins[name],digest,old.prior.history.SOURCE_BYTES)
    return {"scope":"physical_original_product_preparation_view_not_current_old_verifier_or_native_pass",
            "capsule_sha256":CAPSULE_SHA,"complete_original_capsule_byte_exact_reexecution":True,
            "files":len(manifest),"bytes":sum(map(len,copied.values())),"source_sha256":manifest,
            "declared_original_product_archive":ARCHIVE,"declared_original_product_sha256":OLD_LIB,
            "no_function_root_test_or_lock_override":True,"python_environment_ignored_no_bytecode":True,
            "installed_user_and_system_site_dependencies_enabled":True,"owned_scratch_cleaned":True,
            "native_session_started":False}


if __name__=="__main__":
    try: value=reproduce()
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"form_operation_original_reproduction_failed"}))
        raise SystemExit(2)
    print(json.dumps({"state":"pass","complete_original_capsule_reexecution":True,
                      "capsule_sha256":value["capsule_sha256"],"files":value["files"],"bytes":value["bytes"],
                      "native_session_started":False}))
