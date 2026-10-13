"""TEST-ONLY original signed16 stage elapsed observation; original owned limits.

Original assertion/product text is exact after removing ONLY declared cfg(test)
instrumentation. Partial observations are never signed/full249/runtime/Gate PASS.
"""
import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import run_stored_signed_continuation as original
from audit_evidence_io import AuditEvidenceReader
from sql_owned_execution import scoped_path

maintenance, bounded, parent = original.maintenance, original.bounded, original.parent
SELF = "tools/p09/run_signed_stage_cost.py"
TEST = "tools/p09/tests/test_signed_stage_cost.py"
ROOT = "crates/product-cli/tests/form_stored_provider/actual_import/formula_policy_issuer/corpus/"
SOURCE, CONSUMER, NEW = ROOT+"changed.rs", ROOT+"changed/consumer.rs", ROOT+"changed/cost_profile.rs"
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-signed-stage-cost-r11/source-preimages.v1.json"
CANDIDATE = "implementation/p09/evidence/p09-149-signed-stage-cost-candidate.run01.v1.json"
INVENTORY, PROFILE = "stored-signed-cost-inventory", "stored-signed-cost-tests"
OUTER = ("original_expected", "numeric_derivative", "expected_candidate", "outside_compare", "signed_pair")
PAIR = ("changed_setup", "changed_register", "changed_prepare", "changed_consume", "changed_route_denied",
    "current_expected", "current_setup", "current_register", "current_prepare", "current_consume", "rebind_denied", "live_revocation_denied")
ORDER = (*OUTER[:-1], *PAIR, OUTER[-1])
MODULE = '#[cfg(test)]\n#[path = "changed/cost_profile.rs"]\nmod cost_profile;\n'
INITIAL = {SOURCE:("let mut timer = cost_profile::Timer::new(index);", "let _cost_scope = cost_profile::Scope::enter(index);"),
    CONSUMER:("let mut timer = super::cost_profile::Timer::current();",)}


def require_duration(task, seconds):
    maintenance.require(task in (INVENTORY,PROFILE) and type(seconds) is int
        and 30 <= seconds <= 180, "SIGNED_COST_FINITE_SCOPE")


def body_view(source, name):
    text = source.replace("\r\n","\n").replace("\r","\n")
    maintenance.require(name in INITIAL,"SIGNED_COST_BODY_SCOPE")
    if name == SOURCE:
        maintenance.require(text.count(MODULE)==1,"SIGNED_COST_PRIVATE_MODULE_REQUIRED")
        text=text.replace(MODULE,"",1)
    indent="        " if name==SOURCE else "    "
    stages=OUTER if name==SOURCE else PAIR
    for statement in (*INITIAL[name], *(f'timer.record("{stage}");' for stage in stages)):
        gated=indent+'#[cfg(test)]\n'+indent+statement+'\n'
        maintenance.require(text.count(gated)==1,"SIGNED_COST_EXACT_CFG_STATEMENT_REQUIRED")
        text=text.replace(gated,"",1)
    return text


def declared_sources(candidate, archive, expected, reader):
    maintenance.require(candidate.get("schema_version")=="hwpx-agent.p09-test-only-signed-stage-cost-candidate/v1"
        and candidate.get("qualification")=="TEST_SOURCE_CANDIDATE_ONLY_NOT_COMPILED_RUNTIME_SQL_OR_GATE"
        and candidate.get("parent_candidate_pin")==original.PARENT_PIN
        and candidate.get("preimage_archive")==ARCHIVE and candidate.get("added_sources")==[NEW],"SIGNED_COST_CANDIDATE_SCOPE")
    deltas=parent.contract.inputs.inventory(candidate["source_deltas"])
    maintenance.require(set(deltas)=={SOURCE,CONSUMER,NEW} and NEW not in expected
        and all(deltas[name]!=expected[name] for name in (SOURCE,CONSUMER)),"SIGNED_COST_EXACT_DELTA_SCOPE")
    maintenance.require(archive.get("schema_version")=="hwpx-agent.p09-test-only-signed-cost-preimages/v1"
        and archive.get("parent_candidate_pin")==original.PARENT_PIN and len(archive.get("files",[]))==2,"SIGNED_COST_WHOLE_ARCHIVE_SCOPE")
    seen=set()
    for item in archive["files"]:
        name=item["path"]; data=base64.b64decode(item["base64"],validate=True)
        maintenance.require(name in (SOURCE,CONSUMER) and name not in seen
            and len(data)==item["bytes"] and hashlib.sha256(data).hexdigest()==item["sha256"]
            and {key:item[key] for key in ("path","bytes","sha256")}==expected[name],"SIGNED_COST_WHOLE_PREIMAGE_DRIFT")
        maintenance.require(reader.pin(name)==deltas[name] and body_view(reader.text(name),name)==data.decode("utf-8").replace("\r\n","\n").replace("\r","\n"),"SIGNED_COST_ORIGINAL_ASSERTION_BODY_CHANGED")
        seen.add(name)
    maintenance.require(seen=={SOURCE,CONSUMER} and reader.pin(NEW)==deltas[NEW],"SIGNED_COST_COMPLETE_SOURCE_BINDING")
    return {**expected,**deltas}


