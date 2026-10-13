"""Accept114 once from two DISTINCT immutable, actually checked epochs.

The failed original product root stays failed, with its missing final identity.
The independent source root must contain two complete real Native reads and
final identities. This never claims the product ran inside that new frame.
No product/Job/Native replay, no source exclusion or resource-policy relaxation.
"""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import time

import recover_case114_source as s

a=s.a
SELF='tools/p09/accept_case114_compound_epoch.py'
TEST='tools/p09/tests/test_case114_compound_epoch.py'
OUTPUT='implementation/p09/evidence/p09-361-case114-compound-epoch-accept001.v1.json'
SOURCE_PIN=dict(path='implementation/p09/evidence/p09-361-case114-independent-source-recovery001.v1.json',
    bytes=2340585,sha256='14aafb6d996ca85da42e9fdf9faca34d6c79cc99ff092ebd3c83f534e64900b7')
PASS='PASS_EXACT114_DISTINCT_BODY_AND_SOURCE_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE'


def require(ok,code):
    if not ok:raise ValueError('COMPOUND114_'+code)


def finite(value,low=0,high=600):
    return type(value) in (int,float) and math.isfinite(value) and low<=value<high


def source_validator(raw,expected):
    """Retain the WHOLE original source-check block, never the product block.

    The original product block is checked separately by s.eligible. This is
    an explicit distinct-source validator, not a projected full-runtime PASS.
    Physical duplicate accounting uses the reviewed retained-stream projection.
    Only original fixed ancestry metadata is bound to the lossless NEW scope.
    """
    pin=s.candidate.original.ORACLE_PIN
    require(type(raw) is bytes and len(raw)==pin['bytes']
        and hashlib.sha256(raw).hexdigest()==pin['sha256'],'ORIGINAL_SOURCE_ORACLE_PIN')
    tree=ast.parse(raw.decode('utf-8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate']
    require(len(nodes)==1,'ONE_ORIGINAL_VALIDATOR')
    node=s.candidate.mechanics_projection(copy.deepcopy(nodes[0]))
    start=[i for i,n in enumerate(node.body) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='total' for t in n.targets)]
    end=[i for i,n in enumerate(node.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
        and isinstance(n.value.func,ast.Name) and n.value.func.id=='fields'
        and len(n.value.args)==3 and isinstance(n.value.args[2],ast.Constant) and n.value.args[2].value=='TERMINAL']
    require(len(start)==len(end)==1 and start[0]<end[0],'CLOSED_WHOLE_SOURCE_SECTION')
    block=copy.deepcopy(node.body[start[0]:end[0]])
    before=ast.dump(ast.Module(body=block,type_ignores=[]),include_attributes=False)
    counts=[n for item in block for n in ast.walk(item) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Name) and n.func.id=='exact' and len(n.args)==3
        and isinstance(n.args[2],ast.Constant) and n.args[2].value=='COMPLETE_ANCESTRY']
    require(len(counts)==1 and isinstance(counts[0].args[1],ast.Constant)
        and type(counts[0].args[1].value) is int and counts[0].args[1].value==335,'ONE_ORIGINAL_ANCESTRY_COUNT')
    count=counts[0];old=copy.deepcopy(count.args[1])
    directories=len({p.as_posix() for n in expected for p in PurePosixPath(n).parents})
    count.args[1]=ast.Constant(directories)
    restored=copy.deepcopy(block)
    for item in restored:
        for call in ast.walk(item):
            if (isinstance(call,ast.Call) and len(call.args)==3 and isinstance(call.args[2],ast.Constant)
                and call.args[2].value=='COMPLETE_ANCESTRY'):call.args[1]=copy.deepcopy(old)
    require(ast.dump(ast.Module(body=restored,type_ignores=[]),include_attributes=False)==before,
        'ALL_ORIGINAL_SOURCE_PREDICATES_RETAINED')
    function=ast.parse('def check_source(row,expected,checkpoint):\n    pass').body[0]
    function.body=block
    namespace=dict(a.__dict__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),pin['path'],'exec'),namespace)
    return namespace['check_source'],dict(original_whole_source_predicates_retained=True,
        fixed_ancestry_metadata_bound_to_complete_new_scope=True,original_source_oracle_pin=pin,
        physical_duplicate_expectations=3,product_checks_not_claimed_inside_new_source_frame=True)


