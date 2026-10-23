"""Construct original scope prefix and new unopened Batch; no engine/Frame/GO."""
import ast
import copy
import io
import json
import os
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_plan_inspection.py'
TEST='tools/p09/tests/test_native011_current_epoch_plan_prefix.py'
PARENT=dict(path='tools/p09/native011_parent_plan.py',bytes=24332,
    sha256='b58c2658510f7af5824a4b54d64fe6858cd128a1ddef1e235b00bd46238c69b8')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
BOUNDARY='CONSTRUCT_REAL_RUN011_ENGINE_AND_ORIGINAL_PARENT'


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_PLAN_INSPECTION_'+code)


def scope_prefix(raw,definitions,namespace):
    found=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='construct']
    require(len(found)==1,'ONE_ORIGINAL_CONSTRUCTION_FUNCTION')
    original=found[0]
    marker=ast.dump(ast.parse("row['stage']="+repr(BOUNDARY)).body[0],include_attributes=False)
    positions=[i for i,n in enumerate(original.body) if ast.dump(n,include_attributes=False)==marker]
    require(len(positions)==1 and positions[0]>0,'EXACT_BEFORE_ENGINE_BOUNDARY')
    node=copy.deepcopy(original);prefix=node.body[:positions[0]]
    require(all(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
        for a,b in zip(prefix,original.body[:positions[0]])),'ALL_ORIGINAL_PREFIX_STATEMENTS_RETAINED')
    node.body=prefix+[ast.parse('return NS(data=data,batch=batch,delta=delta)').body[0]]
    function=definitions(ast.unparse(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))),
        ('construct',),namespace).construct
    return function,dict(original_whole_source_pin=PARENT,retained_prefix_statements=len(prefix),
        all_retained_statements_AST_identical=True,original_engine_tail_executed=False,
        whole_parent_construction_qualified=False)


def private_parent(root,q,a):
    raw=q.text(LOADER['path']);a.exact(q.snapshots[LOADER['path']],LOADER,'ORIGINAL_COMPLETE_NAMESPACE_LOADER')
    env=dict(__name__='p09_current805_scope_loader',__file__=LOADER['path'])
    exec(compile(raw,LOADER['path'],'exec'),env)
    loader=NS(**env)
    class Source:
        def __init__(self,name):self.name=name
        def __fspath__(self):return os.fspath(root/self.name)
        def open(self,mode):
            require(mode=='rb' and self.name==PARENT['path'],'ONLY_ORIGINAL_PARENT_SOURCE')
            actual,payload=q._read(self.name,parse=True);q._bind(self.name,actual)
            a.exact(actual,PARENT,'EXACT_COMPLETE_ORIGINAL_PARENT_BYTES')
            return io.BytesIO(payload)
    class Root:
        def __fspath__(self):return os.fspath(root)
        def __truediv__(self,name):return Source(name)
    namespaces,proof=loader.load(Root(),[PARENT],{})
    return namespaces.native011_parent_plan,proof


def main():
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('CURRENT805_UNOPENED_PLAN_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import current_stored_runtime_scope as scope,successor_preparation_workspace_v1 as publisher
    import owned_source_read_pressure as bytes_policy,packed_receipt_json as packed
    import native011_current_epoch_scope as epoch,native011_current_epoch_binding as binding
    import native011_current_cohort_listing as listing,native011_current_epoch_plan as projection
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import native011_source_generation_audit as audit
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_CURRENT805_ORIGINAL_BATCH_SCOPE_NOT_ENGINE',official_accepted_count=158,
        accepted_count_delta=0,GO_authorized=False,Frame_instances=0,worker_or_product_executed=False,
        actual_full_source_bytes_or_Native_qualified=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        for name in (SELF,TEST,projection.SELF,projection.TEST,scope.SELF,epoch.SELF,binding.SELF,
                     'tools/p09/native011_current_cohort_listing.py','tools/p09/packed_receipt_json.py'):q.pin(name)
        parent,loaded=private_parent(c.ROOT,q,a)
        raw=q.text(PARENT['path']);a.exact(q.snapshots[PARENT['path']],PARENT,'ORIGINAL_PREFIX_SOURCE')
        prepare,proof=scope_prefix(raw,a.native.definitions,vars(parent))
        original=prepare(c.ROOT,q,a,parent.bootstrap_loader(c.ROOT),scope,bytes_policy,
            NS(inspect_oracle=False,inspect_shared=False),row,NS(shared=None))
        before=original.data.planned
        require(len(before.history)==419 and before.batch.phase=='NEW','ORIGINAL_HISTORY419_AND_UNOPENED_BATCH')
        prior_manifest=json.dumps(original.data.manifest,sort_keys=True,separators=(',',':'))
        cohort=binding.prepare_binding(q,a,scope,epoch,listing.build_contract,packed)
        preimages=a.read_exact(q,epoch.PREIMAGES)
        controls=scope.pins([q.pin(projection.SELF),q.pin(projection.TEST)])
        projected,change,versions=projection.apply(original.data,cohort,preimages['preimages'],controls,
            original.batch,scope,epoch.CHANGED,q.checkpoint)
        after=projected.planned
        require(original.delta.digest(before.history)==original.delta.digest(after.history)
            and len(after.history)==419 and original.data.planned is before,'EXACT_ORIGINAL_HISTORY_AND_PLAN')
        require(json.dumps(projected.manifest,sort_keys=True,separators=(',',':'))==prior_manifest,
            'ENTIRE_ORIGINAL162_MANIFEST_UNMODIFIED')
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'NEW_PLAN_CONSTRUCTION_CLOSING_NO_PROCESS')
        row.update(state='PASS_ACTUAL_UNOPENED_CURRENT805_BATCH_PLAN_NOT_ENGINE_OR_NATIVE',
            original_prefix=proof,original_namespace_source_proof=loaded,source_epoch_projection=change,
            current805_original_binding_projection=cohort.projection,compiled_candidate_pin=cohort.scope.EXE_PIN,
            whole_inputs=len(after.whole),current_inputs=len(after.current),history_inputs=len(after.history),
            whole_sha256=epoch.digest(after.whole),current_sha256=epoch.digest(after.current),
            preservation_sha256=original.delta.digest(after.history),unchanged162_manifest=True,
            original_parent_engine_constructed=False,actual_Batch_class_constructed=True,
            old_metadata_source_versions_routed_to_exact_archives=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            complete_new_runtime600_readiness15_product10_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,SyntaxError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_CURRENT805_BATCH_SCOPE_FAILURE')
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),
            process_creation_attempts=len(denied),resource_summary=audit.sample_summary(g.samples))
        receipt=publisher.publish(c.ROOT,
            'implementation/p09/evidence/p09-361-native011-current805-unopened-plan001.v1.json',
            row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),
            whole=row.get('whole_inputs'),current=row.get('current_inputs'),history=row.get('history_inputs'),
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),cleanup=g.cleanup,receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
