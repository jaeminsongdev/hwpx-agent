"""Plan a separate current-source build; never runs Cargo, binaries or products."""
import ast
import json
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_cohort_plan.py'
TEST='tools/p09/tests/test_native011_current_cohort_plan.py'
BUILD='tools/p09/build_case112_current_stored.py'
RECOVERY=dict(path='implementation/p09/evidence/p09-361-native011-recorded-source-drift-recovery001.v1.json',
    bytes=10984,sha256='a463e885413bbd1c9dd2f3724287b70003320ba991ded454811d8533443e3846')
CHANGED=frozenset(('crates/hwpx-package/src/document_import.rs',
    'crates/hwpx-package/src/document_import/fields.rs','crates/hwpx-package/src/lib.rs',
    'crates/product-cli/src/main.rs','crates/product-cli/src/reference_validation_product.rs'))
TARGET='target/p09-361-native011-current-source-g001'
OLD_TARGET='target/p09-361-case112-current-lib-check-r001'
SUFFIX='extra-filename=-p361-native011-g001'


def require(ok,code):
    if not ok:raise ValueError('CURRENT_COHORT_PLAN_'+code)


def reconcile(compiled,comparison):
    require(len(compiled)==787 and not comparison['unobserved_compiled'],'ORIGINAL787_OBSERVED')
    require(comparison['current_live_freshness_qualified'] is False
        and comparison['closing_boundary_qualified'] is False,'RECOVERY_NOT_PROMOTED')
    changes=comparison['changed'];adds=comparison['added']
    require(len(changes)==5 and {r['path'] for r in changes}==CHANGED and len(adds)==18,'CLOSED_DELTA5_PLUS18')
    result={n:dict(p) for n,p in compiled.items()};delta={}
    for row in changes:
        name=row['path']
        require(row['declared']==compiled[name] and row['observed']['path']==name
            and row['observed']!=row['declared'],'EXACT_OLD_AND_OBSERVED')
        delta[name]=dict(row['observed']);result[name]=dict(row['observed'])
    for pin in adds:
        name=pin['path'];require(name not in result and name not in delta,'NO_ADDITION_OVERWRITE')
        result[name]=dict(pin);delta[name]=dict(pin)
    require(len(result)==805 and len(delta)==23,'EXPECTED805_WITH23_DELTA')
    return result,delta


def target_for(generation):
    require(type(generation) is int and generation in (1,2),'CLOSED_BUILD_GENERATION')
    return f'target/p09-361-native011-current-source-g{generation:03}'


def project_recipe(original,root,generation=1):
    target=target_for(generation)
    suffix=f'extra-filename=-p361-native011-g{generation:03}'
    require(type(original) is list and original.count(str(root/OLD_TARGET))==1
        and original[-1]=='extra-filename=-p361-case112-r001','ORIGINAL_RECIPE_IDENTITIES')
    projected=[str(root/target) if v==str(root/OLD_TARGET) else v for v in original]
    projected[-1]=suffix
    inverse=[str(root/OLD_TARGET) if v==str(root/target) else v for v in projected]
    inverse[-1]='extra-filename=-p361-case112-r001'
    require(inverse==original,'EXACT_RECIPE_INVERSE')
    return projected


def main(generation=1):
    target=target_for(generation)
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('COHORT_PLAN_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,successor_preparation_workspace_v1 as publisher
    import stored_test_profile81 as profile,native011_source_generation_audit as audit
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_CURRENT_COHORT_BUILD_PLAN_NOT_BUILD_OR_RUNTIME',official_accepted_count=158,
        accepted_count_delta=0,product_or_build_executed=False,GO_authorized=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,'tools/p09/stored_test_profile81.py','Cargo.toml','Cargo.lock','rust-toolchain.toml'):q.pin(name)
        recovery=a.read_exact(q,RECOVERY);listing=a.read_exact(q,scope.LIST_PIN)
        require(recovery['state']=='RECOVERED_RECORDED_FIRST_READ_SOURCE_DRIFT_NOT_CURRENT_OR_GATE'
            and recovery['original_failure_promoted'] is False and recovery['cleanup_confirmed'],
            'EXACT_RECORDED_RECOVERY')
        compiled={n:p for n,p in scope.listing_inputs(listing).items()
            if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        expected,delta=reconcile(compiled,recovery['comparison'])
        scope.pins(list(expected.values()),805)
        for name,pin in sorted(delta.items()):a.exact(q.pin(name),pin,'CURRENT23_DELTA_UNCHANGED')
        raw=q.text(BUILD)
        literal=[n.value for n in ast.parse(raw).body if isinstance(n,ast.Assign)
                 and any(isinstance(t,ast.Name) and t.id=='ARGS' for t in n.targets)]
        require(len(literal)==1,'ONE_ORIGINAL_BUILD_ARGS')
        args=ast.literal_eval(literal[0])
        require(args==['rustc','-p','hwpx-agent-cli','--test','form_stored_provider','--profile','test'],
            'BUILD_ONLY_NOT_TEST_COMMAND')
        original=a.native.definitions(raw,('require','task_for','recipe'),
            dict(profile=profile,ARGS=args,TARGET=c.ROOT/OLD_TARGET))
        recipe=project_recipe(original.recipe(1),c.ROOT,generation)
        require(not (c.ROOT/target).exists() and not (c.ROOT/target).is_symlink()
            and not (c.ROOT/target).is_junction(),'FRESH_TARGET_NOT_CREATED')
        q.finish();guard.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'CLOSED_PLAN_NO_PROCESS')
        row.update(state='PREPARED_CURRENT805_COHORT_BUILD_PLAN_NOT_BUILD_LIST_OR_RUNTIME',
            expected_Rust_inputs=list(expected.values()),expected_Rust_count=805,
            current_delta_fresh_inputs=23,unchanged782_current_freshness_qualified=False,
            full805_current_freshness_qualified=False,old_compiled_binary_current_qualified=False,
            recipe=recipe,original_recipe_source_pin=q.snapshots[BUILD],
            original_profile81_preserved=True,recipe_identity_only_inverse=True,
            target_directory=target,build_generation=generation,target_created=False,original158_preserved_not_replayed=True,
            required_before_build=['full805_live_inventory','fresh_all805_plus_build_inputs',
                'original_Owned_Job_readback_before_Cargo','original_CPU_RAM_protection'],
            required_after_build=['full805_live_inventory','fresh_closing_all805_plus_build_inputs',
                'every_Cargo_JSON_record_validated','fresh_exact_artifact_pin',
                'separate_list_only_exact249_not_product','independent_current_runtime_scope_qualification'],
            product_native_readiness_clocks_unchanged=True,automatic_retry=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,SyntaxError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_COHORT_PLAN_FAILURE')
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),
            resource_summary=audit.sample_summary(guard.samples),process_creation_attempts=len(denied))
        receipt=publisher.publish(c.ROOT,
            f'implementation/p09/evidence/p09-361-native011-current-cohort-build-plan{generation:03}.v1.json',
            row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),cleanup=guard.cleanup,
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PREPARED_') and guard.cleanup else 2


if __name__=='__main__':
    require(sys.argv[1:] in ([],['--generation2']),'CLOSED_PLAN_ARGUMENTS')
    raise SystemExit(main(2 if sys.argv[1:] else 1))
