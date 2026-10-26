"""One-use external fixed block-bookmark SOURCE capture, never product PASS.

Only a current qualified jobless caller/lifecycle may start the original limited
Native owners. --inspect-only cannot claim/start Native or create source files.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import block_bookmark_source660 as runtime
import run_prepared_bookmark_native631 as publisher

r=runtime.r
SELF=runtime.ENTRY
CODE='implementation/p09/evidence/p09-361-block-bookmark-source661-code001.v1.json'
STATE='QUALIFIED661_ONE_SOURCE_CONTROLLER_ENTRY_CODE_NOT_NATIVE'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-source660-native001.v1.json'
INSPECT='implementation/p09/evidence/p09-361-block-bookmark-source660-inspection001.v1.json'
CLAIM='implementation/p09/evidence/p09-361-block-bookmark-source660-claim001.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-block-bookmark-source660-native001-forensic'
SCRATCH='target/p09-block-bookmark-source660-native001-scratch'

def parser():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--execute-source-once',action='store_true')
    group.add_argument('--inspect-only',action='store_true')
    return p

def load_code(reader):
    p=publisher.codec.unpack(reader.json(CODE))
    runtime.require(p['state']==STATE and p['cleanup']is True and type(p['fresh_inputs'])is int
        and p['fresh_inputs']==p['final_fresh_hashes']>0 and p['all_new_tests_passed']is True
        and p['Native_started']is False and p['whole_source_execution_qualified']is False,'CURRENT_CODE_NOT_NATIVE_AUTHORITY')
    pins={v['path']:v for v in p['source_pins']};paths=set(p['execution_dependency_paths'])
    runtime.require(runtime.SOURCES|{SELF}<=paths<=pins.keys()
        and runtime.prior.prepared.loaded_dependencies(r.c.ROOT)<=paths,'WHOLE_CURRENT_EXECUTION_DEPENDENCIES')
    for path,pin in pins.items():runtime.require(reader.pin(path)==pin,'CHANGED_CODE_REQUALIFY_NO_EXECUTION')
    return pins,paths,p

def close_readers(readers):
    for q in readers.values():q.finish()
    value=dict(closed=True,readers={k:dict(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)for k,q in readers.items()})
    runtime.require(runtime.sections.closed_boundary(value),'ALL_CURRENT_INPUT_READERS_CLOSED')
    return value

def main(argv=None):
    args=parser().parse_args(argv);output=INSPECT if args.inspect_only else OUTPUT
    runtime.require(Path(sys.executable)==runtime.prior.prepared.inspection.fixed.PYTHON,'FIXED_PYTHON')
    for path in(output,CLAIM,SCRATCH):runtime.prior.prepared.require_absent(r.c.ROOT,path)
    runtime.absent()
    selection=r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=runtime.sections.guard_type(r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard)))()
    start=time.monotonic();readers={}
    row=dict(state='FAILED660_BLOCK_SOURCE_CAPTURE',own_cpu_selection=selection,inspect_only=args.inspect_only,
        native_claim_created=False,source_capture_executed=False,block_content_support_qualified=False,
        reference_semantics_qualified=False,P09_gate='OPEN',P10_started=False,accepted_count_delta=0,automatic_retry=False)
    def notice(stage,value):
        print(json.dumps(dict(value,capture_purpose='fixed_block_bookmark_source_only_not_CROSSREF_acceptance')),flush=True)
        if value.get('state')in('BLOCK660_RESULT_RECORDED_BEFORE_CLEANUP','NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP','NATIVE_TRANSPORT_FAILED_BEFORE_CLEANUP'):
            key=stage+'_early_notice'
            if key not in row:row[key]=publisher.publish('implementation/p09/evidence/p09-361-block-bookmark-source660-'+stage+'-notice001.v1.json',value)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check);readers['source']=q
        manifest,paths,proof=load_code(q)
        row['python_host']=runtime.prior.prepared.runtime.require_qualification(q)
        installed=runtime.base.installed
        image=r.a.AcceptanceReader(Path(installed.native.EXECUTABLE).parent,guard.check)
        shell=r.a.AcceptanceReader(Path(runtime.base.candidate.original.SHELL).parent,guard.check)
        python=r.a.AcceptanceReader(installed.fixed.PYTHON.parent,guard.check)
        readers=dict(source=q,native=image,shell=shell,runtime=python)
        runtime.prior.prepared.runtime.verify_current_reader(python)
        shell_expected=shell.pin(Path(runtime.base.candidate.original.SHELL).name)
        runtime.require(shell_expected==proof['worker_shell_pin'],'SAME_CODE_QUALIFIED_X86_SHELL')
        row['prerequisites']=installed.prerequisites.inspect(guard.windows,guard.check,
            lambda:image.fresh_pin(Path(installed.native.EXECUTABLE).name))
        row['preparation_boundary']=close_readers(readers)
        if args.inspect_only:
            guard.complete(lambda:runtime.sections.closed_boundary(row['preparation_boundary']),preflight=True)
            row['state']='OBSERVED660_CURRENT_PREREQUISITES_ONLY_NOT_NATIVE_OR_SESSION'
        else:
            runtime.require(row['prerequisites']['all_observed_prerequisites_passed'],'CURRENT_NATIVE_PREREQUISITES_DENIED_NO_CLAIM')
            guard.advance('qualification',lambda:runtime.sections.closed_boundary(row['preparation_boundary']))
            row['claim']=publisher.publish(CLAIM,dict(state='ONE_FIXED_BLOCK_SOURCE_CAPTURE_CLAIMED_NO_RETRY',
                purpose='current_lifecycle_then_one_synthetic_source_eight_blocks_save_independent_reopen',code_receipt=CODE,
                code_sha256=q.snapshots[CODE]['sha256'],Native_execution_is_not_product_or_F11_acceptance=True,P09_complete=False))
            row['native_claim_created']=True
            (r.c.ROOT/SCRATCH).mkdir();env=r.audit.environment()
            env.update(TEMP=str(r.c.ROOT/SCRATCH),TMP=str(r.c.ROOT/SCRATCH),PYTHONDONTWRITEBYTECODE='1')
            runtime.execute(guard,manifest,paths,shell_expected,env,notice,row)
            guard.advance('final_audit',lambda:row.get('batch_closed_for_final_audit')is True)
            final={}
            for label,old in readers.items():
                fresh=r.a.AcceptanceReader(old.root,guard.check)
                for path,pin in old.snapshots.items():runtime.require(fresh.pin(path)==pin,'WHOLE_FINAL_CURRENT_INPUTS')
                final[label]=fresh
            readers=final;row['final_audit_boundary']=close_readers(readers)
            guard.complete(lambda:runtime.sections.closed_boundary(row['final_audit_boundary'])and row['batch_closed_for_final_audit'])
            row.update(state='CAPTURED660_FIXED_BLOCK_SOURCE_PRODUCER_BOUND_SEMANTICS_UNQUALIFIED',source_capture_executed=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**runtime.prior.io.safe_failure(error),rerun_forbidden=True)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(row[k].get('cleanup')is True for k in('qualification_worker','capture_worker')if k in row),
            elapsed_seconds=round(time.monotonic()-start,3),section_timing=guard.section_summary(),resource_samples=guard.samples,
            source_pins=[]if'source'not in readers else list(readers['source'].snapshots.values()),
            fresh_inputs=0 if'source'not in readers else len(readers['source'].snapshots),
            final_fresh_hashes=0 if'source'not in readers else readers['source'].final_fresh_hashes)
        spool=SPOOL.replace('native001','inspection001')if args.inspect_only else SPOOL
        normalized,retained=publisher.retention.retain(r.c.ROOT,spool,row)
        pin=publisher.publish(output,normalized)
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),cleanup=row['cleanup'],
            native_claim_created=row['native_claim_created'],source_capture_executed=row['source_capture_executed'],
            prerequisites_passed=row.get('prerequisites',{}).get('all_observed_prerequisites_passed'),
            block_content_support_qualified=False,P09_complete=False,receipt=pin,retained_metadata=retained)),flush=True)
    return 0 if row['state'].startswith(('CAPTURED660_','OBSERVED660_'))and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())


