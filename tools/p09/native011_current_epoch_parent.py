"""Original whole constructor plus explicit epoch installation; always metadata NO-GO."""
import ast
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_parent.py'
TEST='tools/p09/tests/test_native011_current_epoch_parent_projection.py'
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
HELPERS=('native011_current_epoch_scope','native011_current_epoch_binding',
    'native011_current_cohort_listing','native011_current_epoch_plan','native011_current_epoch_plan_inspection',
    'native011_current_epoch_worker_scope','native011_current_epoch_graph','native011_current_epoch_metadata',
    'native011_current_epoch_inventory_budget')
BOUNDARY='CONSTRUCT_REAL_RUN011_ENGINE_AND_ORIGINAL_PARENT'


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_PARENT_'+code)


def project_constructor(raw,definitions,namespace,install):
    found=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='construct']
    require(len(found)==1,'ONE_COMPLETE_ORIGINAL_CONSTRUCTOR')
    original=found[0];node=copy.deepcopy(original)
    marker=ast.dump(ast.parse("row['stage']="+repr(BOUNDARY)).body[0],include_attributes=False)
    positions=[i for i,n in enumerate(node.body) if ast.dump(n,include_attributes=False)==marker]
    require(len(positions)==1,'ONE_EXACT_EPOCH_INSTALLATION_POSITION')
    added=ast.parse('_epoch=_install_epoch(data,batch,q,scope)\ndata=_epoch.data\nscope=_epoch.scope\n'
        'context.current_epoch=_epoch\nrow["current805_epoch_installation"]=_epoch.proof').body
    index=positions[0];node.body[index:index]=added
    inverse=copy.deepcopy(node);del inverse.body[index:index+len(added)]
    require(ast.dump(inverse,include_attributes=False)==ast.dump(original,include_attributes=False),
        'ENTIRE_ORIGINAL_CONSTRUCTOR_AST_INVERSE')
    env=dict(namespace,_install_epoch=install)
    source=ast.unparse(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])))
    function=definitions(source,('construct',),env).construct
    return function,dict(complete_original_constructor_AST_inverse=True,explicit_added_statements=len(added),
        original_parent_Frame_worker_and_metadata_denial_statements_retained=True,
        original_scope_source_or_default_modules_mutated=False)


def private_helpers(root,q,a):
    raw=q.text(LOADER['path']);a.exact(q.snapshots[LOADER['path']],LOADER,'ORIGINAL_WHOLE_NAMESPACE_LOADER')
    env=dict(__name__='p09_current805_parent_loader',__file__=LOADER['path'])
    exec(compile(raw,LOADER['path'],'exec'),env);loader=NS(**env)
    pins=[q.pin('tools/p09/'+name+'.py') for name in HELPERS];allowed={p['path']:p for p in pins}
    class Source:
        def __init__(self,name):self.name=name
        def __fspath__(self):return os.fspath(root/self.name)
        def open(self,mode):
            require(mode=='rb' and self.name in allowed,'ONLY_NAMED_COMPLETE_PRIVATE_HELPERS')
            actual,payload=q._read(self.name,parse=True);q._bind(self.name,actual)
            a.exact(actual,allowed[self.name],'EXACT_PRIVATE_HELPER_SOURCE_BYTES');return io.BytesIO(payload)
    class Root:
        def __fspath__(self):return os.fspath(root)
        def __truediv__(self,name):return Source(name)
    return loader.load(Root(),pins,{})


