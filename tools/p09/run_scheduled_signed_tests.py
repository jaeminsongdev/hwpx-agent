"""Original full signed16 and two-package profile; meaningful binding sample cadence."""
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

import run_optimized_signed_tests as previous
from audit_evidence_io import AuditEvidenceReader
from scheduled_binding_resources import ScheduledBinding, SELF as SCHEDULE_SOURCE
from sql_owned_execution import scoped_path

maintenance = previous.maintenance
SELF = "tools/p09/run_scheduled_signed_tests.py"
TEST = "tools/p09/tests/test_scheduled_signed_tests.py"
INVENTORY = "stored-signed-scheduled-inventory"
PROFILE = "stored-signed-scheduled-tests"
VARIANT = "unchanged-r11-Rust-two-package-profile-scheduled-binding-r13"
ARCHIVE = "implementation/p09/source-archive/p09-149-pre-scheduled-reader-constructor-r13/helper-preimages.v1.json"
FAILURE = "implementation/p09/evidence/p09-149-signed-scheduled.binding-failure-run01.v1.json"
LIGHT01 = "implementation/p09/evidence/p09-149-signed-scheduled.light-run01.v1.json"


def require_duration(task, seconds):
    maintenance.require(task in (INVENTORY,PROFILE), "SCHEDULED_SIGNED_TASK_SCOPE")
    previous.require_duration(previous.INVENTORY if task == INVENTORY else previous.PROFILE, seconds)


def inventory_path(run):
    previous.previous.original.inventory_path(run)
    return f"implementation/p09/evidence/p09-149-signed-scheduled.inventory-run{run:02}.v1.json"


def accept_inventory(row, expected, names, modules):
    maintenance.require(row.get("source_variant") == VARIANT and row.get("task") == INVENTORY
        and row.get("binding_resource_schedule",{}).get("all_legacy_readers_final_fresh_hash_inventory_exact") is True
        and row.get("binding_resource_schedule",{}).get("cleanup_confirmed") is True,
        "SCHEDULED_SIGNED_CURRENT_PROFILE_INVENTORY_REQUIRED")
    previous.accept_inventory(dict(row, source_variant=previous.SOURCE_VARIANT, task=previous.INVENTORY),expected,names,modules)


def load_binding(windows, task, inventory_run):
    require_duration(task,180)
    guard = ScheduledBinding(windows)
    with guard:
        expected,names,modules = previous.load_binding(windows,previous.INVENTORY,1)
    schedule = guard.summary()
    maintenance.require(schedule["all_legacy_readers_final_fresh_hash_inventory_exact"]
        and schedule["cleanup_confirmed"] and schedule["original_resource_stop"] is None,
        "SCHEDULED_SIGNED_BINDING_NOT_ACCEPTED")
    # Fresh independent metadata guard; closed legacy callback scheduling is already restored.
    from sql_runtime_supervision import SQLRuntimeResources,finish_watcher
    resources = SQLRuntimeResources();resources.admit()
    reader = AuditEvidenceReader(maintenance.ROOT,resources.checkpoint_io)
    try:
        archive,failed = reader.json(ARCHIVE),reader.json(FAILURE)
        maintenance.require(archive['binding_failure'] == failed
            and archive['binding_failure_path'] == FAILURE
            and failed['state'] == 'FAILED_NOT_ACCEPTED'
            and failed['error_code'] == 'READER_CONSTRUCTOR_ARGUMENT_BINDING_FAILED'
            and failed['original_reader_constructor_restored'] is True
            and failed['Cargo_SQL_native_executed'] is False
            and archive['light01_pin'] == reader.pin(LIGHT01), 'SCHEDULED_SIGNED_PRIOR_FAILURE_REQUIRED')
        old = {pin['path']:pin for pin in failed['source_freeze']}
        seen=set()
        for item in archive['files']:
            name=item['path'];raw=base64.b64decode(item['base64'],validate=True)
            pin={key:item[key] for key in ('path','bytes','sha256')}
            maintenance.require(name in (SELF,TEST,SCHEDULE_SOURCE) and name not in seen
                and old[name] == pin and len(raw) == pin['bytes']
                and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'SCHEDULED_SIGNED_WHOLE_PREIMAGE_DRIFT')
            seen.add(name)
        maintenance.require(seen == set(old) == {SELF,TEST,SCHEDULE_SOURCE}, 'SCHEDULED_SIGNED_COMPLETE_PREIMAGES_REQUIRED')
        expected.update({name:reader.pin(name) for name in (SELF,TEST,SCHEDULE_SOURCE,ARCHIVE,FAILURE,LIGHT01)})
        if task == PROFILE:
            name = inventory_path(inventory_run)
            accept_inventory(reader.json(name),expected,names,modules)
            expected[name] = reader.pin(name)
        reader.finish()
    finally:
        state = {}; maintenance.require(finish_watcher(resources,state),"STOP_BINDING_WATCHER_CLEANUP_FAILED")
    return expected,names,modules,schedule


