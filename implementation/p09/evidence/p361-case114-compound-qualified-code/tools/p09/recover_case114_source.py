"""Independent full source closing AFTER preserved114's passed product body.

The original failed root stays failed/CLOSED. No product/Job/GO replay. A new
Native frame rereads ALL inherited1750 inputs plus the new complete closure,
then verifies actual held identities and closes every handle. This is a distinct
source epoch, not retroactive original-frame identity or standalone queue PASS.
"""
import ast
import copy
import json
from pathlib import Path
import re
import sys
import threading
import time
from types import SimpleNamespace as NS
from unittest.mock import patch

import accept_case114_current_epoch as candidate

a=candidate.original.original
r=candidate.runtime
native=r.native
SELF='tools/p09/recover_case114_source.py'
TEST='tools/p09/tests/test_recover_case114_source.py'
OUTPUT='implementation/p09/evidence/p09-361-case114-independent-source-recovery001.v1.json'
PASS='PASS_INDEPENDENT_CURRENT114_SOURCE_AFTER_PASSED_BODY_NOT_RUNTIME_OR_GATE'
BODY_PIN=dict(path='implementation/p09/evidence/p09-361-case114-current-runtime-run001.v1.json',
    bytes=2061087,sha256='59d337ea82f6357bbe006f7508c61298ca983d7fb409cc896748c5990ea6e71f')


def require(ok,code):
    if not ok:raise ValueError('RECOVER114_'+code)


def eligible_mechanics(node):
    node=candidate.mechanics_projection(node)
    baseline=ast.dump(node,include_attributes=False);changed=[]
    def replace(old,new):
        new._eligible_before=copy.deepcopy(old);return new
    for call in ast.walk(node):
        if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) or call.func.id!='fields' or len(call.args)!=3:continue
        label=call.args[2]
        if not isinstance(label,ast.Constant):continue
        mapping={}
        if label.value=='CANDIDATE':
            mapping=dict(state='STOPPED_NOT_ACCEPTED',Native_source_frame_qualified=False,
                current_generation_runtime_candidate_qualified=False,
                closing_error_code='CPU_SAMPLE_INTERVAL_MISSING',stop_reason='CPU_SAMPLE_INTERVAL_MISSING')
        elif label.value=='FRAME':
            mapping=dict(frame_state='CLOSED',original_owned_cleanup_confirmed_before_release=False)
        if mapping:
            keywords={k.arg:k for k in call.args[1].keywords}
            require(set(mapping)<=set(keywords),'EXACT_ELIGIBILITY_METADATA')
            for key,value in mapping.items():
                k=keywords[key];k.value=replace(k.value,ast.parse(repr(value),mode='eval').body);changed.append(key)
        elif label.value=='FINAL_IDENTITIES':
            # Missing original identities are REQUIRED for this special recovery
            # path, never manufactured or silently ignored as a complete frame.
            old=copy.deepcopy(call)
            call.func=ast.Name(id='exact',ctx=ast.Load())
            call.args=[call.args[0],ast.Constant(None),ast.Constant('MISSING_FINAL_IDENTITY_REQUIRES_INDEPENDENT_RECOVERY')]
            call._eligible_before=old;changed.append('missing_final_identity')
        elif label.value=='HANDLE_CLEANUP':
            keywords={k.arg:k for k in call.args[1].keywords};k=keywords['handle_metadata_checks']
            require(ast.dump(k.value,include_attributes=False)==ast.dump(ast.parse('2*held+2*n',mode='eval').body,include_attributes=False),
                'EXACT_MISSING_FINAL_IDENTITY_COUNT')
            k.value=replace(k.value,ast.parse('held+2*n',mode='eval').body);changed.append('missing_final_metadata_count')
    post=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
        and n.func.id=='resource_history' and len(n.args)==2
        and ast.dump(n.args[0],include_attributes=False)==ast.dump(ast.parse("row['post_Job_cleanup_resource_samples']",mode='eval').body,include_attributes=False)]
    require(len(post)==1,'ONE_POST_RESOURCE_HISTORY')
    old=copy.deepcopy(post[0]);post[0].func=ast.Name(id='exact',ctx=ast.Load())
    post[0].args=[post[0].args[0],ast.List(elts=[],ctx=ast.Load()),ast.Constant('MISSING_POST_SAMPLES_REQUIRE_INDEPENDENT_RESOURCE_EVIDENCE')]
    post[0]._eligible_before=old;changed.append('missing_post_samples')
    require(len(changed)==10 and len(set(changed))==10,'TEN_EXACT_FAILURE_ELIGIBILITY_EXPECTATIONS')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_eligible_before'):return copy.deepcopy(n._eligible_before)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==baseline,'ALL_OTHER_ORIGINAL_ORACLE_REQUIREMENTS_RETAINED')
    return node