def main(generation=1):
    require(type(generation) is int and generation in (1,2,3,4),'CLOSED_PARENT_GENERATION')
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('CURRENT805_PARENT_CONSTRUCTION_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import current_stored_runtime_scope as scope,owned_source_read_pressure as bytes_policy
    import packed_receipt_json as packed
    # Bootstrap only the original loaders/guards before the real source reader.
    # Every bootstrap source uses its original exact literal pin and is freshly
    # witnessed again below; no sys.modules entry is removed or masked.
    path=c.ROOT/LOADER['path'];raw=path.read_bytes()
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],
        'ORIGINAL_BOOTSTRAP_NAMESPACE_PIN')
    env=dict(__name__='p09_current805_parent_bootstrap',__file__=LOADER['path']);exec(compile(raw,LOADER['path'],'exec'),env)
    bootstrap=NS(**env)
    original_pin=dict(path='tools/p09/native011_parent_plan.py',bytes=24332,
        sha256='b58c2658510f7af5824a4b54d64fe6858cd128a1ddef1e235b00bd46238c69b8')
    modules,_=bootstrap.load(c.ROOT,[original_pin],{});parent=modules.native011_parent_plan
    source_loader=parent.bootstrap_loader(c.ROOT)
    guards,_=source_loader.load(c.ROOT,list(parent.GUARDS),{})
    host,baseline,policy,final=(getattr(guards,n) for n in ('prepared_run_closure_v1',
        'owned_cpu_baseline_v1','preparation_attributed_cpu_v1','distinct_final_sample_guard_v1'))
    publishers,_=source_loader.load(c.ROOT,[parent.PUBLISHER],{});publisher=publishers.successor_preparation_workspace_v1
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();context=NS(shared=None)
    row=dict(state='FAILED_CURRENT805_ORIGINAL_PARENT_CONSTRUCTION_NOT_NATIVE',official_accepted_count=158,
        accepted_count_delta=0,GO_authorized=False,worker_or_product_executed=False,
        actual_live_Frame_or_metadata_qualified=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        require(not (c.ROOT/f'implementation/p09/evidence/p09-361-native011-current805-parent-inspection{generation:03}.v1.json').exists(),
            'EXCLUSIVE_NEW_PARENT_INSPECTION_NO_REPLAY')
        for name in (SELF,TEST,LOADER['path'],original_pin['path']):q.pin(name)
        helpers,proof=private_helpers(c.ROOT,q,a)
        epoch,binding,listing,projection,inspection,routing,graph_scope,metadata_scope,inventory_budget=(getattr(helpers,n) for n in HELPERS)
        def install(data,batch,reader,original_scope):
            require(reader is q and original_scope is scope,'SAME_ORIGINAL_OWNER_AND_SCOPE')
            cohort=binding.prepare_binding(q,a,scope,epoch,listing.build_contract,packed)
            preimages=a.read_exact(q,epoch.PREIMAGES)
            controls=scope.pins([q.pin(projection.SELF),q.pin(projection.TEST)])
            route_controls=scope.pins([q.pin(routing.SELF),q.pin(routing.TEST)])
            if generation>=3:
                route_controls=scope.extend(route_controls,scope.pins([q.pin(graph_scope.SELF),q.pin(graph_scope.TEST),
                    q.pin(metadata_scope.SELF),q.pin(metadata_scope.TEST)]))
            if generation>=4:
                route_controls=scope.extend(route_controls,scope.pins([q.pin(inventory_budget.SELF),q.pin(inventory_budget.TEST)]))
            declared_cohort=NS(**{**vars(cohort),'required':scope.extend(cohort.required,route_controls)})
            projected,change,versions=projection.apply(data,declared_cohort,preimages['preimages'],controls,
                batch,scope,epoch.CHANGED,q.checkpoint)
            change['explicit_worker_routing_control_pins']=list(route_controls.values())
            return NS(data=projected,scope=cohort.scope,cohort=cohort,versions=versions,proof=change)
        raw=q.text(original_pin['path']);a.exact(q.snapshots[original_pin['path']],original_pin,'EXACT_COMPLETE_PARENT_CONSTRUCTOR')
        construct,projection_proof=project_constructor(raw,a.native.definitions,vars(parent),install)
        construct(c.ROOT,q,a,source_loader,scope,bytes_policy,
            NS(inspect_oracle=False,inspect_shared=False),row,context)
        prepared=context.prepared;actual=context.actual
        if generation>=2:
            row['explicit_worker_candidate_routing']=routing.route(prepared.linked,scope.EXE_PIN,
                context.current_epoch.cohort.scope.EXE_PIN,scope)
        if generation>=3:
            graph=prepared.entry.graph;cohort=context.current_epoch.cohort
            identity=NS(normalize=scope.pins,to_physical=scope.pins)
            triples=a.read_exact(q,epoch.PREIMAGES)['preimages']
            versions=projection.Versions(identity,triples,scope,epoch.CHANGED)
            graph_proof=graph_scope.attach(graph.binding,versions,scope,q.checkpoint)
            selected,_=graph.binding.semantic_union(context.data.planned.logical,q.checkpoint)
            mapping={r['semantic_original_pin']['path']:r['physical_envelope_pin']['path'] for r in graph.binding.descriptors()}
            current={n:dict(p) for n,p in selected.items() if mapping.get(n,n) in context.data.planned.current}
            physical,_=graph.binding.project(current,q.checkpoint)
            a.exact({n:dict(p) for n,p in physical.physical_pins.items()},context.data.planned.current,
                'REAL_CURRENT805_GRAPH_EXACT_CURRENT_NOT_HISTORY_OR_SUBSET')
            row['current805_actual_graph']=dict(same_binding_instance_retained=graph_proof['same_binding_instance_retained'],
                original_class_methods_retained=True,original_manifest_descriptors_unchanged=graph.binding.descriptors()==graph_proof['descriptors'],
                exact162_descriptors=len(graph.binding.descriptors()),semantic_current_inputs=len(current),
                physical_current_inputs=len(physical.physical_pins),current_physical_exact=True,
                current_source_and_archive_versions_present=True)
            original_scope_function=prepared.entry.runtime.connect_factory.__globals__.get('current_input_scope')
            require(callable(original_scope_function) and '_batch' not in original_scope_function.__globals__,
                'ORIGINAL_RUNTIME_SCOPE_BEFORE_APPROVED_POLICY')
            runtime=NS(**{**vars(prepared.entry.runtime),'current_input_scope':original_scope_function})
            view=metadata_scope.ListingView(scope,cohort.owner.listing,cohort.owner.current)
            scope_api=NS(**{**vars(cohort.scope),'listing_inputs':view.listing_inputs})
            runtime_raw=q.text(context.batch.RUNTIME).encode('utf-8')
            adapted,metadata_proof=metadata_scope.connect(runtime,runtime_raw,context.batch,context.data.planned.batch,scope_api)
            denied_reader=NS(checkpoint=q.checkpoint)
            try:adapted.current_input_scope(denied_reader,graph,prepared.entry.core['step'],None,None,{})
            except ValueError as error:require(error.args==('BATCH_VERIFY_READY_METADATA_OWNER_ONLY',),
                'ORIGINAL_UNAUDITED_METADATA_DENIED_BEFORE_IO')
            else:require(False,'METADATA_CANNOT_RUN_BEFORE_REAL_WHOLE_BEGIN')
            require(context.data.planned.batch.phase=='NEW' and not context.data.planned.batch.metadata_reader_active
                and view.calls==0,'DENIAL_NO_METADATA_READER_OR_LISTING_CONSUMPTION')
            row['current805_metadata_scope_projection']=metadata_proof
            row['actual_metadata_preaudit_denial_before_IO']=True
            raw_inventory=q.text('tools/p09/current_issuer_build_inputs.py')
            enumerator=a.native.definitions(raw_inventory,('rust_inputs',),dict(require=c.require,Path=Path,os=os))
            import locked_runtime_inputs as inventory_locks
            q.pin('tools/p09/locked_runtime_inputs.py')
            inventory_requests=[0];pacer=inventory_locks.OpenPacer(q.checkpoint,rate=20)
            def checkpoint_inventory():inventory_requests[0]+=1;pacer.reserve()
            observed=enumerator.rust_inputs(c.ROOT,checkpoint_inventory)
            require(observed==cohort.rust,'FRESH_INVENTORY_ALL805_FOR_COMPLETE_BUDGET')
            row['actual_current805_inventory_requests']=inventory_requests[0]
            original_budget=prepared.linked.engine.run_owned.__globals__['runtime_budget']
            if generation>=4:
                a.exact(q.pin(inventory_budget.SOURCE['path']),inventory_budget.SOURCE,'ORIGINAL_COMPLETE_BUDGET_SOURCE_BEFORE_DATA_BINDING')
                original_budget,budget_proof=inventory_budget.bind(original_budget,inventory_requests[0])
                row['current805_inventory_budget_identity']=budget_proof
            complete=graph.binding.runtime_budget(current,inventory_requests[0],original_budget,q.checkpoint)
            require(complete['unchanged_lock_deadline_seconds']==600 and complete['unallocated_margin_seconds']==60
                and complete['aggregate_envelope_decoder_allowance_seconds']==5.0,'ORIGINAL_COMPLETE600_MARGIN60_SHARED5')
            total=complete['predicted_runtime_combined_seconds']+15
            row['current805_complete_budget']=dict(original_complete_model=complete,
                actual_inventory_requests=inventory_requests[0],readiness_allowance_seconds=15,
                with_readiness15_seconds=total,actual_readiness_or_Runtime_qualified=False)
            require(total<600,'COMPLETE_CURRENT805_COST_PLUS_READINESS15_FITS_ORIGINAL600')
        row.update(actual_original_engine_constructed=True,actual_original_parent_constructed=True,
            preparation=prepared.proof,original_constructor_projection=projection_proof,
            current_parent_helper_count=q.worker_default_helper_count,
            parent_attempts=context.parent_state.attempts,Frame_instances=len(context.parent_state.frames))
        worker_scope=prepared.linked.original_worker.__globals__.get('scope')
        candidate=None if worker_scope is None else getattr(worker_scope,'EXE_PIN',None)
        row['actual_original_worker_candidate_pin']=None if candidate is None else dict(candidate)
        require(candidate==context.current_epoch.cohort.scope.EXE_PIN,'ORIGINAL_WORKER_USES_CURRENT805_BINARY')
        require(context.parent_state.attempts==0 and not context.parent_state.frames
            and prepared.linked.state.attempts==prepared.linked.state.calls==0
            and context.data.planned.batch.phase=='NEW','ORIGINAL_ENGINE_PARENT_UNEXECUTED')
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'ALL_PARENT_CONSTRUCTION_INPUTS_CLOSING')
        row.update(state='PASS_CURRENT805_ORIGINAL_UNOPENED_PARENT_NOT_FRAME_OR_NATIVE',
            private_complete_helper_sources=proof,whole_inputs=len(context.data.planned.whole),
            current_inputs=len(context.data.planned.current),history_inputs=len(context.data.planned.history),
            helper64_bound_retained=True,metadata_remains_explicitly_denied=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,SyntaxError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_CURRENT805_PARENT_FAILURE')
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),process_creation_attempts=len(denied),
            resource_summary=dict(count=len(g.samples),last_eight=g.samples[-8:],
                system_CPU_max=max((s['system_cpu_percent'] for s in g.samples),default=None),
                available_RAM_min=min((s['available_ram_percent'] for s in g.samples),default=None)))
        receipt=publisher.publish(c.ROOT,
            f'implementation/p09/evidence/p09-361-native011-current805-parent-inspection{generation:03}.v1.json',
            row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),
            helpers=row.get('current_parent_helper_count'),fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),
            cleanup=g.cleanup,receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__=='__main__':
    require(sys.argv[1:] in ([],['--generation2'],['--generation3'],['--generation4']),'CLOSED_PARENT_ARGUMENTS')
    raise SystemExit(main(4 if sys.argv[1:]==['--generation4'] else 3 if sys.argv[1:]==['--generation3'] else 2 if sys.argv[1:] else 1))
