"""Current805 report and original shared parent with an explicit audit hook.

The original scope prefix, report admission, shared class/owner, parent and
callback implementations are called directly. Default construction never
begins a Batch. Only the readonly preparation audit driver may invoke the
whole opening/metadata/closing; no Frame, worker or product authority exists.
"""
import hashlib
import io
import json
import os
import re
import sys
import time
import traceback
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_shared.py'
TEST='tools/p09/tests/test_native011_current_epoch_shared.py'
PARENT=dict(path='tools/p09/native011_parent_plan.py',bytes=24332,
    sha256='b58c2658510f7af5824a4b54d64fe6858cd128a1ddef1e235b00bd46238c69b8')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_SHARED_'+code)


def batch_scope_api(batch,scope_api,connector):
    """Only this private dependency slot; original shared attach code remains."""
    state=NS(calls=0,proof=None)
    def install(runtime,raw,owner):
        require(state.calls==0,'ONE_EXPLICIT_CURRENT805_SCOPE_INSTALLATION')
        state.calls+=1
        adapted,proof=connector(runtime,raw,batch,owner,scope_api)
        approved=proof['approved_three_policy_slot_proof']
        require(approved['exact_original_AST_inverse'] is True
            and proof['entire_approved_AST_inverse'] is True,'BOTH_FULL_POLICY_AND_EPOCH_AST_INVERSES')
        state.proof=proof
        return adapted,dict(approved,current805_epoch_projection=proof)
    return NS(**{**vars(batch),'install_scope':install}),state


def callback_sources(admitted,step_pin,current,scope):
    require(current.get(step_pin['path'])==step_pin,'EXACT_ALREADY_CURRENT_STEP_INPUT')
    sources=scope.extend(admitted.sources,{step_pin['path']:dict(step_pin)})
    return NS(**{**vars(admitted),'sources':sources})


def private_load(loader,root,q,a,names,reuse):
    pins=[q.pin('tools/p09/'+name+'.py') for name in names]
    allowed={p['path']:p for p in pins}
    class Source:
        def __init__(self,name):self.name=name
        def __fspath__(self):return os.fspath(root/self.name)
        def open(self,mode):
            require(mode=='rb' and self.name in allowed,'ONLY_NAMED_PRIVATE_SOURCE')
            actual,raw=q._read(self.name,parse=True);q._bind(self.name,actual)
            a.exact(actual,allowed[self.name],'FRESH_COMPLETE_PRIVATE_SOURCE')
            return io.BytesIO(raw)
    class Root:
        def __fspath__(self):return os.fspath(root)
        def __truediv__(self,name):return Source(name)
    return loader.load(Root(),pins,reuse)


