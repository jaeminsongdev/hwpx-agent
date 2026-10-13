#!/usr/bin/env python3
"""Read-only complete PDF-pair render for six trace-valid r03 cases, not a Gate."""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import re
import sys
import tempfile
if not __package__:sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from PIL import Image, ImageChops, __version__ as PIL_VERSION
from tools.p08 import object_target_oracle as pdf
from tools.p09 import qualify_native_owned_exit_wait_admission as prior

ROOT=prior.ROOT
oracle=prior.old.sdk.oracle
CAPSULE="implementation/p09/evidence/p09-36-native-form-r03-six-pdf-stability.v1.json"
RENDERS="implementation/p09/evidence/private/p09-36-r03-six-pdf-stability-render.v1"
ADMISSION_SHA="d9d75f6fe4442ecbe702cd9d90fd5f0584b47de60825269bc6ed64325c1a4125"
SOURCES=("tools/p09/inspect_partial_native_form_pdf_stability.py",
         "tools/p08/object_target_oracle.py",prior.CAPSULE,
         "tools/p09/qualify_native_owned_exit_wait_admission.py",
         "tools/p09/qualify_native_form_diagnostic_batch.py",prior.binding.MANIFEST)
POPLER=Path(r"C:\Users\thdqu\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin")
INFO,PPM=POPLER/"pdfinfo.exe",POPLER/"pdftoppm.exe"

def require(value,code):prior.require(value,code)

def source_pins():
    return {name:prior.q.sha(prior.public.bounded_bytes(ROOT/name,2097152)) for name in SOURCES}

def measure(left,right):
    with Image.open(left) as ls,Image.open(right) as rs:
        a,b=ls.convert("RGB"),rs.convert("RGB")
        require(a.size==b.size and 100<=a.width<=4096 and 100<=a.height<=4096,"partial_pdf_dimensions_invalid")
        white=Image.new("RGB",a.size,"white")
        bounds=[ImageChops.difference(page,white).getbbox() for page in (a,b)]
        require(all(bound is not None for bound in bounds),"partial_pdf_blank_page_rejected")
        delta=ImageChops.difference(a,b)
        changed=sum(any(pixel) for pixel in delta.get_flattened_data())
        total=sum(sum(pixel) for pixel in delta.get_flattened_data())
        return {"width":a.width,"height":a.height,"changed_pixels":changed,
                "absolute_rgb_delta_sum":total,"difference_bbox":delta.getbbox(),
                "nonwhite_bboxes":bounds}