def run_worker(task):
    require_duration(task,180)
    with patch.object(previous,"INVENTORY",INVENTORY),patch.object(previous,"PROFILE",PROFILE):
        return previous.run_worker(task)


def run_owned(destination,expected,names,modules,schedule,task,seconds):
    require_duration(task,seconds)
    real_dump = json.dump
    def write(row,stream,**kwargs):
        row.update(source_variant=VARIANT,binding_resource_schedule=schedule,
            original_owned_resource_policy_changed=False,full249_current_qualified=False,
            product_complete=False,P09_gate="OPEN")
        return real_dump(row,stream,**kwargs)
    with patch.object(previous,"SELF",SELF),patch.object(previous,"TEST",TEST), \
            patch.object(previous,"INVENTORY",INVENTORY),patch.object(previous,"PROFILE",PROFILE), \
            patch.object(json,"dump",write):
        return previous.run_owned(destination,expected,names,modules,task,seconds)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",type=int,choices=range(1,100),required=True)
    parser.add_argument("--task",choices=(INVENTORY,PROFILE),default=PROFILE)
    parser.add_argument("--inventory-run",type=int,choices=range(1,100),default=1)
    parser.add_argument("--maximum-seconds",type=int,default=120)
    parser.add_argument("--light",action="store_true")
    args=parser.parse_args();require_duration(args.task,args.maximum_seconds)
    maintenance.require(maintenance.Path.cwd().resolve()==maintenance.ROOT,"SCHEDULED_SIGNED_ROOT_SCOPE")
    windows=maintenance.Windows()
    kind="light" if args.light else ("inventory" if args.task==INVENTORY else "actual")
    destination=scoped_path(f"implementation/p09/evidence/p09-149-signed-scheduled.{kind}-run{args.run:02}.v1.json",fresh=True)
    if not args.light:
        expected,names,modules,schedule=load_binding(windows,args.task,args.inventory_run)
        return run_owned(destination,expected,names,modules,schedule,args.task,args.maximum_seconds)
    from tests.test_scheduled_signed_tests import ScheduledSignedTests
    reader=AuditEvidenceReader(maintenance.ROOT,lambda:None)
    freeze=[reader.pin(n) for n in (SELF,TEST,SCHEDULE_SOURCE)]
    with patch("subprocess.Popen",side_effect=AssertionError("SCHEDULED_LIGHT_CHILD_FORBIDDEN")), \
            patch("subprocess.run",side_effect=AssertionError("SCHEDULED_LIGHT_CHILD_FORBIDDEN")), \
            patch("threading.Thread.start",side_effect=AssertionError("SCHEDULED_LIGHT_THREAD_FORBIDDEN")):
        result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(ScheduledSignedTests))
    reader.finish()
    failed=sorted({t.id().split(".")[-1] for t,_ in result.failures+result.errors+result.skipped})
    passed=result.testsRun==17 and result.wasSuccessful() and not result.skipped
    row={"state":"PASS_SCHEDULED_BINDING_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE" if passed else "FAILED_NOT_ACCEPTED",
        "tests_run":result.testsRun,"tests_passed":result.testsRun-len(failed),"failed_tests":failed,
        "source_freeze":freeze,"source_freeze_exact_after":True,"product_complete":False,
        "P09_gate":"OPEN","Cargo_SQL_native_executed":False}
    with destination.open("x",encoding="utf-8") as stream:json.dump(row,stream,indent=2)
    print(json.dumps({key:row[key] for key in ("state","tests_run","tests_passed","failed_tests")}))
    return 0 if passed else 2


if __name__=="__main__":
    if len(sys.argv[1:])==3 and sys.argv[1:3]==["--owned-worker","--task"]:
        raise SystemExit(run_worker(sys.argv[3]))
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch(r"[A-Z_]+",str(error)) else "SCHEDULED_SIGNED_OPERATION_FAILED"
        print(json.dumps({"state":"FAILED_NOT_ACCEPTED","error_code":code}))
        raise SystemExit(2) from None