def eligible(q):
    body=a.read_exact(q,BODY_PIN)
    listing=a.read_exact(q,a.scope.LIST_PIN);oldbody=a.read_exact(q,a.BODY_PIN)
    fresh=a.packed.unpack(a.read_exact(q,a.FRESH_PIN),q.checkpoint)
    parent=a.read_exact(q,r.PRIOR_ACCEPT_PIN)
    a.fields(parent,dict(state=candidate.original.PASS,accepted_count_after=107,next_runtime_index=114,
        accepted_count_delta=1,resource_cleanup_confirmed=True,P09_gate='OPEN'),'UNCHANGED_PRIOR107')
    project,proof=candidate.projection(candidate.read_source(q,candidate.ACCEPTOR_PIN),'validator')
    project.__globals__['mechanics_projection']=eligible_mechanics
    check,oracle_proof=project(candidate.read_source(q,candidate.original.ORACLE_PIN),body,listing,oldbody)
    evidence=check(body,listing,oldbody,fresh,q.checkpoint)
    candidate.retained_evidence(body)
    a.exact(len(body['source_freeze']),1750,'WHOLE_ORIGINAL114_NOT_A_FIXTURE')
    proof.update(complete_product_and_before_after_checks_preserved=True,
        eligibility_is_not_complete_candidate_acceptance=True,
        missing_original_final_identity_and_post_samples_explicitly_required=True,
        original_validator_projection=oracle_proof)
    return body,listing,evidence,proof