def load_binding(windows, task, inventory_run):
    require_duration(task,180)
    # Original lineage read uses an UNCHANGED target. It does not pretend that
    # archived signed test bytes are the live bytes or current compiled proof.
    expected,_,_=original.previous.load_binding(windows,"import-formula-output-tests")
    hot=0
    def checkpoint():
        nonlocal hot
        hot,reason=maintenance.decision(parent.observed_sample(windows),hot)
        maintenance.require(reason is None,reason)
    reader=AuditEvidenceReader(maintenance.ROOT,checkpoint)
    maintenance.require(reader.pin(original.previous.CANDIDATE)==original.PARENT_PIN,"SIGNED_COST_PARENT_PIN_DRIFT")
    expected=declared_sources(reader.json(CANDIDATE),reader.json(ARCHIVE),expected,reader)
    expected.update({name:reader.pin(name) for name in (SELF,TEST,ARCHIVE,CANDIDATE,original.SELF,original.TEST)})
    def read(name):
        maintenance.require(name in expected and reader.pin(name)==expected[name],"SIGNED_COST_CURRENT_MODULE_SOURCE_DRIFT")
        return reader.text(name)
    names,modules=parent.recursive_names(read,"stored-form-tests")
    original.select_names(names)
    maintenance.require(len(modules)==59,"SIGNED_COST_COMPLETE_MODULE_INVENTORY")
    if task==PROFILE:
        name=inventory_path(inventory_run);row=reader.json(name)
        maintenance.require(row.get("source_variant")=="test-only-signed-stage-cost-r11","SIGNED_COST_CURRENT_COMPILED_VARIANT_REQUIRED")
        view=dict(row,source_variant="call-local-xml-reuse-r9",task=original.INVENTORY)
        original.accept_inventory(view,expected,names,modules)
        expected[name]=reader.pin(name)
    reader.finish()
    return expected,names,modules


def inventory_path(run):
    original.inventory_path(run)
    return f"implementation/p09/evidence/p09-149-signed-stage-cost.inventory-run{run:02}.v1.json"


def observe_cost(text):
    maintenance.require(isinstance(text,str) and len(text.encode())<=bounded.LIMIT,"SIGNED_COST_OUTPUT_BUDGET")
    events=[]; index=None; position=0
    for line in text.split("\n")[:-1]:
        if not line.startswith("P149_SIGNED_COST:"):
            continue
        match=re.fullmatch(r"P149_SIGNED_COST:([0-9]+):([a-z_]+):([0-9]+)\r?",line)
        maintenance.require(match is not None,"SIGNED_COST_CLOSED_MARKER_REQUIRED")
        case,stage,micros=int(match[1]),match[2],int(match[3])
        maintenance.require(0<=case<36 and stage in ORDER and 0<=micros<=180000000,"SIGNED_COST_MARKER_RANGE")
        if case!=index:
            maintenance.require(index is None or (case>index and position==len(ORDER)),"SIGNED_COST_CASE_ORDER_OR_INCOMPLETE_PREDECESSOR")
            index,position=case,0
        maintenance.require(position<len(ORDER) and stage==ORDER[position],"SIGNED_COST_STAGE_ORDER_OR_DUPLICATE")
        events.append({"case_index":case,"stage":stage,"elapsed_us":micros});position+=1
        maintenance.require(len(events)<=16*len(ORDER),"SIGNED_COST_COMPLETE_CORPUS_EVENT_BUDGET")
    complete=sum(event["stage"]==OUTER[-1] for event in events)
    return {"qualification":"TEST_ONLY_STAGE_ELAPSED_NOT_CPU_PROFILER_OR_CASE_RUNTIME_PASS",
        "events":events,"fully_observed_case_sequences":complete,
        "last_observed_case":index,"next_expected_stage":ORDER[position] if index is not None and position<len(ORDER) else None,
        "outer_signed_pair_overlaps_nested_PAIR_do_not_sum_both":True,"signed16_runtime_complete":False}


def run_worker(task):
    require_duration(task,180)
    real_call=subprocess.call
    def call(args,**kwargs):
        if task==PROFILE:
            maintenance.require(args[-4:]==["--",original.NAME,"--exact","--test-threads=1"],"SIGNED_COST_EXACT_WORKER_FILTER_REQUIRED")
            args=[*args[:-1],"--nocapture",args[-1]]
        return real_call(args,**kwargs)
    with patch.object(original,"INVENTORY",INVENTORY),patch.object(original,"CHANGED",PROFILE), \
            patch.object(original,"TASKS",(INVENTORY,PROFILE)),patch.object(subprocess,"call",call):
        return original.run_worker(task)