def inspect(persist=False):
    before=source_pins()
    admitted=json.loads(prior.public.checked(ROOT/prior.CAPSULE,ADMISSION_SHA,2097152),object_pairs_hook=prior.q.shared.lifecycle.duplicate_guard)
    prior.old.exact(prior.own_pins(),admitted["source_sha256"],"partial_pdf_admission_sources_changed")
    old=prior.prior_attempts()
    prior.old.exact(old,admitted["prior_partial_batch_preserved"],"partial_pdf_native_evidence_changed")
    manifest=prior.q.shared.lifecycle.checked_json(ROOT/prior.binding.MANIFEST,prior.binding.MANIFEST_SHA)
    tools={path.name:prior.q.sha(prior.public.bounded_bytes(path,67108864)) for path in (INFO,PPM)}
    base=ROOT/"fixtures/target-build";oracle.no_links(base)
    renders=ROOT/RENDERS
    if persist:
        oracle.no_links(renders.parent);require(not renders.exists(),"partial_pdf_render_directory_exists")
        renders.mkdir();context=nullcontext(str(renders))
    else:context=tempfile.TemporaryDirectory(prefix="p09-36-pdf-verify-",dir=base)
    cases=[];rasters={}
    with context as directory:
        directory=Path(directory);oracle.no_links(directory)
        for index,path in enumerate(prior.binding.attempt_paths("p09-35-20261003-r03")[:6]):
            row=manifest["cases"][index]
            trace=json.loads(prior.public.bounded_bytes(path/"target-trace.json",131072),object_pairs_hook=prior.q.shared.lifecycle.duplicate_guard)
            require(prior.binding.verify_case_trace(trace,row) is True,"partial_pdf_trace_binding_invalid")
            snapshot=prior.binding.artifact_snapshot(path,trace,True)
            counts=[pdf.pdf_page_count(INFO,path/name) for name in ("saved.pdf","reopened.pdf")]
            require(counts[0]==counts[1] and 1<=counts[0]<=4,"partial_pdf_page_inventory_changed")
            a=pdf.render_pdf(PPM,path/"saved.pdf",directory,f"c{index+1:02}-saved")
            b=pdf.render_pdf(PPM,path/"reopened.pdf",directory,f"c{index+1:02}-reopened")
            require(len(a)==len(b)==counts[0],"partial_pdf_render_inventory_invalid")
            pages=[measure(left,right) for left,right in zip(a,b,strict=True)]
            for image in (*a,*b):rasters[image.name]=prior.q.sha(prior.public.bounded_bytes(image,16777216))
            cases.append({"case_id":row["case_id"],"trace_sha256":prior.q.sha(prior.public.bounded_bytes(path/"target-trace.json",131072)),
                          "pdf_artifacts":{name:snapshot[name] for name in ("saved.pdf","reopened.pdf")},
                          "page_count":counts[0],"pages":pages,
                          "state":"equal" if all(page["changed_pixels"]==0 for page in pages) else "mismatch"})
        require(set(rasters)=={file.name for file in directory.iterdir()},"partial_pdf_derived_inventory_invalid")
    if not persist:require(not directory.exists(),"partial_pdf_verify_scratch_not_cleaned")
    require(source_pins()==before and prior.prior_attempts()==old,"partial_pdf_sources_changed")
    prior.old.exact(prior.own_pins(),admitted["source_sha256"],"partial_pdf_admission_sources_changed")
    require(tools=={path.name:prior.q.sha(prior.public.bounded_bytes(path,67108864)) for path in (INFO,PPM)},"partial_pdf_renderer_changed")
    return {"schema_version":"hwpx-agent.p09-native-partial-pdf-stability/v1",
            "state":"six_actual_r03_saved_reopened_pdf_observations_non_green",
            "source_sha256":before,"admission_sha256":ADMISSION_SHA,"prior_partial_batch_preserved":old,
            "renderer_sha256":tools,"pillow_version":PIL_VERSION,"dpi":96,"cases":cases,
            "derived_png_sha256":rasters,"masks_or_tolerances_used":False,
            "claims":{"scope":"six_trace_valid_old_r03_cases_only_not_current_r05_batch",
                      "all_relevant_pages_actually_rendered_and_compared":True,
                      "input_to_native_or_direct_automation_differential":False,"native_form_semantics_qualified":False,
                      "visual_acceptance_qualified":False,"new_native_session_started":False,
                      "green_rows":0,"p09_complete":False},
            "privacy":{"raw_document_text_present":False,"absolute_private_paths_present":False,
                       "source_pdf_modified_or_reexported":False,"computer_use_input_invoked":False}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output",type=Path);group.add_argument("--verify",type=Path);args=parser.parse_args()
    try:
        target=(args.output or args.verify).absolute()
        require(target==ROOT/CAPSULE and ".." not in (args.output or args.verify).parts,"partial_pdf_evidence_boundary")
        oracle.no_links(target.parent)
        if args.output:require(not target.exists(),"partial_pdf_receipt_exists")
        value=inspect(persist=bool(args.output));raw=prior.q.shared.lifecycle.canonical_bytes(value)
        if args.output:
            with target.open("xb") as stream:stream.write(raw)
        else:prior.prior.raw_equal(prior.public.bounded_bytes(target,2097152),raw)
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,pdf.OracleError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+",str(error)) else type(error).__name__
        print(json.dumps({"state":"fail","error_code":code,"native_semantics_qualified":False}));return 2
    print(json.dumps({"state":"pass","cases":6,"equal_pairs":sum(case["state"]=="equal" for case in value["cases"]),
                      "pages":sum(case["page_count"] for case in value["cases"]),"receipt_sha256":prior.q.sha(raw),
                      "native_semantics_qualified":False,"green_rows":0}));return 0

if __name__=="__main__":raise SystemExit(main())
