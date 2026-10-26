"""One fresh current-session + renamed eight initial/saved/reopened BMP capture.
No insertion/refresh/revision/result-ingestion or previous Native replay.
"""
import argparse,json,sys,subprocess,time
from pathlib import Path
from types import SimpleNamespace as NS
import prepared_bookmark_native768 as runtime
import run_prepared_bookmark_native631 as publisher
import prepared_bookmark690_receipt as codec
r=runtime.r
SELF='tools/p09/run_prepared_bookmark_native768.py'
CODE='implementation/p09/evidence/p09-361-bookmark-cursor770-code001.v1.json'
STATE='QUALIFIED770_BOOKMARK_CURSOR_CODE_AND_READY_DENIAL_NOT_NATIVE'
OUTPUT='implementation/p09/evidence/p09-361-prepared-bookmark768-native001.v1.json'
INSPECT='implementation/p09/evidence/p09-361-prepared-bookmark768-inspection001.v1.json'
CLAIM='implementation/p09/evidence/p09-361-prepared-bookmark768-claim001.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-prepared-bookmark768-native001-forensic'
SCRATCH='target/p09-prepared-bookmark768-native001-scratch'

def parser():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--execute-bookmark-cursor-eight-once',action='store_true');g.add_argument('--inspect-only',action='store_true');return p

def publish(path,value):
    return r.shared.publisher.publish(r.c.ROOT,path,codec.pack(value,lambda:None),NS(require=r.c.require,exact=r.a.exact))

def load_code(reader):
    proof=codec.unpack(reader.json(CODE),reader.checkpoint)
    runtime.require(proof['state']==STATE and proof['cleanup']is True and proof['fresh_inputs']==proof['final_fresh_hashes']>0
        and proof['all_new_tests_passed']is True and proof['actual_native_started']is False
        and proof['ready_denial']['cleanup']is True and proof['ready_denial']['requests']==1
        and proof['ready_denial']['result']['completed_callback_cases']==0,'PREPARED768_CURRENT_CODE_PROOF')
    pins={p['path']:p for p in proof['source_pins']};paths=set(proof['execution_dependency_paths'])
    runtime.require(runtime.SOURCES|{SELF}<=paths<=set(pins)and runtime.prepared.loaded_dependencies(r.c.ROOT)<=paths,'PREPARED768_WHOLE_EXECUTION_CLOSURE')
    for path,pin in pins.items():runtime.require(reader.pin(path)==pin,'PREPARED768_CHANGED_INPUT_REQUALIFY')
    return pins,paths,proof

def close_readers(readers):
    for q in readers.values():q.finish()
    value=dict(closed=True,readers={k:dict(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)for k,q in readers.items()})
    runtime.require(runtime.sections.closed_boundary(value),'PREPARED768_WHOLE_READER_CLOSURE');return value

