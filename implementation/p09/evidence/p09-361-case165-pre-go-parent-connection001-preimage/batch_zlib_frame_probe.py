"""Construct the actual case165 parent with a reversible pre-GO stop.

Only --connect-only exists. No Native run, worker, GO, product or receipt
namespace is enabled here. Reuse the completed metadata driver unchanged;
add just these two named diagnostic programs to the current input scope.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/batch_zlib_frame_probe.py'
ADAPTER='tools/p09/batch_pre_go_stop.py'
METADATA=dict(path='tools/p09/batch_zlib_metadata.py',bytes=19240,
    sha256='c8611aada02a99d9d82d29c3823d67bc835332ec053006f6706fea1785bf8115')


def require(ok,code):
    if not ok:raise ValueError('ZLIB_FRAME_PROBE_'+code)


def bootstrap(root):
    path=root/METADATA['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_METADATA_PROGRAM')
    for directory in (path.parent,*path.parent.parents):
        require(directory.is_dir() and not directory.is_symlink() and not directory.is_junction(),
            'DIRECT_METADATA_ANCESTORS')
        if directory==root:break
    with path.open('rb') as stream:raw=stream.read(METADATA['bytes']+1)
    require(len(raw)==METADATA['bytes'] and hashlib.sha256(raw).hexdigest()==METADATA['sha256'],
        'EXACT_COMPLETED_METADATA_DRIVER')
    env=dict(__name__='p09_exact_frame_probe_metadata',__file__=str(path))
    exec(compile(raw,METADATA['path'],'exec'),env)
    return NS(**env)


def extended_parent(parent,extras):
    original=parent.project_plan
    def project(data,manifest,additions,batch,checkpoint):
        return original(data,manifest,batch.scope.extend(additions,extras),batch,checkpoint)
    return NS(**{**vars(parent),'project_plan':project})


def main():
    require(sys.argv[1:]==['--connect-only'],'ONLY_PARENT_CONSTRUCTION_NO_EXECUTION_MODE')
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/p09'));sys.dont_write_bytecode=True
    metadata=bootstrap(root);denied=[];sys.addaudithook(metadata.process_blocker(denied))
    prep,parent,loader,entry,profile=metadata.bootstrap(root)
    import accept_case112_current_epoch as a,conservative_maintenance as c,owned_source_read_pressure as byte_policy
    policy,witness,Reader,chunk=metadata.approved_admission(root,prep,loader,entry,a,c)
    guards,_=loader.load(root,list(entry.BOOTSTRAP[1:]),{})
    guards.prepared_run_closure_v1.configure_host_policy(c)
    def factory(role):
        return guards.owned_cpu_baseline_v1.guard_type(policy.guard_type(
            guards.distinct_final_sample_guard_v1.guard_type(a.Guard),role=role))()
    epochs=metadata.ReadOnlyEpochs(factory);q=context=adapter=None;started=time.monotonic()
    row=dict(state='FAILED_ACTUAL_PRE_GO_PARENT_CONNECTION_NOT_NATIVE',GO_authorized=False,
        accepted_count_delta=0,actual_worker_or_product_or_Frame_executed=False,
        policy_admission=witness,earlier_complete_whole_and_metadata_reexecuted=False)
    try:
        epochs.advance('construction');q=Reader(root,epochs.check)
        a.exact(q.pin(METADATA['path']),METADATA,'EXACT_COMPLETED_DRIVER_NOT_EDITED')
        extras={name:dict(q.pin(name)) for name in (SELF,ADAPTER)}
        selected=extended_parent(parent,extras)
        context=metadata.construct(root,q,epochs,a,selected,entry,profile,loader,prep,policy,witness,byte_policy)
        batch=context.result.assembled.batch
        for name,pin in extras.items():a.exact(batch.current[name],pin,'EXPLICIT_NEW_DIAGNOSTIC_INPUT')
        libraries,_=context.connected.loader.load(root,[extras[ADAPTER]],{})
        actual_context=metadata.readiness_context(context.result)
        adapter=libraries.batch_pre_go_stop.connect_parent(actual_context)
        metadata.idle(context.result)
        row.update(scope_projection=context.projection,
            helper_inventory=context.result.proof['helper_inventory'],
            original_complete_cost=context.result.proof['original_complete_cost'],
            with_preparation15_seconds=context.result.proof['with_preparation15_seconds'],
            actual_parent_connection_installed=True,
            parent_connect_same_code=adapter.wrapped.__code__ is adapter.original.__code__,
            parent_connect_same_globals=adapter.wrapped.__globals__ is adapter.original.__globals__,
            parent_connect_same_defaults=adapter.wrapped.__defaults__ is adapter.original.__defaults__,
            explicit_dependency_slot='connection',Native_source_scope_exclusions_added=False)
        adapter.restore();metadata.idle(context.result)
        require(actual_context.windows[0].component.connect is adapter.original,'ACTUAL_PRIVATE_CONNECTION_RESTORED')
        q.finish();epochs.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'FULL_CURRENT_CONSTRUCTION_CLOSING')
        row.update(state='PASS_ACTUAL_PRE_GO_PARENT_CONNECTION_NOT_NATIVE',
            actual_parent_context=actual_context.evidence(),private_connection_restored=True,
            actual_readiness_or_Native_or_combined_decoder_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError,ImportError,MemoryError) as error:
        epochs.broken=True;row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
        if error.args and error.args[0]=='BATCH_ENGINE_EVERY_OBSERVED_HELPER_ALREADY_DECLARED':row['undeclared_helpers']=list(error.args[1])
        import traceback
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        try:
            if adapter is not None:adapter.restore()
            if context is not None:context.result.assembled.batch.shared.restore()
        except (ValueError,OSError):row['state']='CLEANUP_FAILED_PRE_GO_PARENT_CONNECTION'
        try:epochs.close()
        except (ValueError,OSError):row['state']='CLEANUP_FAILED_PRE_GO_PARENT_CONNECTION'
        cleanup=bool(epochs.records) and all(r['cleanup_confirmed'] is True for r in epochs.records)
        if not cleanup:row['state']='CLEANUP_FAILED_PRE_GO_PARENT_CONNECTION'
        row.update(cleanup_confirmed=cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            preparation_epochs=[metadata.epoch_evidence(r) for r in epochs.records],
            process_creation_attempts=len(denied),Native_policy_changed=False)
        print(json.dumps(row,ensure_ascii=True),flush=True)
    return 0 if row['state'].startswith('PASS_') and cleanup else 2


def entrypoint():
    try:return main()
    except (ValueError,OSError,KeyError,TypeError,AttributeError,ImportError) as error:
        row=dict(state='FAILED_PRE_GO_PARENT_BOOTSTRAP_OR_ADMISSION_NOT_NATIVE',error_type=type(error).__name__,
            GO_authorized=False,accepted_count_delta=0,actual_worker_or_product_or_Frame_executed=False,
            preparation_evidence=getattr(error,'preparation_evidence',[]))
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}',error.args[0]):row['error_code']=error.args[0]
        print(json.dumps(row,ensure_ascii=True),flush=True);return 2


if __name__=='__main__':raise SystemExit(entrypoint())
