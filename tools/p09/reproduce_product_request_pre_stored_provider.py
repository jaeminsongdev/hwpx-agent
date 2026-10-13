#!/usr/bin/env python3
"""Whole unchanged P09-44 CLI/capsule in an authentic pre-stored-provider source view."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import record_stored_form_provider_progress as progress

ROOT=progress.ROOT
old,oracle,public=progress.old,progress.oracle,progress.public
LIMIT_FILES,LIMIT_BYTES,SOURCE_BYTES=1800,64*1024*1024,16*1024*1024
EXPECTED_RESULT={"state":"pass","qualification_sha256":progress.CAPSULE_SHA,"capsule_bytes":221043,
                 "source_pins":11,"actual_public_product_tests":10,"actual_private_tests":2,
                 "actual_python_source_guards":8,"whole_original_p43_reexecuted":True,
                 "native_session_started":False,"green_rows":0}
relative=old.history.relative


def select():
    preserved=progress.preserve()
    capsule=json.loads(public.checked(ROOT/old.CAPSULE,progress.CAPSULE_SHA,2*1024*1024),
                       object_pairs_hook=oracle.duplicate_guard)
    graph=capsule["complete_original_form_operation_reproduction"]["source_sha256"]
    oracle.require(len(graph)==1479 and set(capsule["source_sha256"])==set(old.SOURCES),"stored_provider_view_original_inventory")
    manifest={**graph,**capsule["source_sha256"],old.CAPSULE:progress.CAPSULE_SHA}
    origins={name:progress.ARCHIVE+progress.CHANGED[name][0] if name in progress.CHANGED else name for name in manifest}
    oracle.require(len(manifest)<=LIMIT_FILES and not any("p09-45" in name or "form_stored_provider" in name
                                                       for name in manifest),"stored_provider_view_inventory")
    oracle.require(len({str(relative(name)).casefold() for name in manifest})==len(manifest),"stored_provider_view_path_alias")
    copied={};total=0
    for name,digest in sorted(manifest.items()):
        relative(name);relative(origins[name])
        value=public.checked(ROOT/origins[name],digest,SOURCE_BYTES);total+=len(value)
        oracle.require(total<=LIMIT_BYTES,"stored_provider_view_source_bytes");copied[name]=value
    oracle.require(progress.preserve()==preserved,"stored_provider_view_origins_changed")
    return copied,manifest,origins


def inventory(directory,manifest):
    return {name:oracle.sha(public.bounded_bytes(directory/relative(name),SOURCE_BYTES)) for name in manifest}


def validate_result(code,stdout,stderr):
    oracle.require(len(stdout)<=128*1024 and len(stderr)<=1024*1024,"stored_provider_view_process_limit")
    value=json.loads(stdout.decode("utf-8",errors="strict"),object_pairs_hook=oracle.duplicate_guard)
    canonical=old.original.old.prior.q.shared.lifecycle.canonical_bytes
    oracle.require(code==0 and canonical(value)==canonical(EXPECTED_RESULT),"stored_provider_view_complete_original_replay_failed")


def reproduce():
    copied,manifest,origins=select();base=ROOT/"fixtures/target-build";oracle.no_links(base)
    with tempfile.TemporaryDirectory(prefix="p09-45-source-view-",dir=base) as temporary:
        directory=Path(temporary);oracle.no_links(directory)
        oracle.require(directory.resolve().parent==base.resolve() and not any(directory.iterdir()),"stored_provider_view_scratch_boundary")
        for name,value in copied.items():
            target=directory/relative(name);target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as stream:stream.write(value)
        oracle.require(inventory(directory,manifest)==manifest,"stored_provider_view_copy_identity")
        environment=dict(os.environ)
        for key in ("PYTHONPATH","PYTHONHOME","PYTHONSTARTUP",old.original.old.prior.old.ENVIRONMENT):environment.pop(key,None)
        environment["PYTHONDONTWRITEBYTECODE"]="1"
        environment["CARGO_TARGET_DIR"]=str(ROOT/"target/p09-45-pre-provider-view")
        command=[sys.executable,"-E","-B",str(directory/"tools/p09/qualify_product_form_request.py"),"--verify",str(directory/old.CAPSULE)]
        process=subprocess.run(command,cwd=directory,env=environment,capture_output=True,timeout=1800,
                               creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
        if process.returncode:
            diagnostic=subprocess.run([sys.executable,"-E","-B","-c",
                                       "from tools.p09 import qualify_product_form_request as q; q.qualify()"],
                                      cwd=directory,env=environment,capture_output=True,timeout=1800,
                                      creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            oracle.require(len(diagnostic.stdout)<=128*1024 and len(diagnostic.stderr)<=1024*1024,"stored_provider_view_diagnostic_limit")
            lines=diagnostic.stderr.decode("utf-8",errors="replace").splitlines()
            print(json.dumps({"diagnostic_codes":[line for line in lines if re.fullmatch(r"ValueError: [a-z0-9_:.\-/]+",line)],
                              "diagnostic_frames":[Path(match.group(1)).name+":"+match.group(2) for line in lines
                                  if (match:=re.fullmatch(r'  File "([^\"]+)", line (\d+), in .+',line))]}))
        validate_result(process.returncode,process.stdout,process.stderr)
        oracle.require(inventory(directory,manifest)==manifest,"stored_provider_view_sources_changed")
    oracle.require(not Path(temporary).exists(),"stored_provider_view_scratch_not_cleaned")
    for name,digest in manifest.items():public.checked(ROOT/origins[name],digest,SOURCE_BYTES)
    progress.preserve()
    return {"scope":"complete_physical_original_p44_replay_not_current_old_source_or_native_pass",
            "capsule_sha256":progress.CAPSULE_SHA,"complete_original_capsule_byte_exact_reexecution":True,
            "original_cli_result":EXPECTED_RESULT,"files":len(manifest),"bytes":sum(map(len,copied.values())),
            "source_sha256":manifest,"declared_original_changed_sources":{
                name:{"archive":progress.ARCHIVE+archive,"sha256":digest} for name,(archive,digest) in progress.CHANGED.items()},
            "only_four_declared_changed_files_use_raw_archives":all(actual==(progress.ARCHIVE+progress.CHANGED[name][0] if name in progress.CHANGED else name)
                                                                    for name,actual in origins.items()),
            "no_function_root_test_source_lock_or_expected_hash_override":True,"python_environment_ignored_no_bytecode":True,
            "installed_user_and_system_site_dependencies_enabled":True,"owned_scratch_cleaned":True,"native_session_started":False}


if __name__=="__main__":
    try:value=reproduce()
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"stored_provider_whole_original_replay_failed"}));raise SystemExit(2)
    print(json.dumps({"state":"pass","complete_original_capsule_reexecution":True,"capsule_sha256":value["capsule_sha256"],
                      "files":value["files"],"bytes":value["bytes"],"native_session_started":False}))
