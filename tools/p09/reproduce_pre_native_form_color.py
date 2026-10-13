#!/usr/bin/env python3
"""Complete unchanged original P46 in its authentic pre-color physical source view."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.p09 import record_native_form_color_preparation as progress

ROOT=progress.ROOT
ORIGINAL="implementation/p09/evidence/p09-46-stored-product-request.source-qualified.v1.json"
ORIGINAL_SHA="2d4386dda7efe9a9d9e6ab5efaa301816756818a3cb49c71129408f7fdb398ac"
EXPECTED={"state":"pass","qualification_sha256":ORIGINAL_SHA,"capsule_bytes":233471,
          "source_pins":31,"actual_product_tests":8,"actual_python_source_guards":8,
          "whole_original_p45_reexecuted":True,"native_session_started":False,"green_rows":0}
LIMIT_FILES=1800
LIMIT_BYTES=64*1024*1024
MAX_SOURCE=16*1024*1024
DIAGNOSTIC_CODE=r'''
import sys,json,re,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from tools.p09 import qualify_stored_product_request as q
try:
    value=q.qualify();raw=q.prior.q.shared.lifecycle.canonical_bytes(value)
    original=q.public.checked(q.ROOT/q.CAPSULE,"2d4386dda7efe9a9d9e6ab5efaa301816756818a3cb49c71129408f7fdb398ac",2097152)
    print(json.dumps({"state":"pass" if raw==original else "fail","scope":"diagnostic_only_original_p46_body_not_cli_qualification",
        "original_capsule_byte_exact":raw==original,"actual_bytes":len(raw),"actual_sha256":q.oracle.sha(raw)}))
    raise SystemExit(0 if raw==original else 2)
except Exception as error:
    frames=[];nested=[];paths=[];node=error.__traceback__
    while node:
        frames.append(Path(node.tb_frame.f_code.co_filename).name+":"+str(node.tb_lineno))
        path=node.tb_frame.f_locals.get("path")
        if isinstance(path,Path):
            try:name=path.relative_to(q.ROOT).as_posix()
            except ValueError:name=""
            if name.startswith("crates/") and re.fullmatch(r"[a-zA-Z0-9_./-]+",name):paths.append(name)
        for process in tuple(node.tb_frame.f_locals.values()):
            if not isinstance(process,subprocess.CompletedProcess):continue
            codes=[]
            for raw in (process.stdout,process.stderr):
                if not isinstance(raw,bytes) or len(raw)>1048576:continue
                for line in raw.decode("utf-8",errors="replace").splitlines():
                    if re.fullmatch(r"ValueError: [a-z_]+",line):codes.append(line)
                    for code in re.findall(r"\b(?:LNK[0-9]{4}|E[0-9]{4})\b",line):codes.append(code)
                    try:result=json.loads(line)
                    except ValueError:continue
                    if isinstance(result,dict) and isinstance(result.get("error_code"),str) and re.fullmatch(r"[a-z_]+",result["error_code"]):codes.append(result["error_code"])
            nested.append({"exit_code":process.returncode,"codes":sorted(set(codes))})
        node=node.tb_next
    message=str(error)
    print(json.dumps({"state":"fail","scope":"diagnostic_only_original_p46_body_not_cli_qualification",
        "error_type":type(error).__name__,"error_code":message if re.fullmatch(r"[a-z_]+",message) else "redacted_nonconstant_error",
        "frames":frames,"rejected_source_inputs":paths,"nested_results":nested}))
    raise SystemExit(2)
'''

def require(value,code):progress.require(value,code)

def select():
    value=json.loads(progress.io.checked(ROOT/ORIGINAL,ORIGINAL_SHA),object_pairs_hook=progress.io.duplicate_guard)
    manifest=dict(value["complete_original_stored_provider_reproduction"]["source_sha256"])
    manifest.update(value["source_sha256"])
    manifest[ORIGINAL]=ORIGINAL_SHA
    require(len(manifest)==1534 and len(manifest)<=LIMIT_FILES,"color_original_source_inventory")
    origins={};copied={};total=0
    for name,digest in manifest.items():
        progress.original.history.relative(name)
        origin=progress.ARCHIVE+progress.CHANGED[name][0] if name in progress.CHANGED else name
        progress.original.history.relative(origin)
        raw=progress.original.public.checked(ROOT/origin,digest,MAX_SOURCE)
        require(name not in copied,"color_original_source_alias")
        copied[name]=raw;origins[name]=origin;total+=len(raw)
    require(total==50833903 and total<=LIMIT_BYTES,"color_original_source_bytes")
    # All ORIGINAL P46 direct pins supersede its pre-P46 predecessor graph entries.
    # Only the two explicitly archived package/product roots differ from live files.
    require({n for n,o in origins.items() if n!=o}==set(progress.CHANGED),"color_original_archive_origins")
    progress.preserve()
    return copied,manifest,origins

def boundary(directory,empty=False):
    require(directory.absolute()==directory and directory.parent==ROOT
            and re.fullmatch(r"q[0-9a-f]{4}",directory.name),"color_original_short_source_boundary")
    for item in (directory,*directory.parents):
        stat=item.lstat();require(not item.is_symlink() and not getattr(stat,"st_file_attributes",0)&0x400,"color_original_short_source_link")
    require(directory.is_dir() and directory.resolve().parent==ROOT.resolve(),"color_original_short_source_boundary")
    if empty:require(not any(directory.iterdir()),"color_original_short_source_not_empty")

def fresh_directory():
    # Five-character exclusive child adds only6 path characters, keeping unchanged
    # nested P46/P45/P44/P43/P42 linker paths short. Parent repository Git remains
    # discoverable for original readonly Git-blob checks; no Git environment override.
    for _ in range(64):
        directory=ROOT/("q"+secrets.token_hex(2))
        try:directory.mkdir()
        except FileExistsError:continue
        boundary(directory,True);return directory
    raise ValueError("color_original_short_source_collision")

def protocol(code,stdout,stderr):
    require(code==0 and not stderr.strip() and 0<len(stdout)<=65536,"color_original_cli_failed")
    result=json.loads(stdout,object_pairs_hook=progress.io.duplicate_guard)
    require(type(result) is dict and result.keys()==EXPECTED.keys()
            and all(type(result[k]) is type(v) and result[k]==v for k,v in EXPECTED.items()),"color_original_cli_protocol")
    return result

def original_command(diagnostic=False):
    # -E ignores Python environment injection without disabling already installed
    # user-site PIL required by unchanged original oracle imports. -I hid PIL.
    prefix=[sys.executable,"-E","-B","-X","utf8"]
    return prefix+(["-c",DIAGNOSTIC_CODE] if diagnostic else
                  ["tools/p09/qualify_stored_product_request.py","--verify",ORIGINAL])

def diagnostic_protocol(code,stdout,stderr):
    require(code in (0,2) and not stderr.strip() and 0<len(stdout)<=131072,"color_original_diagnostic_protocol")
    results=[]
    # The unchanged nested original helpers may print their own diagnostic JSON.
    # They are not a replacement success protocol; select exactly this diagnostic.
    for line in stdout.splitlines():
        try:value=json.loads(line,object_pairs_hook=progress.io.duplicate_guard)
        except ValueError:continue
        if type(value) is dict and value.get("scope")=="diagnostic_only_original_p46_body_not_cli_qualification":results.append(value)
    require(len(results)==1 and results[0].get("state")==("pass" if code==0 else "fail"),"color_original_diagnostic_scope")
    return results[0]

def reproduce(diagnostic=False):
    before=progress.pins();preserved=progress.preserve();copied,manifest,origins=select()
    directory=fresh_directory()
    try:
        for name,raw in copied.items():
            path=directory/name;path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("xb") as stream:stream.write(raw)
        # Original P46 guards validate an existing ROOT/target scratch parent.
        # It is an empty owned directory, not a source input or copied build cache.
        (directory/"target").mkdir(exist_ok=True)
        # Use the original bounded inventory, not a replacement acceptance filter.
        require(progress.original.history.inventory(directory,manifest)==manifest,"color_original_copy_identity")
        environment=dict(os.environ)
        environment["CARGO_TARGET_DIR"]=str(ROOT/"target/p09-48-pre-color-view")
        # The ORIGINAL script resolves ROOT from its own physical location.
        # No function/source/test/lock/hash/timeout substitution or monkey-patch.
        actual=subprocess.run(original_command(diagnostic),
                              cwd=directory,env=environment,capture_output=True,check=False)
        if diagnostic:
            result=diagnostic_protocol(actual.returncode,actual.stdout,actual.stderr)
        else:result=protocol(actual.returncode,actual.stdout,actual.stderr)
        require(progress.original.history.inventory(directory,manifest)==manifest,"color_original_source_copy_changed")
        boundary(directory)
    finally:
        # Delete only this actually created, exact validated disposable source view.
        # Source files/fixtures/receipts and external main target cache remain intact.
        boundary(directory)
        shutil.rmtree(directory)
        for name,digest in manifest.items():progress.original.public.checked(ROOT/origins[name],digest,MAX_SOURCE)
        require(progress.pins()==before and progress.preserve()==preserved,"color_original_source_changed")
    if diagnostic:return result
    return {"state":"complete_original_p46_cli_byte_exact_reexecution",
            "original_capsule_sha256":ORIGINAL_SHA,"original_capsule_bytes":233471,
            "files":len(manifest),"bytes":sum(map(len,copied.values())),"source_sha256":manifest,
            "declared_original_changed_sources":{n:{"archive":origins[n],"sha256":manifest[n]} for n in progress.CHANGED},
            "original_cli_result":result,"whole_original_p46_and_nested_p45_p44_p43_p42_reexecuted":True,
            "no_function_root_test_source_lock_hash_or_timeout_override":True,
            "source_view_layout":{"repository_direct_child_name_pattern":"q[0-9a-f]{4}","added_path_characters":6,
                                  "original_parent_git_blob_checks_unmodified":True,"child_git_environment_overridden":False},
            "owned_short_source_view_removed":True,"native_session_started":False,"p09_complete":False}

def main():
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group()
    mode.add_argument("--run",action="store_true");mode.add_argument("--diagnose",action="store_true");args=parser.parse_args()
    try:
        if args.diagnose:
            value=reproduce(True);print(json.dumps(value));return 0 if value["state"]=="pass" else 2
        if args.run:
            value=reproduce()
            print(json.dumps({"state":"pass","scope":"complete_original_p46_reexecution_not_new_color_full_source_qualification",
                "files":value["files"],"bytes":value["bytes"],"original_capsule_sha256":ORIGINAL_SHA,
                "original_capsule_bytes":233471,"whole_original_p46_reexecuted":True,"native_session_started":False}));return 0
        copied,_,_=select()
        print(json.dumps({"state":"pass","scope":"raw_origin_preflight_only_not_original_reexecution",
                          "files":len(copied),"bytes":sum(map(len,copied.values())),"original_capsule_sha256":ORIGINAL_SHA}));return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch("[a-z_]+",str(error)) else type(error).__name__
        print(json.dumps({"state":"fail","error_code":code}));return 2

if __name__=="__main__":raise SystemExit(main())
