"""Actual whole opening/metadata/closing; no Frame, worker, GO or product.

Four original600 preparation epochs keep large whole reads separate from the
metadata body. Native source/15-second readiness/10-second product clocks are
not started, reset, extended or qualified by this inspection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import traceback
from types import SimpleNamespace as NS

SELF='tools/p09/native011_metadata_audit.py'
PLAN=dict(path='tools/p09/native011_parent_plan.py',bytes=24332,
    sha256='b58c2658510f7af5824a4b54d64fe6858cd128a1ddef1e235b00bd46238c69b8')
EPOCH=dict(path='tools/p09/native011_metadata_epochs.py',bytes=5696,
    sha256='4afc83d1ec7af136081a2314ae92cce1f63f14398a7cc6982ece9d3692275eb1')


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_METADATA_AUDIT_'+code)


def bootstrap(root):
    path=root/PLAN['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_CONSTRUCTION_SOURCE')
    with path.open('rb') as stream:raw=stream.read(PLAN['bytes']+1)
    require(len(raw)==PLAN['bytes'] and hashlib.sha256(raw).hexdigest()==PLAN['sha256'],'PINNED_WHOLE_CONSTRUCTION_MODULE')
    env=dict(__name__='p09_exact_native011_metadata_construction',__file__=PLAN['path'])
    exec(compile(raw,PLAN['path'],'exec'),env)
    return NS(**env)


def digest(rows):
    return hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=True,allow_nan=False,
        separators=(',',':')).encode('ascii')).hexdigest()


def metadata(root,epochs,context,a):
    owner=context.data.planned.batch;graph=context.prepared.entry.graph
    require(owner.phase=='READY' and owner.initial==context.batch.plain(owner.whole),'REAL_COMPLETE_WHOLE_OPENING_REQUIRED')
    build=context.prepared.linked.engine.run_owned.__globals__['build']
    reader=build.BuildReader(root,epochs.check)
    required,rust=context.bound.attached.callback(reader)
    projected,_=graph.binding.project(required,epochs.check)
    a.exact(context.batch.plain(projected.physical_pins),context.data.planned.current,'EXACT_ACTUAL_CURRENT_METADATA_SCOPE')
    # Admit the actual post-callback default/helper set before closing this
    # metadata reader. It is not unioned into the runtime declaration.
    helpers=context.oracle_result.known
    for name in context.row['oracle_construction']['helper_inventory']['original_Native_helper_union']:
        a.exact(reader.pin(name),helpers[name],'ACTUAL_DECLARED_HELPER_METADATA_BYTES')
    with owner.metadata_reader(reader,graph.binding):reader.finish()
    epochs.check(force=True);epochs.validator(context)
    require(reader.final_fresh_hashes==len(reader.snapshots),'ALL_ACTUAL_METADATA_CLOSING_HASHES')
    connection=owner.metadata_connection
    require(len(connection.readers)==len(connection.budgets)==1 and connection.readers[0] is reader,
        'ONE_REAL_ENGINE_METADATA_READER')
    return dict(state='PASS_ACTUAL_NATIVE011_METADATA_CALLBACK_NOT_NATIVE',
        fresh_inputs=len(reader.snapshots),final_fresh_hashes=reader.final_fresh_hashes,
        physical_read_passes=reader.read_passes,physical_bytes_read=reader.bytes_read,
        selected_current_inputs=len(projected.physical_pins),rust_inputs=len(rust),
        callback_attempts=len(context.bound.attached.calls),
        metadata=context.shared.components.fresh_lossless_metadata_reader_v1.summary(reader),
        shared_decoder=owner.shared.evidence(),metadata_body_executed=True,
        original_engine_run_owned_called=False,Frame_created=False,worker_created=False,GO_authorized=False)


def main():
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    require(1<=args.attempt<=8 and 1<=args.generation<=8,'CLOSED_READONLY_AUDIT_IDENTIFIERS')
    denied=[]
    def deny(event,arguments):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('NATIVE011_METADATA_AUDIT_PROCESS_DENIED')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import current_stored_runtime_scope as scope,owned_source_read_pressure as bytes_policy
    root=c.ROOT;plan=bootstrap(root);loader=plan.bootstrap_loader(root)
    modules,_=loader.load(root,list(plan.GUARDS)+[EPOCH,plan.PUBLISHER],{})
    host,baseline,policy,final=(getattr(modules,n) for n in ('prepared_run_closure_v1',
        'owned_cpu_baseline_v1','preparation_attributed_cpu_v1','distinct_final_sample_guard_v1'))
    helper=modules.native011_metadata_epochs;publisher=modules.successor_preparation_workspace_v1
    host.configure_host_policy(c)
    def factory(role):return baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role=role))()
    epochs=helper.Epochs(factory);q=context=None;started=time.monotonic()
    output=f'implementation/p09/evidence/p09-361-native011-metadata-audit-attempt{args.attempt:03}.v1.json'
    row=dict(state='FAILED_NATIVE011_ACTUAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE',
        GO_authorized=False,accepted_count_delta=0,actual_Native_Frame_created=False,actual_product_executed=False)
    def advance(stage):
        epochs.advance(stage);index=helper.STAGES.index(stage)
        print('P146_STAGE:'+helper.MARKERS[index],file=sys.stderr,flush=True)
        print(json.dumps(dict(phase=stage,phase_index=index,original_limit_seconds=600,
            Native_clock_started=False,elapsed_seconds=time.monotonic()-started)),flush=True)
    try:
        require(not (root/output).exists(),'EXCLUSIVE_NEW_AUDIT')
        advance('construction');q=a.AcceptanceReader(root,epochs.check)
        for pin in (PLAN,EPOCH,plan.PUBLISHER,*plan.GUARDS):a.exact(q.pin(pin['path']),pin,'EXACT_BOOTSTRAP_SOURCE_BYTES')
        q.pin(SELF);q.pin(loader.SELF)
        context=NS(shared=None);construction={};context.row=construction
        options=NS(inspect_shared=True,inspect_oracle=True,metadata_generation=args.generation)
        plan.construct(root,q,a,loader,scope,bytes_policy,options,construction,context)
        resources=context.oracle_result
        optimized=context.admission.optimized_reader(root,q,resources.known,resources.loader,a.AcceptanceReader,a)
        Reader=optimized.Reader
        q.finish();epochs.check(force=True);epochs.bind(context)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'FULL_ACTUAL_CONSTRUCTION_CLOSING')
        owner=context.data.planned.batch;whole=context.batch.plain(owner.whole)
        binary=sum(p['bytes'] for n,p in whole.items() if n.lower().endswith('.exe'))
        other=sum(p['bytes'] for n,p in whole.items() if not n.lower().endswith('.exe'))
        nominal=len(whole)/20+binary/1048576+other/2097152
        row.update(construction=construction,source_pins=list(q.snapshots.values()),
            construction_fresh_inputs=len(q.snapshots),construction_final_fresh_hashes=q.final_fresh_hashes,
            declared_whole_inputs=len(whole),declared_whole_bytes=binary+other,whole_pin_sha256=digest(whole),
            nominal_one_whole_read_seconds=nominal,readonly_original600_per_stage=True,
            reader_optimization=dict(source=optimized.source_proof,chunk=optimized.chunk_proof))
        require(nominal<600,'DECLARED_WHOLE_READ_CANNOT_FIT_ORIGINAL600')
        advance('opening');opening=Reader(root,epochs.check);owner.begin(opening)
        row['whole_opening']=dict(fresh_inputs=opening.read_passes,bytes_read=opening.bytes_read,
            full_pin_sha256=digest(opening.snapshots),actual_complete=True)
        advance('metadata');row['metadata']=metadata(root,epochs,context,a)
        advance('closing');closing=Reader(root,epochs.check);row['whole_batch']=owner.finish(closing)
        epochs.validator(context,closed=True);epochs.check(force=True)
        require(not denied and digest(closing.snapshots)==row['whole_pin_sha256'],'ACTUAL_WHOLE_MATCH_BOTH_BOUNDARIES')
        row['whole_closing']=dict(fresh_inputs=closing.read_passes,bytes_read=closing.bytes_read,
            full_pin_sha256=digest(closing.snapshots),actual_complete=True)
        row['state']='PASS_NATIVE011_ACTUAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE'
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,NameError,ImportError,MemoryError) as error:
        epochs.broken=True;value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_METADATA_AUDIT_FAILURE')
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        if context is not None and context.shared is not None and hasattr(context.shared.batch,'shared'):
            context.shared.batch.shared.restore();row['shared_budget_restored']=context.shared.batch.shared.restored
        epochs.close();row.update(epochs=epochs.records,process_creation_attempts=len(denied),
            cleanup_confirmed=all(r['cleanup_confirmed'] for r in epochs.records),elapsed_seconds=time.monotonic()-started)
        receipt=publisher.publish(root,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),error_frames=row.get('error_frames'),
            cleanup=row['cleanup_confirmed'],metadata_inputs=row.get('metadata',{}).get('fresh_inputs'),
            whole_inputs=row.get('declared_whole_inputs'),whole_bytes=row.get('declared_whole_bytes'),
            nominal_one_whole_read_seconds=row.get('nominal_one_whole_read_seconds'),
            elapsed=row['elapsed_seconds'],receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