def main(argv=None):
    args=parser().parse_args(argv);output=INSPECT if args.inspect_only else OUTPUT
    runtime.require(Path(sys.executable)==runtime.prepared.inspection.fixed.PYTHON,'PREPARED768_FIXED_PYTHON')
    for path in(output,CLAIM,SCRATCH):runtime.prepared.require_absent(r.c.ROOT,path)
    runtime.absent();selection=r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=runtime.sections.guard_type(r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard)))()
    begin=time.monotonic();readers={}
    row=dict(state='FAILED768_BLOCK_PRODUCT_CAPTURE',inspect_only=args.inspect_only,own_cpu_selection=selection,native_claim_created=False,
        fixed_eight_executed=False,SDK_insertion_invoked=False,REF036_refresh_invoked=False,reference_semantics_qualified=False,
        P09_gate='OPEN',P10_started=False,accepted_count_delta=0,automatic_retry=False)
    def notice(stage,value):
        print(json.dumps(dict(value,capture_purpose='direct_bookmark_target_cursor_only_no_link_activation_or_save')),flush=True)
        if value.get('state')in('NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP','NATIVE_TRANSPORT_FAILED_BEFORE_CLEANUP'):
            key=stage+'_early_notice'
            if key not in row:row[key]=publish('implementation/p09/evidence/p09-361-prepared-bookmark768-'+stage+'-notice001.v1.json',value)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check);readers['source']=q
        manifest,paths,proof=load_code(q)
        row['prepared_files']=runtime.prepared.validate_prepared(q)
        row['python_host']=runtime.prepared.runtime.require_qualification(q);installed=runtime.base.installed
        image=r.a.AcceptanceReader(Path(installed.native.EXECUTABLE).parent,guard.check)
        shell=r.a.AcceptanceReader(Path(runtime.base.candidate.original.SHELL).parent,guard.check)
        python=r.a.AcceptanceReader(installed.fixed.PYTHON.parent,guard.check)
        readers=dict(source=q,native=image,shell=shell,runtime=python);runtime.prepared.runtime.verify_current_reader(python)
        shell_expected=shell.pin(Path(runtime.base.candidate.original.SHELL).name)
        runtime.require(shell_expected==proof['shell_pin'],'PREPARED768_EXACT_VERIFIED_SHELL')
        row['prerequisites']=installed.prerequisites.inspect(guard.windows,guard.check,lambda:image.fresh_pin(Path(installed.native.EXECUTABLE).name))
        row['preparation_boundary']=close_readers(readers)
        if args.inspect_only:
            guard.complete(lambda:runtime.sections.closed_boundary(row['preparation_boundary']),preflight=True)
            row['state']='OBSERVED768_CURRENT_PREREQUISITES_NOT_NATIVE_OR_SESSION'
        else:
            runtime.require(row['prerequisites']['all_observed_prerequisites_passed'],'PREPARED768_CURRENT_PREREQUISITES_DENIED_NO_CLAIM')
            guard.advance('qualification',lambda:runtime.sections.closed_boundary(row['preparation_boundary']))
            row['claim']=publish(CLAIM,dict(state='ONE_NEW_BOOKMARK_CURSOR_EIGHT_CLAIMED_NO_RETRY',purpose='current_session_then_eight_initial_reopened_direct_bookmark_cursor_pairs',
                code_receipt=CODE,code_sha256=q.snapshots[CODE]['sha256'],P09_complete=False));row['native_claim_created']=True
            (r.c.ROOT/SCRATCH).mkdir();env=r.audit.environment();env.update(TEMP=str(r.c.ROOT/SCRATCH),TMP=str(r.c.ROOT/SCRATCH),PYTHONDONTWRITEBYTECODE='1')
            runtime.execute(guard,manifest,paths,shell_expected,env,notice,row)
            guard.advance('final_audit',lambda:row.get('batch_closed_for_final_audit')is True)
            current={}
            for label,old in readers.items():
                fresh=r.a.AcceptanceReader(old.root,guard.check)
                for name,pin in old.snapshots.items():runtime.require(fresh.pin(name)==pin,'PREPARED768_FINAL_FRESH_INPUTS')
                current[label]=fresh
            readers=current;row['final_audit_boundary']=close_readers(readers)
            guard.complete(lambda:runtime.sections.closed_boundary(row['final_audit_boundary'])and row['batch_closed_for_final_audit'])
            row.update(state='CAPTURED768_DIRECT_BOOKMARK_CURSOR_PAIRS_NOT_HYPERLINK_OR_P09',bookmark_cursor_eight_executed=True,fixed_eight_executed=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**runtime.io.safe_failure(error),rerun_forbidden=True)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(row[k].get('cleanup')is True for k in('qualification_worker','capture_worker')if k in row),
            elapsed_seconds=round(time.monotonic()-begin,3),section_timing=guard.section_summary(),resource_samples=guard.samples,
            source_pins=[]if'source'not in readers else list(readers['source'].snapshots.values()),fresh_inputs=0 if'source'not in readers else len(readers['source'].snapshots),
            final_fresh_hashes=0 if'source'not in readers else readers['source'].final_fresh_hashes)
        spool=SPOOL.replace('native001','inspection001')if args.inspect_only else SPOOL
        normalized,retained=publisher.retention.retain(r.c.ROOT,spool,row);pin=publish(output,normalized)
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),cleanup=row['cleanup'],native_claim_created=row['native_claim_created'],
            fixed_eight_executed=row['fixed_eight_executed'],prerequisites_passed=row.get('prerequisites',{}).get('all_observed_prerequisites_passed'),
            P09_complete=False,receipt=pin,retained_metadata=retained)),flush=True)
    return 0 if row['state'].startswith(('CAPTURED761_','OBSERVED768_'))and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
