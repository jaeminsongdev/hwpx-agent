"""User-run external-terminal inspection only. No Native CLI or execution path.

Usage is deliberately closed: --inspect-only --inspection-run 1..8. It writes a
new immutable inspection receipt; existing receipts, failures and sources stay.
Even success requires a future live host/factory qualification before fixed8.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace as NS

import named_style_verification_runtime as r
import crossref_external_host_inspection as inspection

SELF='tools/p09/inspect_external_crossref_host.py'
MODULE='tools/p09/crossref_external_host_inspection.py'
TEST='tools/p09/tests/test_crossref_external_host_inspection.py'
CODE='implementation/p09/evidence/p09-361-external-crossref-host-packed389.v1.json'
CODE_STATE='PASS_EXTERNAL_HOST_INSPECTION_CONTRACTS_AND_ACTUAL_JOB_DENIAL_NOT_NATIVE_OR_GATE'


def receipt_name(run):
    r.c.require(type(run)is int and 1<=run<=8,'EXTERNAL_HOST_CLOSED_INSPECTION_RUN')
    return f'implementation/p09/evidence/p09-361-external-crossref-host-inspection-run{run:03}.v1.json'


def safe_code(error):
    value=error.args[0]if error.args else None
    return value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'EXTERNAL_HOST_INSPECTION_FAILURE_NO_RAW_VALUES'


def load_code_proof(reader):
    proof=r.compact.unpack(reader.json(CODE))
    r.c.require(proof['state']==CODE_STATE and proof['cleanup']is True
        and proof['fresh_inputs']==proof['final_fresh_hashes']>0
        and proof['contracts']==dict(run=1,errors=0,failures=0,skipped=0)
        and proof['current_distinct_contracts']==24 and proof['retained_contracts']==23,
        'EXTERNAL_HOST_VERIFIED_INSPECTION_CODE_REQUIRED')
    return proof


def main(argv=None):
    parser=argparse.ArgumentParser(description='Readonly external CROSSREF host inspection; never starts Hangul.')
    parser.add_argument('--inspect-only',action='store_true',required=True)
    parser.add_argument('--inspection-run',type=int,choices=range(1,9),required=True)
    args=parser.parse_args(argv);output=receipt_name(args.inspection_run)
    c,a,shared=r.c,r.a,r.shared
    c.require(Path(sys.executable)==inspection.fixed.PYTHON,'EXTERNAL_HOST_FIXED_PYTHON_PATH')
    c.require(not(c.ROOT/output).exists() and not(c.ROOT/output).is_symlink(),'EXTERNAL_HOST_IMMUTABLE_INSPECTION_RECEIPT')
    shared.host.configure_host_policy(c)
    # Preparation policy is used only for this childless probe. Actual Native
    # continues to require its original native guard and factory independently.
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=runtime=None;started=time.monotonic()
    row=dict(state='FAILED_EXTERNAL_HOST_INSPECTION_NOT_NATIVE',inspection_run=args.inspection_run,
        actual_Hangul_or_COM_or_child_started=False,permission_dialog_requested=False,
        source_or_OS_settings_changed=False,fixed_eight_executed=False,native_startup_qualified=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);proof=load_code_proof(q)
        pins={p['path']:p for p in proof['source_pins']}
        for path in sorted({SELF,MODULE,TEST}|set(proof['inspection_dependency_paths'])):
            c.require(q.pin(path)==pins[path],'EXTERNAL_HOST_INSPECTION_INPUT_CHANGED_REQUALIFY')
        # Include every locally imported dependency actually used by this entry.
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':
                    relative=path.relative_to(c.ROOT).as_posix()
                    c.require(relative in pins and q.pin(relative)==pins[relative],'EXTERNAL_HOST_IMPORTED_DEPENDENCY_CHANGED')
        executable=Path(inspection.native.EXECUTABLE)
        image=a.AcceptanceReader(executable.parent,guard.check)
        runtime=a.AcceptanceReader(inspection.fixed.PYTHON.parent,guard.check)
        row['observation']=inspection.inspect(guard.windows,guard.check,
            lambda:image.pin(executable.name),lambda:runtime.pin(inspection.fixed.PYTHON.name))
        image.finish();runtime.finish();q.finish();guard.check(force=True)
        passed=row['observation']['external_jobless_prerequisites_observed']
        row.update(state='OBSERVED_EXTERNAL_JOBLESS_PREREQUISITES_EMPTY_LIMITS_NOT_NATIVE_OR_SESSION'if passed else'DENIED_EXTERNAL_HOST_PREREQUISITES_NO_NATIVE_STARTED',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            external_image_final_hashes=image.final_fresh_hashes,external_runtime_final_hashes=runtime.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        row.update(error_type=type(error).__name__,error_code=safe_code(error))
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),
            external_image_pins=[]if image is None else list(image.snapshots.values()),
            external_runtime_pins=[]if runtime is None else list(runtime.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),receipt=pin,
            cleanup=row['cleanup'],elapsed_seconds=row['elapsed_seconds'],fixed_eight_executed=False,native_startup_qualified=False)),flush=True)
    return 0 if row['state'].startswith('OBSERVED_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