def main(*,audit_driver=None):
    require(sys.argv[1:] in ([],['--cost-oracle']),'CLOSED_CONSTRUCTION_ARGUMENTS')
    with_oracle=bool(sys.argv[1:]) or audit_driver is not None
    generation=2+audit_driver.run_id if audit_driver is not None else 2 if with_oracle else 1
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('CURRENT805_SHARED_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import current_stored_runtime_scope as scope,owned_source_read_pressure as bytes_policy
    import packed_receipt_json as packed
    # Exact original bootstrap; helpers remain private, not hidden default
    # imports or additions to a union inferred from observed module activity.
    raw=(c.ROOT/LOADER['path']).read_bytes()
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_ORIGINAL_BOOTSTRAP')
    env=dict(__name__='p09_current805_shared_bootstrap',__file__=LOADER['path'])
    exec(compile(raw,LOADER['path'],'exec'),env);bootstrap=NS(**env)
    modules,_=bootstrap.load(c.ROOT,[PARENT],{});parent=modules.native011_parent_plan
    loader=parent.bootstrap_loader(c.ROOT)
    guards,_=loader.load(c.ROOT,list(parent.GUARDS),{})
    host,baseline,policy,final=(getattr(guards,name) for name in ('prepared_run_closure_v1',
        'owned_cpu_baseline_v1','preparation_attributed_cpu_v1','distinct_final_sample_guard_v1'))
    publishers,_=loader.load(c.ROOT,[parent.PUBLISHER],{});publisher=publishers.successor_preparation_workspace_v1
    host.configure_host_policy(c)
    g=audit_driver if audit_driver is not None else baseline.guard_type(
        policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=resources=context=None;started=time.monotonic()
    output=f'implementation/p09/evidence/p09-361-native011-current805-shared-parent{generation:03}.v1.json'
    row=dict(state='FAILED_CURRENT805_SHARED_PARENT_CONSTRUCTION_NOT_NATIVE',official_accepted_count=158,
        accepted_count_delta=0,GO_authorized=False,worker_or_product_executed=False,
        actual_live_Frame_or_metadata_body_qualified=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        require(not(c.ROOT/output).exists(),'EXCLUSIVE_NEW_SHARED_CONSTRUCTION')
        for name in (SELF,TEST,LOADER['path']):q.pin(name)
        a.exact(q.pin(PARENT['path']),PARENT,'ENTIRE_ORIGINAL_PREFIX_SOURCE')
        names=('native011_current_epoch_parent','native011_current_epoch_report',
            'native011_current_epoch_report_admission')
        libraries,private_proof=private_load(loader,c.ROOT,q,a,names,{})
        controls=libraries.native011_current_epoch_parent
        report=libraries.native011_current_epoch_report
        admission=libraries.native011_current_epoch_report_admission
        helpers,_=controls.private_helpers(c.ROOT,q,a)
        epoch,binding,listing,projection,inspection,routing,graph_scope,metadata_scope,inventory=(
            getattr(helpers,name) for name in controls.HELPERS)
        prepare,prefix=inspection.scope_prefix(q.text(PARENT['path']),a.native.definitions,vars(parent))
        original=prepare(c.ROOT,q,a,loader,scope,bytes_policy,
            NS(inspect_oracle=False,inspect_shared=False),row,NS(shared=None))
        cohort=binding.prepare_binding(q,a,scope,epoch,listing.build_contract,packed)
        preimages=a.read_exact(q,epoch.PREIMAGES)
        declared_names=(SELF,TEST,admission.SELF,admission.TEST,routing.SELF,routing.TEST,
            graph_scope.SELF,graph_scope.TEST,metadata_scope.SELF,metadata_scope.TEST,inventory.SELF,inventory.TEST)
        if with_oracle:
            declared_names+=('tools/p09/native011_current_epoch_runtime_cost.py',
                'tools/p09/tests/test_native011_current_epoch_runtime_cost.py','tools/p09/native011_parent_oracle.py')
        if audit_driver is not None:
            declared_names+=('tools/p09/native011_current_epoch_audit.py','tools/p09/tests/test_native011_current_epoch_audit.py')
        explicit=scope.pins([q.pin(name) for name in declared_names])
        declared_cohort=NS(**{**vars(cohort),'required':scope.extend(cohort.required,explicit)})
        fixed=scope.pins([q.pin(projection.SELF),q.pin(projection.TEST)])
        data,change,_=projection.apply(original.data,declared_cohort,preimages['preimages'],fixed,
            original.batch,scope,epoch.CHANGED,q.checkpoint)
        raw=q.text(report.SOURCE['path']).encode('utf-8');reports,report_proof=report.connect(raw)
        libraries,_=private_load(loader,c.ROOT,q,a,('native011_shared_parent',),{'native011_metadata_report':reports})
        shared=libraries.native011_shared_parent
        a.exact(q.pin(admission.SOURCE['path']),admission.SOURCE,'EXACT_ORIGINAL_SHARED_SOURCE')
        admit,admission_proof=admission.connect(shared.admit_report,reports)
        admitted=admit(c.ROOT,q,a,original.batch,data,3)
        names=('native011_preparation','native011_worker_transport','native011_zlib_binding',
            'native011_worker_preparation','batch_engine_connection')
        libraries,_=private_load(loader,c.ROOT,q,a,names,{'current_stored_runtime_scope':cohort.scope})
        entry=libraries.batch_engine_connection
        a.exact(q.pin(entry.SELF),parent.ENTRY_SOURCE,'ENTIRE_ORIGINAL_PARENT_ENTRY_SOURCE')
        prepared=libraries.native011_worker_preparation.prepare(c.ROOT,q,a,cohort.scope,bytes_policy,loader)
        linked=prepared.linked;graph=prepared.entry.graph
        row['worker_routing']=routing.route(linked,scope.EXE_PIN,cohort.scope.EXE_PIN,scope)
        versions=projection.Versions(NS(normalize=scope.pins,to_physical=scope.pins),
            preimages['preimages'],scope,epoch.CHANGED)
        graph_proof=graph_scope.attach(graph.binding,versions,scope,q.checkpoint)
        current=entry.current_logical(data,graph.binding,q.checkpoint,scope,a.exact)
        row['current805_graph_exact_current']=True
        def metadata_unavailable(reader):
            q.checkpoint();require(False,'WHOLE_AUDIT_REQUIRED_BEFORE_METADATA')
        linked.engine.run_owned.__globals__['binding']=metadata_unavailable
        resources=shared.prepare(c.ROOT,q,a,loader,original.batch,data,prepared,entry)
        actual,state=data.planned.batch.connect_parent(linked.engine,graph)
        view=metadata_scope.ListingView(scope,cohort.owner.listing,cohort.owner.current)
        epoch_api=NS(**{**vars(cohort.scope),'listing_inputs':view.listing_inputs})
        batch_api,installed=batch_scope_api(original.batch,epoch_api,metadata_scope.connect)
        step_pin=libraries.native011_worker_preparation.STEP
        a.exact(q.pin(step_pin['path']),step_pin,'FRESH_ALREADY_DECLARED_METADATA_STEP')
        callback_admitted=callback_sources(admitted,step_pin,data.planned.current,scope)
        bound=shared.attach(c.ROOT,q,a,batch_api,data,prepared,actual,entry,resources,callback_admitted)
        row['explicit_metadata_step_pin']=dict(step_pin)
        require(installed.calls==1 and view.calls==0,'ONE_DENIED_CALLBACK_NO_LISTING_OR_METADATA_BODY')
        require(state.attempts==0 and state.frames==[] and linked.state.attempts==linked.state.calls==0
            and resources.batch.phase=='NEW' and actual.worker is linked.original_worker,
            'ACTUAL_SHARED_PARENT_WORKER_UNEXECUTED')
        require(data.planned.history==original.data.planned.history and len(data.planned.history)==419,
            'ALL_HISTORY419_PINS_RETAINED')
        if with_oracle:
            libraries,_=private_load(loader,c.ROOT,q,a,
                ('native011_current_epoch_runtime_cost','native011_parent_oracle'),{})
            costs=libraries.native011_current_epoch_runtime_cost
            original_oracle=libraries.native011_parent_oracle
            raw=q.text('tools/p09/current_issuer_build_inputs.py')
            enumerator=a.native.definitions(raw,('rust_inputs',),dict(require=c.require,Path=parent.Path,os=os))
            import locked_runtime_inputs as locks
            q.pin('tools/p09/locked_runtime_inputs.py')
            requests=[0];pacer=locks.OpenPacer(q.checkpoint,rate=20)
            def count():requests[0]+=1;pacer.reserve()
            observed=enumerator.rust_inputs(c.ROOT,count)
            require(observed==cohort.rust,'FRESH_ENTIRE805_DIRECTORY_INVENTORY')
            a.exact(q.pin(inventory.SOURCE['path']),inventory.SOURCE,'ENTIRE_ORIGINAL_BUDGET_SOURCE')
            direct,engine_cost=costs.connect_engine(linked.engine,linked.window.DIRECT,requests[0],inventory.bind)
            # The original builder returned a private namespace. Keep that old
            # namespace intact; the unopened connection uses this named copy.
            linked.window=NS(**{**vars(linked.window),'DIRECT':direct})
            oracle,oracle_cost=costs.oracle_connection(original_oracle,requests[0])
            oracle_evidence={}
            checked=oracle.connect(c.ROOT,q,a,loader,original.batch,data,prepared,actual,entry,oracle_evidence)
            checker_direct,checker_cost=costs.connect_checker(checked.checker,requests[0],inventory.bind)
            engine_model=graph.binding.runtime_budget(current,requests[0],direct.runtime_budget,q.checkpoint)
            checker_model=graph.binding.runtime_budget(current,requests[0],checker_direct.runtime_budget,q.checkpoint)
            a.exact(engine_model,checker_model,'ACTUAL_ENGINE_AND_INDEPENDENT_CHECKER_SAME_ENTIRE_COST')
            a.exact(oracle_evidence['budget']['original_complete_cost'],engine_model,'ORIGINAL_DECLARED_COST_SAME_MODEL')
            require(oracle_evidence['independent_checker_connected'] is True
                and oracle_evidence['checker_body_or_candidate_executed'] is False
                and not checked.checker.projectors and state.attempts==0 and not state.frames
                and linked.state.attempts==linked.state.calls==0,'ORIGINAL_CHECKER_CONNECTED_UNEXECUTED')
            row.update(actual_inventory_requests=requests[0],engine_cost_dependency=engine_cost,
                checker_cost_dependency=checker_cost,oracle_cost_projection=oracle_cost,
                oracle_construction=oracle_evidence,complete_runtime_model=engine_model,
                actual_engine_and_checker_same_complete_model=True)
        if audit_driver is not None:
            context=NS(data=data,batch=original.batch,prepared=prepared,bound=bound,shared=resources,
                oracle_result=checked,row=row)
            audit_driver.prepare(c.ROOT,q,a,loader,entry,context,private_load,publisher)
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'SHARED_CONSTRUCTION_CLOSING_BYTES')
        if audit_driver is not None:row.update(audit_driver.run(c.ROOT,q,context,a))
        row.update(state='PASS_CURRENT805_SHARED_PARENT_CALLBACK_CONSTRUCTION_NOT_NATIVE',
            source_projection=change,original_prefix=prefix,report_admission=admitted.proof,
            original_admission_dependency=admission_proof,shared_parent_connection=bound.proof,
            current805_metadata_projection=installed.proof,explicit_private_sources=private_proof,
            whole_inputs=len(data.planned.whole),current_inputs=len(data.planned.current),history_inputs=419,
            parent_attempts=state.attempts,Frame_instances=0,worker_attempts=0,worker_calls=0,
            current_parent_helper_count=q.worker_default_helper_count,
            original162_descriptors_retained=len(graph.binding.descriptors())==162
                and graph.binding.descriptors()==graph_proof['descriptors'],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_shared_decoder5_or_readiness15_qualified=False,actual_whole_corpus_bytes_qualified=False)
        if audit_driver is not None:
            row.update(state='PASS_CURRENT805_ACTUAL_METADATA_WHOLE_BOUNDARIES_NOT_NATIVE',
                actual_whole_corpus_bytes_qualified=True,actual_metadata_body_qualified=True,
                actual_Native_Frame_created=False,actual_product_executed=False)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,SyntaxError,ImportError,MemoryError) as error:
        if audit_driver is not None:audit_driver.fail()
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_CURRENT805_SHARED_FAILURE',
            error_frames=[dict(file=os.path.basename(f.filename),function=f.name,line=f.lineno)
                for f in traceback.extract_tb(error.__traceback__)[-5:]])
        if isinstance(error,KeyError) and type(value) is str and value.startswith(('tools/p09/','implementation/p09/')):
            row['missing_declared_project_key']=value
    finally:
        if resources is not None and hasattr(resources.batch,'shared'):
            resources.batch.shared.restore();row['shared_budget_restored']=resources.batch.shared.restored
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),process_creation_attempts=len(denied),
            resource_summary=dict(count=len(g.samples),last_eight=g.samples[-8:],
                system_CPU_max=max((s['system_cpu_percent'] for s in g.samples),default=None),
                available_RAM_min=min((s['available_ram_percent'] for s in g.samples),default=None)))
        if audit_driver is not None:row.update(audit_driver.report(context))
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),error_frames=row.get('error_frames'),
            whole=row.get('whole_inputs'),current=row.get('current_inputs'),history=row.get('history_inputs'),
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),cleanup=g.cleanup,receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
