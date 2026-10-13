#!/usr/bin/env python3
"""Complete unchanged original P09-45 CLI/capsule in its authentic source view."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import record_stored_product_request_progress as progress

ROOT=progress.ROOT
old,oracle,public=progress.old,progress.oracle,progress.public
LIMIT_FILES,LIMIT_BYTES,SOURCE_BYTES=1800,64*1024*1024,16*1024*1024
SCRATCH_PARENT,SCRATCH_PREFIX="target","p46-"
EXPECTED_RESULT={"state":"pass","qualification_sha256":progress.CAPSULE_SHA,"capsule_bytes":223976,
                 "source_pins":17,"actual_product_tests":8,"actual_python_source_guards":8,
                 "whole_original_p44_reexecuted":True,"native_session_started":False,"green_rows":0}
relative=old.history.relative
# The original P45 graph omitted compile-time artifact-service migrations.
# These raw inputs are unchanged Git blobs at the recorded repository revision;
# they supplement the physical build view, never rewrite the original capsule.
MIGRATION_GIT_REVISION="1f8cd23da15d2e517e0e5640eae2bffe2c19af3f"
MIGRATIONS={
 "migrations/postgres/0001_p14_metadata.up.sql":"7c00f744993581448acb4b6d4d8a46f1ff03d108750da0afc671c3b5e2b0a78d",
 "migrations/postgres/0002_p14_artifact_service.up.sql":"202753fbd6f20f181b09bd6227766dfb808811bd4e734a4a418cb5bae4eaee56",
 "migrations/postgres/0003_p14_revision_cas.up.sql":"beeac1f22fde0eb3474d40acc14838c1e9676a74b68c5b6f9608713ba6e6e53a",
 "migrations/postgres/0004_p14_history_checkpoints.up.sql":"e336890d4ee3fdf4819f52c079ba320f450b01ec516bf5ffaaf505a76b14f249",
 "migrations/postgres/0005_p14_job_state_machine.up.sql":"4f15cd28510d55fa58a18aef7b8edf8b4606169fd722a0b8d2c63da2cfb4bf9b",
 "migrations/postgres/0006_p14_worker_lease_fencing.up.sql":"03af7cc8b2ae883ff132e3b1737b29c3829fcb0fa9887566485f865b3c0393ab",
 "migrations/postgres/0007_p14_idempotency_reconciliation.up.sql":"cc60353df6cf3c51155417e39d0f1f4c348d2a6282bba7d63de9ea0282be5e5d",
 "migrations/postgres/0008_p14_cancel_cleanup.up.sql":"2ba28c1386db9c5aeb4661d11069e48f8624c2560b69301a0750ab9344c46f29",
 "migrations/postgres/0009_p14_retention_local_mirror.up.sql":"272da51d665be7b9c0b5150a641ca1f9f51b9b78cddb839096acb57eb71e9ec2",
 "migrations/postgres/0010_p16_artifact_repository.up.sql":"3d1ce21be0cb100bbc098e798b1917e52c4767da9a832359578179d9b0522420",
 "migrations/postgres/0011_p16_plan_source.up.sql":"3aa21685e7511322414265b076f1ed43ff6b7e39c4dd1ee695e121a161777bbc",
 "migrations/postgres/0012_p16_durable_plan_store.up.sql":"d85b1b4bbfbf8f63d85ae1088ae676d5c70bf926d6eb3c1cdb070a4b297d6cc0",
 "migrations/postgres/0013_p16_plan_review_evidence.up.sql":"16c818ddb5aac58b168174cb39067c2d941e572d883fef3be9b5c452a5b6c923",
 "migrations/postgres/0014_p17_history_checkpoint_note.up.sql":"d3e8a2846780f9442ea4b3acf55c072a2ba663590e3b24c9e46736517bb4c129",
 "migrations/postgres/0015_p17_atomic_mirror_checkpoint.up.sql":"ff513cf4eed8b9498241e5b111646f1a4b58e7e373e4126b75d9ad317c69b25a",
 "migrations/postgres/0016_p17_durable_git_mirror_push.up.sql":"a928dab01d36399a9ce5f24800f689ffcb585abb1da7bdcdf228d8cedafb7263",
 "migrations/postgres/0017_p17_durable_git_mirror_pull.up.sql":"2880461cc22be5cbcc0df3802f3996ad8a0ee9ad6a2509d5798e040bdbeea1f4",
}

def select():
    preserved=progress.preserve()
    capsule=json.loads(public.checked(ROOT/old.CAPSULE,progress.CAPSULE_SHA,2*1024*1024),object_pairs_hook=oracle.duplicate_guard)
    replay=capsule["complete_original_product_request_reproduction"]
    graph=replay["source_sha256"];current=capsule["source_sha256"];declared=replay["declared_original_changed_sources"]
    oracle.require(len(graph)==1490 and set(current)==set(old.SOURCES),"stored_request_view_original_inventory")
    # Source pins override prior graph entries: actual original P45 Cargo/lock/getters/root,
    # not their PRE-provider archives. Their archived pre-provider files are also original inputs.
    oracle.require(not set(MIGRATIONS).intersection(graph) and len(MIGRATIONS)==17,"stored_request_migration_inventory")
    for name,digest in MIGRATIONS.items():
        raw=public.checked(ROOT/name,digest,SOURCE_BYTES)
        blob=subprocess.run(["git","show",MIGRATION_GIT_REVISION+":"+name],cwd=ROOT,capture_output=True,timeout=15)
        oracle.require(blob.returncode==0 and blob.stdout==raw and not blob.stderr,"stored_request_migration_git_identity")
    manifest={**graph,**current,old.CAPSULE:progress.CAPSULE_SHA,**MIGRATIONS}
    origins={name:progress.ARCHIVE+progress.CHANGED[name][0] if name in progress.CHANGED
             else name if name in current else declared[name]["archive"] if name in declared else name
             for name in manifest}
    oracle.require(len(manifest)<=LIMIT_FILES and not any("p09-46" in name or "form_product_request/stored.rs" in name
                                                       or "form_stored_product_request.rs" in name for name in manifest),"stored_request_view_inventory")
    oracle.require(len({str(relative(name)).casefold() for name in manifest})==len(manifest),"stored_request_view_path_alias")
    copied={};total=0
    for name,digest in sorted(manifest.items()):
        relative(name);relative(origins[name]);value=public.checked(ROOT/origins[name],digest,SOURCE_BYTES);total+=len(value)
        oracle.require(total<=LIMIT_BYTES,"stored_request_view_source_bytes");copied[name]=value
    oracle.require(progress.preserve()==preserved,"stored_request_view_origins_changed")
    return copied,manifest,origins

def inventory(directory,manifest):
    return {name:oracle.sha(public.bounded_bytes(directory/relative(name),SOURCE_BYTES)) for name in manifest}

def validate_result(code,stdout,stderr):
    oracle.require(len(stdout)<=128*1024 and len(stderr)<=1024*1024,"stored_request_view_process_limit")
    value=json.loads(stdout.decode("utf-8",errors="strict"),object_pairs_hook=oracle.duplicate_guard)
    canonical=old.old.original.old.prior.q.shared.lifecycle.canonical_bytes
    oracle.require(code==0 and canonical(value)==canonical(EXPECTED_RESULT),"stored_request_view_complete_original_replay_failed")

P44_DIAGNOSTIC=r'''
from tools.p09 import reproduce_product_request_pre_stored_provider as r
from pathlib import Path
import json,re,subprocess
try:
    result=r.reproduce()
except Exception as error:
    frames=[];nested=[];node=error.__traceback__
    while node:
        frames.append(Path(node.tb_frame.f_code.co_filename).name+":"+str(node.tb_lineno))
        for key in ("process","diagnostic"):
            process=node.tb_frame.f_locals.get(key)
            if not isinstance(process,subprocess.CompletedProcess):continue
            if len(process.stdout)>131072 or len(process.stderr)>1048576:continue
            codes=[];subframes=[]
            for line in process.stdout.decode("utf-8",errors="replace").splitlines():
                try:value=json.loads(line)
                except (ValueError,TypeError):continue
                if not isinstance(value,dict):continue
                code=value.get("error_code")
                if isinstance(code,str) and re.fullmatch(r"[a-z][a-z0-9_]{1,100}",code):codes.append(code)
                for code in value.get("diagnostic_codes",[]) if isinstance(value.get("diagnostic_codes"),list) else []:
                    if isinstance(code,str) and re.fullmatch(r"ValueError: [a-z][a-z0-9_]{1,100}",code):codes.append(code)
                for frame in value.get("diagnostic_frames",[]) if isinstance(value.get("diagnostic_frames"),list) else []:
                    if isinstance(frame,str) and re.fullmatch(r"[a-z0-9_.<>-]+:[0-9]+",frame):subframes.append(frame)
            for line in process.stderr.decode("utf-8",errors="replace").splitlines():
                if re.fullmatch(r"ValueError: [a-z][a-z0-9_]{1,100}",line):codes.append(line)
            nested.append({"exit_code":process.returncode,"codes":codes,"frames":subframes})
        node=node.tb_next
    print(json.dumps({"state":"fail","scope":"diagnostic_only_original_p44_not_p45_qualification",
                      "error_type":type(error).__name__,"frames":frames,"nested_results":nested}))
    raise SystemExit(2)
print(json.dumps({"state":"pass","scope":"diagnostic_only_original_p44_not_p45_qualification",
                  "original_capsule_sha256":result["capsule_sha256"]}))
'''

P42_DIAGNOSTIC=r'''
from tools.p09 import qualify_product_form_value_preparation as q
from pathlib import Path
import json,re,os
scope="diagnostic_only_original_p42_not_p45_qualification"
try:
    original=q.public.checked(q.ROOT/q.CAPSULE,"c86a2d44b933cb34ac5462ddec77e8bdec94f800485040c73178fe567a1fbc48",2*1024*1024)
    value=q.qualify();raw=q.prior.q.shared.lifecycle.canonical_bytes(value)
    expected=json.loads(original,object_pairs_hook=q.oracle.duplicate_guard)
    differences=[]
    def compare(a,b,path=""):
        if type(a) is not type(b):differences.append(path+":type");return
        if isinstance(a,dict):
            if a.keys()!=b.keys():differences.append(path+":keys")
            for key in sorted(a.keys() & b.keys()):compare(a[key],b[key],path+"/"+key)
        elif isinstance(a,list):
            if len(a)!=len(b):differences.append(path+":length")
            for index,(left,right) in enumerate(zip(a,b)):compare(left,right,path+"/"+str(index))
        elif a!=b:differences.append(path)
    compare(expected,value)
    safe=[path for path in differences if re.fullmatch(r"[a-zA-Z0-9_./\\:-]{1,240}",path)]
    print(json.dumps({"state":"pass" if raw==original else "fail","scope":scope,
        "original_capsule_byte_exact":raw==original,"actual_bytes":len(raw),
        "actual_sha256":q.oracle.sha(raw),"difference_count":len(differences),
        "difference_paths":safe[:20],"native_session_started":False}))
except Exception as error:
    frames=[];compiler=[];node=error.__traceback__
    while node:
        frames.append(Path(node.tb_frame.f_code.co_filename).name+":"+str(node.tb_lineno))
        stderr=node.tb_frame.f_locals.get("_")
        if isinstance(stderr,bytes) and len(stderr)<=2097152:
            text=stderr.decode("utf-8",errors="replace")
            linker_paths=re.findall(r"LNK1104:\s*(?:cannot open file\s*)?['\"]([^'\"\r\n]+)['\"]",text)
            compiler.append({"cargo_exit_code":node.tb_frame.f_locals.get("code") if type(node.tb_frame.f_locals.get("code")) is int else None,
                             "rust_error_codes":re.findall(r"(?m)^error\[([A-Z][0-9]+)\]",text),
                             "linker_error_codes":sorted(set(re.findall(r"\bLNK[0-9]{4}\b",text))),
                             "os_error_codes":sorted(set(re.findall(r"\bos error ([0-9]{1,5})\b",text))),
                             "process_status_codes":sorted(set(re.findall(r"(?:exit code|exit status):? (0x[0-9a-fA-F]+|[0-9-]{1,12})",text))),
                             "error_heading_prefixes":re.findall(r"(?m)^error: ([a-z][a-z ]{1,64})",text),
                             "linker_file_metadata":[{"basename":Path(path).name,"path_chars":len(path),
                                                       "suffix":Path(path).suffix,"parent_exists":Path(path).parent.exists()}
                                                      for path in linker_paths],
                             "windows_path_length_error_206":bool(re.search(r"(?:os error|오류) 206|filename or extension is too long",text,re.I)),
                             "locations":[Path(match.group(1)).name+":"+match.group(2)+":"+match.group(3)
                                          for match in re.finditer(r"--> ([^\r\n]+?):(\d+):(\d+)",text)]})
        node=node.tb_next
    code=str(error) if isinstance(error,ValueError) and re.fullmatch(r"[a-z][a-z0-9_]{1,100}",str(error)) else None
    short_probe=None
    target=os.environ.get("P09_46_DIAGNOSTIC_SHORT_TARGET")
    if target and code=="product_preparation_compiled_integration_failed" and any("LNK1104" in row["linker_error_codes"] for row in compiler):
        os.environ["CARGO_TARGET_DIR"]=target
        try:
            value=q.qualify();raw=q.prior.q.shared.lifecycle.canonical_bytes(value)
            short_probe={"state":"pass" if raw==original else "fail","capsule_byte_exact":raw==original,
                         "actual_bytes":len(raw),"actual_sha256":q.oracle.sha(raw)}
        except Exception as probe_error:
            short_probe={"state":"fail","error_type":type(probe_error).__name__}
    print(json.dumps({"state":"fail","scope":scope,"error_type":type(error).__name__,
                      "error_code":code,"frames":frames,"compiler_diagnostics":compiler,
                      "short_build_target_diagnostic_only":short_probe,"native_session_started":False}))
    raise SystemExit(2)
'''

def diagnostic_layer_code(module,child):
    oracle.require(module in {"reproduce_product_request_pre_stored_provider",
                             "reproduce_form_operation_pre_request",
                             "reproduce_form_preparation_pre_operation"},"stored_request_diagnostic_layer_invalid")
    # Each child imports the unchanged selector from its own authentic physical
    # view. No module ROOT/function/source/expected-output override is applied.
    return '''
import importlib,json,os,subprocess,sys,tempfile,re
from pathlib import Path
r=importlib.import_module("tools.p09."+%r)
relative=r.old.prior.history.relative if %r=="reproduce_form_preparation_pre_operation" else r.relative
scope="diagnostic_only_original_p42_not_p45_qualification"
try:
    copied,manifest,origins=r.select();base=r.ROOT/"fixtures/target-build";r.oracle.no_links(base)
    with tempfile.TemporaryDirectory(prefix=%r,dir=base) as temporary:
        directory=Path(temporary);r.oracle.no_links(directory)
        r.oracle.require(directory.resolve().parent==base.resolve() and not any(directory.iterdir()),"stored_request_diagnostic_layer_boundary")
        for name,value in copied.items():
            path=directory/relative(name);path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("xb") as stream:stream.write(value)
        r.oracle.require(r.inventory(directory,manifest)==manifest,"stored_request_diagnostic_layer_copy_identity")
        environment=dict(os.environ)
        environment["CARGO_TARGET_DIR"]=str(r.ROOT/"target"/%r)
        process=subprocess.run([sys.executable,"-E","-B","-c",%r],cwd=directory,env=environment,
                               capture_output=True,timeout=1500,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
        r.oracle.require(len(process.stdout)<=131072 and len(process.stderr)<=1048576,"stored_request_diagnostic_layer_output_limit")
        rows=[]
        for line in process.stdout.decode("utf-8",errors="strict").splitlines():
            try:value=json.loads(line,object_pairs_hook=r.oracle.duplicate_guard)
            except ValueError:continue
            if type(value) is dict and value.get("scope")==scope:rows.append(value)
        r.oracle.require(len(rows)==1,"stored_request_diagnostic_layer_result_missing")
        r.oracle.require(r.inventory(directory,manifest)==manifest,"stored_request_diagnostic_layer_sources_changed")
    for name,digest in manifest.items():r.public.checked(r.ROOT/origins[name],digest,16*1024*1024)
    r.oracle.require(not Path(temporary).exists(),"stored_request_diagnostic_layer_scratch_not_cleaned")
    print(json.dumps(rows[0]));raise SystemExit(process.returncode)
except Exception as error:
    frames=[];node=error.__traceback__
    while node:
        frames.append(Path(node.tb_frame.f_code.co_filename).name+":"+str(node.tb_lineno));node=node.tb_next
    code=str(error) if isinstance(error,ValueError) and re.fullmatch(r"[a-z][a-z0-9_]{1,100}",str(error)) else None
    print(json.dumps({"state":"fail","scope":scope,"error_type":type(error).__name__,
                      "error_code":code,"frames":frames,"native_session_started":False}))
    raise SystemExit(2)
''' % (module,module,{"reproduce_product_request_pre_stored_provider":"p09-45-source-view-",
                       "reproduce_form_operation_pre_request":"p09-44-source-view-",
                       "reproduce_form_preparation_pre_operation":"p09-43-source-view-"}[module],
                       {"reproduce_product_request_pre_stored_provider":"p09-45-pre-provider-view",
                       "reproduce_form_operation_pre_request":"p09-44-pre-request-view",
                       "reproduce_form_preparation_pre_operation":"p09-43-pre-operation-view"}[module],child)

def diagnose_p44(code=P44_DIAGNOSTIC,scope="diagnostic_only_original_p44_not_p45_qualification"):
    copied,manifest,origins=select();base=ROOT/"fixtures/target-build";oracle.no_links(base)
    with tempfile.TemporaryDirectory(prefix="p09-46-source-view-",dir=base) as temporary:
        directory=Path(temporary);oracle.no_links(directory)
        oracle.require(directory.resolve().parent==base.resolve() and not any(directory.iterdir()),"stored_request_diagnostic_scratch_boundary")
        for name,value in copied.items():
            target=directory/relative(name);target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as stream:stream.write(value)
        oracle.require(inventory(directory,manifest)==manifest,"stored_request_diagnostic_copy_identity")
        environment=dict(os.environ)
        for key in ("PYTHONPATH","PYTHONHOME","PYTHONSTARTUP",old.old.original.old.prior.old.ENVIRONMENT):environment.pop(key,None)
        environment["PYTHONDONTWRITEBYTECODE"]="1"
        environment["CARGO_TARGET_DIR"]=str(ROOT/"target/p09-46-pre-stored-request-view")
        environment["P09_46_DIAGNOSTIC_SHORT_TARGET"]=str(ROOT/"target/p09-46-short-link-diagnostic")
        process=subprocess.run([sys.executable,"-E","-B","-c",code],cwd=directory,env=environment,
                               capture_output=True,timeout=1800,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
        oracle.require(len(process.stdout)<=131072 and len(process.stderr)<=1048576,"stored_request_diagnostic_output_limit")
        # Frozen reproducers print their own diagnostic JSON before our scoped result.
        # This extraction is diagnostic-only; default full CLI protocol stays strict.
        scoped=[]
        for line in process.stdout.decode("utf-8",errors="strict").splitlines():
            try:candidate=json.loads(line,object_pairs_hook=oracle.duplicate_guard)
            except ValueError:continue
            if type(candidate) is dict and candidate.get("scope")==scope:scoped.append(candidate)
        oracle.require(len(scoped)==1,"stored_request_diagnostic_scope_invalid");value=scoped[0]
        oracle.require(type(value) is dict and value.get("scope")==scope,
                       "stored_request_diagnostic_scope_invalid")
        oracle.require(inventory(directory,manifest)==manifest,"stored_request_diagnostic_sources_changed")
    for name,digest in manifest.items():public.checked(ROOT/origins[name],digest,SOURCE_BYTES)
    oracle.require(not Path(temporary).exists(),"stored_request_diagnostic_scratch_not_cleaned")
    progress.preserve();print(json.dumps(value));return process.returncode

def scratch_parent():
    base=ROOT/SCRATCH_PARENT;oracle.no_links(base)
    oracle.require(base.is_dir() and base.resolve().parent==ROOT.resolve(),"stored_request_short_scratch_parent")
    return base

def scratch_boundary(directory,base):
    oracle.require(base==ROOT/SCRATCH_PARENT and re.fullmatch(r"p46-[a-z0-9_]{8}",directory.name),"stored_request_view_scratch_boundary")
    oracle.no_links(directory)
    oracle.require(directory.is_dir() and directory.resolve().parent==base.resolve()
                   and not any(directory.iterdir()),"stored_request_view_scratch_boundary")
    return True

def reproduce():
    copied,manifest,origins=select();base=scratch_parent()
    # Only the NEW outer physical view is shorter. All frozen nested scripts,
    # roots relative to their physical files, target paths and timeouts stay exact.
    with tempfile.TemporaryDirectory(prefix=SCRATCH_PREFIX,dir=base) as temporary:
        directory=Path(temporary);oracle.no_links(directory)
        scratch_boundary(directory,base)
        for name,value in copied.items():
            target=directory/relative(name);target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as stream:stream.write(value)
        oracle.require(inventory(directory,manifest)==manifest,"stored_request_view_copy_identity")
        environment=dict(os.environ)
        for key in ("PYTHONPATH","PYTHONHOME","PYTHONSTARTUP",old.old.original.old.prior.old.ENVIRONMENT):environment.pop(key,None)
        environment["PYTHONDONTWRITEBYTECODE"]="1"
        environment["CARGO_TARGET_DIR"]=str(ROOT/"target/p09-46-pre-stored-request-view")
        command=[sys.executable,"-E","-B",str(directory/"tools/p09/qualify_stored_form_provider.py"),"--verify",str(directory/old.CAPSULE)]
        process=subprocess.run(command,cwd=directory,env=environment,capture_output=True,timeout=1800,
                               creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
        if process.returncode:
            diagnostic=subprocess.run([sys.executable,"-E","-B","-c","from tools.p09 import qualify_stored_form_provider as q; q.qualify()"],
                                      cwd=directory,env=environment,capture_output=True,timeout=1800,
                                      creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
            oracle.require(len(diagnostic.stdout)<=128*1024 and len(diagnostic.stderr)<=1024*1024,"stored_request_view_diagnostic_limit")
            lines=diagnostic.stderr.decode("utf-8",errors="replace").splitlines()
            print(json.dumps({"diagnostic_codes":[line for line in lines if re.fullmatch(r"ValueError: [a-z0-9_:.\-/]+",line)],
                              "diagnostic_frames":[Path(match.group(1)).name+":"+match.group(2) for line in lines
                                  if (match:=re.fullmatch(r'  File "([^\"]+)", line (\d+), in .+',line))]}))
            if "ValueError: stored_provider_actual_tests_failed" in lines:
                rust=subprocess.run(["cargo","test","--locked","--offline","-p","hwpx-agent-cli","--test","form_stored_provider"],
                                    cwd=directory,env=environment,capture_output=True,timeout=180,
                                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
                oracle.require(len(rust.stdout)<=256*1024 and len(rust.stderr)<=2*1024*1024,"stored_request_view_rust_diagnostic_limit")
                stderr=rust.stderr.decode("utf-8",errors="replace");stdout=rust.stdout.decode("utf-8",errors="replace")
                print(json.dumps({"original_rust_exit_code":rust.returncode,
                                  "original_rust_error_codes":re.findall(r"(?m)^error\[([A-Z][0-9]+)\]",stderr),
                                  "original_rust_failed_tests":re.findall(r"(?m)^test ([a-z0-9_:]+) \.\.\. FAILED$",stdout),
                                  "original_rust_locations":[Path(m.group(1)).name+":"+m.group(2)+":"+m.group(3)
                                      for m in re.finditer(r"(?:--> |panicked at )([^\r\n]+?):(\d+):(\d+)",stderr)],
                                  "original_rust_missing_target":bool(re.search(r"error: no test target named",stderr))}))
        validate_result(process.returncode,process.stdout,process.stderr)
        oracle.require(inventory(directory,manifest)==manifest,"stored_request_view_sources_changed")
    oracle.require(not Path(temporary).exists(),"stored_request_view_scratch_not_cleaned")
    for name,digest in manifest.items():public.checked(ROOT/origins[name],digest,SOURCE_BYTES)
    progress.preserve()
    return {"scope":"complete_physical_original_p45_replay_not_current_old_source_product_or_native_pass",
            "capsule_sha256":progress.CAPSULE_SHA,"complete_original_capsule_byte_exact_reexecution":True,
            "original_cli_result":EXPECTED_RESULT,"files":len(manifest),"bytes":sum(map(len,copied.values())),
            "source_sha256":manifest,"declared_original_changed_sources":{
                name:{"archive":progress.ARCHIVE+archive,"sha256":digest} for name,(archive,digest) in progress.CHANGED.items()},
            "original_graph_compile_time_inventory_gap":{"files":17,"bytes":517795,"git_revision":MIGRATION_GIT_REVISION,
                "source_sha256":MIGRATIONS,"unchanged_raw_git_blobs":True,"original_capsule_unchanged":True},
            "only_two_declared_changed_modules_use_new_raw_archives":all(actual==(progress.ARCHIVE+progress.CHANGED[name][0]
                  if name in progress.CHANGED else name) for name,actual in origins.items()),
            "original_post_provider_source_pins_override_pre_provider_graph_identity":True,
            "owned_outer_source_view_layout":"repository_target_p46_short_prefix_original_nested_scripts_unchanged",
            "no_function_root_test_source_lock_or_expected_hash_override":True,"python_environment_ignored_no_bytecode":True,
            "installed_user_and_system_site_dependencies_enabled":True,"owned_scratch_cleaned":True,"native_session_started":False}

if __name__=="__main__":
    if sys.argv[1:]==["--diagnose-original-p44"]:
        raise SystemExit(diagnose_p44())
    if sys.argv[1:]==["--diagnose-original-p42"]:
        code=P42_DIAGNOSTIC
        for module in ("reproduce_form_preparation_pre_operation","reproduce_form_operation_pre_request",
                       "reproduce_product_request_pre_stored_provider"):
            code=diagnostic_layer_code(module,code)
        raise SystemExit(diagnose_p44(code,"diagnostic_only_original_p42_not_p45_qualification"))
    oracle.require(not sys.argv[1:],"stored_request_replay_arguments_invalid")
    try:value=reproduce()
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError):
        print(json.dumps({"state":"fail","error_code":"stored_request_whole_original_replay_failed"}));raise SystemExit(2)
    print(json.dumps({"state":"pass","complete_original_capsule_reexecution":True,"capsule_sha256":value["capsule_sha256"],
                      "files":value["files"],"bytes":value["bytes"],"native_session_started":False}))