def validate_source(row,body,raw,checkpoint=lambda:None):
    a.fields(row,dict(schema_version='hwpx-agent.p09-case114-independent-source-recovery/v1',state=s.PASS,
        phase='completed',stop_reason=None,preserved_failed_product_body_pin=s.BODY_PIN,
        prior_queue_authority_pin=s.r.PRIOR_ACCEPT_PIN,selected_test_index=114,selected_test_name=s.r.CASE,
        product_child_or_Job_executed=False,product_body_replayed=False,
        actual_product_executed_inside_new_source_frame=False,original_failed_root_state_rewritten=False,
        original_final_identities_retroactively_fabricated=False,ready_for_strict_distinct_compound_acceptance=True,
        queue_advance=0,original_inherited_input_count=1750,original_all_inherited_bytes_preserved=True,
        current_Rust_input_count=787,cleanup_confirmed=True,sole_original_serial_sampler=True,
        parallel_observer=False,Native_product_single_frame_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',P10_started=False,PC_freeze_resolved=False),'DISTINCT_SOURCE_ROOT')
    inherited=a.scope.pins(body['source_freeze'],1750)
    a.exact(a.scope.pins(row['inherited_source_pins'],1750),inherited,'COMPLETE_INHERITED1750')
    bootstrap=a.scope.pins(row['bootstrap_input_pins'])
    expected=a.scope.extend(inherited,bootstrap)
    a.exact(a.scope.pins(row['complete_source_pins']),expected,'WHOLE_NEW_SOURCE_CLOSURE')
    imports=row['imported_source_paths']
    require(type(imports) is list and 0<len(imports)<=64 and imports==sorted(set(imports))
        and all(type(n) is str and n.startswith('tools/p09/') and n.endswith('.py') and n in bootstrap for n in imports)
        and {s.SELF,s.TEST}<=set(imports),'COMPLETE_NEW_IMPORTED_CLOSURE')
    for pin in body['bootstrap_metadata']['input_pins']:
        a.exact(bootstrap.get(pin['path']),pin,'OLD_BOOTSTRAP_NOT_REBASED')
    for name in (s.r.SELF,s.r.TEST,s.native.SELF,s.native.TEST):
        a.exact(bootstrap.get(name),inherited[name],'ACTUAL_BODY_RUNTIME_UNCHANGED')
        name_archive='implementation/p09/evidence/p361-case114-failed001-code/'+name
        a.exact(bootstrap.get(name_archive),dict(inherited[name],path=name_archive),'FAILED_CODE_PREIMAGE')
    check,proof=source_validator(raw,expected);check(row,expected,checkpoint)
    # Supplementary retained-stream/acquisition/PDH predicates from the current
    # reviewed validator. This proxy changes FIELD NAMES only, no observations.
    proxy=dict(source_frame=row['source_frame'],source_freeze=row['complete_source_pins'],
        complete_runtime_budget=row['complete_recovery_budget'],serial_CPU_attribution=row['serial_CPU_attribution'])
    s.candidate.retained_evidence(proxy)
    inventory=row['current_Rust_inventory_observations']
    require(type(inventory) is list and len(inventory)==2,'TWO_WHOLE_RUST_INVENTORIES')
    for value in inventory:
        a.fields(value,dict(request_limit_per_second=20,requests=167,requests_skipped=False,cleanup_paced=False),'RUST787')
    budget=row['complete_recovery_budget'];model=s.native.model(expected,167)
    a.fields(budget,model,'EXACT_COMPLETE_SERIAL_COST')
    a.fields(budget,dict(final_distinct_sample_wait_allowance_seconds=.5,
        original_global_limit_seconds=600,original_native_limit_seconds=600,
        original_unused_product_allowance_not_removed=True),'NO_DEADLINE_OR_MARGIN_RELAXATION')
    before=budget['measured_pre_Native_bootstrap_elapsed_seconds']
    require(finite(before),'PRE_NATIVE_ELAPSED')
    nominal=sum(p['bytes']/(1048576 if n.lower().endswith('.exe') else 2097152) for n,p in bootstrap.items())+len(bootstrap)/20
    a.exact(budget['post_Native_fresh_metadata_nominal_seconds'],nominal,'COMPLETE_FINAL_METADATA_COST')
    total=model['predicted_runtime_combined_seconds']+before+nominal+.5
    a.exact(budget['predicted_global_recovery_seconds'],total,'EXACT_GLOBAL_COST')
    require(finite(total) and finite(row['elapsed_seconds']),'ORIGINAL_GLOBAL600')
    require(type(row['metadata_read_passes']) is int and row['metadata_read_passes']>=2*len(bootstrap)
        and type(row['metadata_bytes_read']) is int and row['metadata_bytes_read']>=2*sum(p['bytes'] for p in bootstrap.values()),
        'ALL_BOOTSTRAP_FIRST_AND_FRESH_READS')
    a.exact(row['metadata_final_fresh_hashes'],len(bootstrap),'ALL_CLOSING_FRESH_METADATA')
    a.resource_history(row['resource_samples'])
    checkpoint()
    return expected,dict(proof,whole_source_count=len(expected),whole_source_bytes=sum(p['bytes'] for p in expected.values()),
        actual_full_byte_passes=2,final_real_Native_identities_complete=True,
        product_and_source_epochs_distinct=True,original_failed_body_not_promoted=True)


def prepare(q):
    require(type(SOURCE_PIN) is dict,'ACTUAL_COMPLETED_INDEPENDENT_SOURCE_PIN_REQUIRED')
    require(SOURCE_PIN.get('path')==s.OUTPUT,'EXACT_INDEPENDENT_SOURCE_PATH')
    body,listing,body_evidence,body_proof=s.eligible(q)
    require(listing['source_test_names'][113]==s.r.CASE,'EXACT_FULL249_NEXT114')
    source=a.read_exact(q,SOURCE_PIN)
    raw=s.candidate.read_source(q,s.candidate.original.ORACLE_PIN)
    expected,source_evidence=validate_source(source,body,raw,q.checkpoint)
    # Independent verifier's own complete imported closure and test are covered
    # by its actual Native bytes, and must also match the live qualifier reads.
    for name in source['imported_source_paths']:
        a.exact(q.pin(name),expected[name],'CURRENT_SOURCE_RECOVERY_CONTROLLER_DRIFT')
    return source,body,listing,expected,dict(body=body_evidence,body_projection=body_proof,source=source_evidence)


def run():
    destination=a.c.ROOT/OUTPUT
    require(not destination.exists() and not destination.is_symlink(),'IMMUTABLE_ACCEPT_ALREADY_EXISTS')
    started=time.monotonic();guard=None;q=None;result=None;stop=None
    try:
        guard=a.Guard();guard.acquire();q=a.AcceptanceReader(a.c.ROOT,guard.check)
        source,body,listing,expected,validation=prepare(q)
        current=a.scope.listing_inputs(listing)
        rust={n for n in current if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==787,'ALL_CURRENT_RUST787')
        pacer=s.r.stable.prior.build.QueryPacer(guard.check)
        enumerate_rust=s.r.stable.prior.build.base.inputs.rust_inputs
        require(enumerate_rust(a.c.ROOT,pacer.reserve)==rust,'FRESH_COMPLETE_RUST_INVENTORY')
        inventories=[pacer.summary()]
        names=rust|set(source['imported_source_paths'])|set(body['imported_worker_source_paths'])|{a.scope.EXE_PIN['path']}
        for name in sorted(names):a.exact(q.pin(name),expected[name],'FRESH_CURRENT_EPOCH_INPUT_DRIFT')
        imported={SELF,TEST}
        for module in tuple(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path:
                path=Path(path).absolute()
                if path.is_relative_to(a.c.ROOT/'tools/p09') and path.suffix=='.py':
                    imported.add(path.relative_to(a.c.ROOT).as_posix())
        require(len(imported)<=64,'COMPLETE_QUALIFIER_IMPORTED_CLOSURE_BOUND')
        for name in sorted(imported):
            pin=q.pin(name)
            if name in expected:a.exact(pin,expected[name],'NO_IMPORTED_SOURCE_REBASE')
            else:require(name in (SELF,TEST),'NO_UNQUALIFIED_NEW_DEPENDENCY')
        q.finish()
        pacer=s.r.stable.prior.build.QueryPacer(guard.check)
        require(enumerate_rust(a.c.ROOT,pacer.reserve)==rust,'FINAL_COMPLETE_RUST_INVENTORY')
        inventories.append(pacer.summary())
        for value in inventories:
            a.fields(value,dict(request_limit_per_second=20,requests=167,requests_skipped=False,cleanup_paced=False),'QUALIFIER_RUST_PACING')
        guard.check();time.sleep(.5);guard.check(force=True)
        a.resource_history(guard.samples)
        require(time.monotonic()-started<600,'QUALIFIER_ORIGINAL_GLOBAL600')
        result=dict(schema_version='hwpx-agent.p09-case114-compound-epoch-acceptance/v1',state=PASS,
            preserved_failed_product_body_pin=s.BODY_PIN,independent_source_recovery_pin=SOURCE_PIN,
            prior_queue_authority_pin=s.r.PRIOR_ACCEPT_PIN,current_compiled_listing_pin=a.scope.LIST_PIN,
            accepted_epoch_key=s.BODY_PIN['sha256']+':114:source:'+SOURCE_PIN['sha256'],
            accepted_test_indices=[114],accepted_test_names=[s.r.CASE],accepted_count_before=107,
            accepted_count_delta=1,accepted_count_after=108,runtime_remaining_individual_cases=141,next_runtime_index=115,
            historical105_and_current112_113_epochs_preserved=True,prior_epochs_rebased_to_new_runtime=False,
            accepted_current_generation_case_count=3,acceptance_kind='distinct_preserved_body_and_independent_source',
            product_and_source_epochs_distinct=True,product_child_executed=False,Native_frame_reexecuted=False,
            successful_product_cases_reexecuted=False,original_failed_root_state_rewritten=False,
            original_missing_final_identity_retroactively_fabricated=False,Native_product_single_frame_qualified=False,
            actual_compound_evidence_validation=validation,current_Rust_input_count=787,
            current_Rust_inventory_checked_before_after=True,current_Rust_inventory_observations=inventories,
            fresh_input_pins=list(q.snapshots.values()),qualifier_imported_source_paths=sorted(imported),
            fresh_read_passes=q.read_passes,fresh_bytes_read=q.bytes_read,final_fresh_hashes=q.final_fresh_hashes,
            file_open_ceiling_per_second=20,qualifier_read_rates_by_kind=dict(binary=1048576,other=2097152),
            fresh_qualifier_is_not_new_native_or_product_evidence=True,full249_current_qualified=False,
            signed16_current_qualified=False,whole_runtime_reconciliation_required=True,
            P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',P10_started=False,PC_freeze_resolved=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        stop=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z0-9_]{1,256}',str(error)) else 'REDACTED_COMPOUND_QUALIFICATION_FAILURE'
    finally:
        if guard is not None:guard.close()
    if stop or result is None or guard is None or not guard.cleanup:
        print(json.dumps(dict(state='STOPPED_COMPOUND_NOT_ACCEPTED',stop_reason=stop,
            cleanup_confirmed=bool(guard and guard.cleanup),queue_unchanged=107)))
        return 2
    result.update(resource_samples=guard.samples,resource_cleanup_confirmed=True,
        sole_serial_sampler=True,parallel_observer_started=False,elapsed_seconds=time.monotonic()-started)
    with destination.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=True,indent=2)
    print(json.dumps(dict(state=PASS,accepted=108,remaining=141,next_case=115,cleanup_confirmed=True)))
    return 0


if __name__=='__main__':raise SystemExit(run())