def pin_closure(q,body):
    inherited=a.scope.pins(body['source_freeze'],1750)
    for name in (r.SELF,r.TEST,native.SELF,native.TEST):
        a.exact(q.pin(name),inherited[name],'UNCHANGED_ACTUAL114_RUNTIME_SOURCE')
        archive='implementation/p09/evidence/p361-case114-failed001-code/'+name
        a.exact(q.pin(archive),dict(inherited[name],path=archive),'EXACT_FAILED114_CODE_PREIMAGE')
    for pin in body['bootstrap_metadata']['input_pins']:
        a.exact(q.pin(pin['path']),pin,'ALL_INHERITED_BOOTSTRAP_BYTES_UNCHANGED')
    names={SELF,TEST}
    for module in tuple(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            path=Path(path).absolute()
            if path.is_relative_to(a.c.ROOT/'tools/p09') and path.suffix=='.py':
                names.add(path.relative_to(a.c.ROOT).as_posix())
    require(len(names)<=64,'COMPLETE_IMPORTED_HELPER_BOUND')
    for name in sorted(names):q.pin(name)
    return a.scope.extend(inherited,q.snapshots),sorted(names)


def run():
    destination=a.c.ROOT/OUTPUT
    require(not destination.exists() and not destination.is_symlink(),'IMMUTABLE_FRESH_OUTPUT')
    started=time.monotonic();guard=None;q=None;frame=None;api=None;body=None
    state='NOT_RUN';stop=None;phase='admission';complete=False;frame_clean=True;PDH_clean=True
    objects=[];source_guards=[];inventories=[];expected=None;budget=None;proof=None;evidence=None
    windows=r.stable.attribution.windows_type(a.c.Windows,objects)
    try:
        with patch.object(a.c,'Windows',windows):guard=a.Guard()
        guard.acquire()
        def checkpoint():
            require(time.monotonic()-started<600,'ORIGINAL_GLOBAL600_NOT_EXTENDED')
            guard.check()
        phase='eligible_body_and_source_closure';q=a.AcceptanceReader(a.c.ROOT,checkpoint)
        body,listing,evidence,proof=eligible(q)
        api=native.load(q,14,a.c)
        expected,imports=pin_closure(q,body)
        rust={n for n in a.scope.listing_inputs(listing) if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==787,'WHOLE_CURRENT_RUST787')
        pacer=r.stable.prior.build.QueryPacer(checkpoint)
        require(r.stable.prior.build.base.inputs.rust_inputs(a.c.ROOT,pacer.reserve)==rust,'CURRENT_WHOLE_RUST_INVENTORY')
        inventories.append(pacer.summary())
        base=native.model(expected,pacer.requests)
        metadata_elapsed=time.monotonic()-started
        final_metadata_nominal=sum(p['bytes']/(1048576 if n.lower().endswith('.exe') else 2097152)
            for n,p in q.snapshots.items())+len(q.snapshots)/20
        total=base['predicted_runtime_combined_seconds']+metadata_elapsed+final_metadata_nominal+.5
        require(total<600,'COMPLETE_GLOBAL_RECOVERY_BUDGET')
        budget=dict(base,measured_pre_Native_bootstrap_elapsed_seconds=metadata_elapsed,
            post_Native_fresh_metadata_nominal_seconds=final_metadata_nominal,
            final_distinct_sample_wait_allowance_seconds=.5,predicted_global_recovery_seconds=total,
            original_global_limit_seconds=600,original_native_limit_seconds=600,
            original_unused_product_allowance_not_removed=True)
        owner=NS(lock=threading.Lock(),samples=guard.samples,checkpoint_io=checkpoint)
        context=NS(phase='metadata_hash')
        early=api.EarlySourceCheckpoint(checkpoint,owner)
        class ProgressLocks(api.InputLocks):
            def take(self,*args,**kwargs):
                value=super().take(*args,**kwargs)
                if len(self.owned)%210==1:print(json.dumps(dict(stage='native_acquisition',completed=len(self.owned),case=114,product_replay=False)),flush=True)
                return value
        held=ProgressLocks(a.c.ROOT,early,owner,context)
        frame=native.frames.Frame(native.frames.Registry(),expected,early,held=held)
        phase='native_acquisition';held.mark('before_acquire');frame.acquire();held.mark('after_acquire')
        def factory(callback):return r.stable.prior.BoundaryReader(a.c.ROOT,callback,owner=owner,api=api)
        phase='before_bytes';api.read_with_held_path_guards(frame,factory,checkpoint,source_guards)
        print(json.dumps(dict(stage='whole_before_bytes',completed=len(expected),product_replay=False)),flush=True)
        context.phase='final_fresh_hash';phase='after_bytes'
        api.read_with_held_path_guards(frame,factory,checkpoint,source_guards)
        print(json.dumps(dict(stage='whole_after_bytes',completed=len(expected),product_replay=False)),flush=True)
        pacer=r.stable.prior.build.QueryPacer(checkpoint)
        require(r.stable.prior.build.base.inputs.rust_inputs(a.c.ROOT,pacer.reserve)==rust,'FINAL_WHOLE_RUST_INVENTORY')
        require(pacer.requests==inventories[0]['requests'],'WHOLE_INVENTORY_PACING_COUNT')
        inventories.append(pacer.summary())
        phase='independent_identity_after_preserved_owned_cleanup'
        held.mark('before_release')
        frame.commit(body)  # REAL immutable prior Job cleanup, no synthetic Job.
        require(frame.state=='COMMITTED','NEW_SOURCE_FRAME_COMMITTED')
        # Record this argument's temporal boundary explicitly: product did NOT
        # execute in this independent source frame. Original failed identities
        # remain missing; these are NEW real Native identities after cleanup.
        phase='fresh_metadata_and_distinct_final_sample';q.finish()
        checkpoint();time.sleep(.5);guard.check(force=True);checkpoint()
        a.resource_history(guard.samples)
        complete=True;state=PASS;phase='completed'
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        state='STOPPED_INDEPENDENT_RECOVERY_NOT_ACCEPTED'
        stop=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z0-9_]{1,256}',str(error)) else 'REDACTED_SOURCE_RECOVERY_FAILURE'
    finally:
        if frame is not None:frame_clean=frame.close()
        if guard is not None:guard.close()
        PDH_clean=r.stable.attribution.close(objects)
    ready=complete and frame_clean and PDH_clean and guard is not None and guard.cleanup
    if complete and not ready:state='STOPPED_SOURCE_CLEANUP_NOT_ACCEPTED';stop='SOURCE_OR_PDH_CLEANUP_FAILED'
    row=dict(schema_version='hwpx-agent.p09-case114-independent-source-recovery/v1',state=state,phase=phase,
        stop_reason=stop,preserved_failed_product_body_pin=BODY_PIN,prior_queue_authority_pin=r.PRIOR_ACCEPT_PIN,
        selected_test_index=114,selected_test_name=r.CASE,product_child_or_Job_executed=False,
        product_body_replayed=False,actual_product_executed_inside_new_source_frame=False,
        original_failed_root_state_rewritten=False,original_final_identities_retroactively_fabricated=False,
        ready_for_strict_distinct_compound_acceptance=ready,queue_advance=0,
        original_inherited_input_count=1750,original_all_inherited_bytes_preserved=True,
        inherited_source_pins=body['source_freeze'] if body else [],
        complete_source_pins=list(expected.values()) if expected else [],
        source_frame=frame.summary() if frame else None,source_path_guard_diagnostics=source_guards,
        eligible_body_oracle_validation=evidence,eligible_body_projection=proof,
        complete_recovery_budget=budget,bootstrap_input_pins=list(q.snapshots.values()) if q else [],
        imported_source_paths=imports if expected else [],current_Rust_input_count=787,
        current_Rust_inventory_observations=inventories,resource_samples=guard.samples if guard else [],
        serial_CPU_attribution=r.stable.attribution.summary(objects),
        metadata_read_passes=q.read_passes if q else 0,metadata_bytes_read=q.bytes_read if q else 0,
        metadata_final_fresh_hashes=q.final_fresh_hashes if q else 0,
        cleanup_confirmed=frame_clean and PDH_clean and bool(guard and guard.cleanup),
        elapsed_seconds=time.monotonic()-started,sole_original_serial_sampler=True,parallel_observer=False,
        Native_product_single_frame_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',P10_started=False,PC_freeze_resolved=False)
    with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,ensure_ascii=True,indent=2)
    print(json.dumps(dict(state=state,ready=ready,stop_reason=stop,cleanup_confirmed=row['cleanup_confirmed'],
        product_replay=False,accepted_delta=0)))
    return 0 if ready else 2


if __name__=='__main__':raise SystemExit(run())