def run_owned(destination,expected,names,modules,task,seconds):
    require_duration(task,seconds)
    original_capture,original_dump=bounded.BoundedProcessCapture,json.dump
    captures=[]
    class CostCapture(original_capture):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);captures.append(self)
        def cost(self):
            with self.lock:
                text=bytes(self.buffers["stderr"]).decode("utf-8",errors="replace")
            return observe_cost(text)
        def progress(self):
            value=super().progress()
            if task==PROFILE: self.cost()
            return value
    def write(row,stream,**kwargs):
        row.update(source_variant="test-only-signed-stage-cost-r11",test_sources_changed=True,
            original_assertion_body_exact_after_declared_cfg_removal=True,
            stage_candidate=CANDIDATE,exact_CPU_profiler=False,statistical_speedup_proven=False,
            PC_freeze_resolved=False,product_complete=False,P09_gate="OPEN")
        if task==PROFILE:
            try:
                observation=captures[-1].cost() if captures else observe_cost("")
                row["signed_stage_cost"]=observation
                if row.get("state")=="PASS_SCOPED_NOT_GATE":
                    maintenance.require(observation["fully_observed_case_sequences"]==16,"SIGNED_COST_COMPLETE_MARKERS_REQUIRED")
                    observation["signed16_runtime_complete"]=True
            except ValueError as error:
                if row.get("state")=="PASS_SCOPED_NOT_GATE":
                    row.update(state="STOPPED_NOT_ACCEPTED",stop_reason="SIGNED_COST_OBSERVATION_NOT_ACCEPTED",signed_changed16_component_complete=False)
                row["signed_stage_cost_error"]=str(error) if re.fullmatch(r"SIGNED_COST_[A-Z_]+",str(error)) else "SIGNED_COST_OBSERVATION_FAILED"
        return original_dump(row,stream,**kwargs)
    with patch.object(original,"SELF",SELF),patch.object(original,"TEST",TEST), \
            patch.object(original,"INVENTORY",INVENTORY),patch.object(original,"CHANGED",PROFILE), \
            patch.object(original,"TASKS",(INVENTORY,PROFILE)),patch.object(original,"require_duration",require_duration), \
            patch.object(bounded,"BoundedProcessCapture",CostCapture),patch.object(json,"dump",write):
        return original.run_owned(destination,expected,names,modules,task,seconds)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",type=int,choices=range(1,100),required=True)
    parser.add_argument("--task",choices=(INVENTORY,PROFILE),default=PROFILE)
    parser.add_argument("--inventory-run",type=int,choices=range(1,100),default=1)
    parser.add_argument("--maximum-seconds",type=int,default=120)
    parser.add_argument("--light",action="store_true")
    args=parser.parse_args();require_duration(args.task,args.maximum_seconds)
    maintenance.require(maintenance.Path.cwd().resolve()==maintenance.ROOT,"SIGNED_COST_ROOT_SCOPE")
    windows=maintenance.Windows()
    kind="light" if args.light else ("inventory" if args.task==INVENTORY else "actual")
    dest=scoped_path(f"implementation/p09/evidence/p09-149-signed-stage-cost.{kind}-run{args.run:02}.v1.json",fresh=True)
    if not args.light:
        expected,names,modules=load_binding(windows,args.task,args.inventory_run)
        return run_owned(dest,expected,names,modules,args.task,args.maximum_seconds)
    from tests.test_signed_stage_cost import SignedStageCostTests
    reader=AuditEvidenceReader(maintenance.ROOT,lambda:None)
    freeze=[reader.pin(name) for name in (SELF,TEST,CANDIDATE,ARCHIVE,NEW)]
    with patch("subprocess.Popen",side_effect=AssertionError("SIGNED_COST_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run",side_effect=AssertionError("SIGNED_COST_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start",side_effect=AssertionError("SIGNED_COST_LIGHT_THREAD_FORBIDDEN")):
        result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(SignedStageCostTests))
    reader.finish()
    failed=sorted({t.id().split(".")[-1] for t,_ in result.failures+result.errors+result.skipped})
    passed=result.testsRun==10 and result.wasSuccessful() and not result.skipped
    row={"state":"PASS_SIGNED_COST_RUNNER_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run":result.testsRun,"tests_passed":result.testsRun-len(failed),"failed_tests":failed,
        "source_freeze":freeze,"source_freeze_exact_after":True,"product_complete":False,"P09_gate":"OPEN","Cargo_SQL_native_executed":False}
    with dest.open("x",encoding="utf-8") as stream: json.dump(row,stream,indent=2)
    print(json.dumps({key:row[key] for key in ("state","tests_run","tests_passed","failed_tests")}))
    return 0 if passed else 2


if __name__=="__main__":
    if len(sys.argv[1:])==3 and sys.argv[1:3]==["--owned-worker","--task"]:
        raise SystemExit(run_worker(sys.argv[3]))
    try:
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch(r"[A-Z_]+",str(error)) else "SIGNED_COST_OPERATION_FAILED"
        print(json.dumps({"state":"FAILED_NOT_ACCEPTED","error_code":code}))
        raise SystemExit(2) from None
