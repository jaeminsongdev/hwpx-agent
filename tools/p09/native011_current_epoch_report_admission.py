"""Admit the explicit805 report into an actual unopened Batch, never GO."""
import json
import re
import sys
import time
from types import FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_report_admission.py'
TEST='tools/p09/tests/test_native011_current_epoch_report_admission.py'
SOURCE=dict(path='tools/p09/native011_shared_parent.py',bytes=6496,
    sha256='048070086879aefb7d9210b3dcba72bbe2cbb728805d93191ac74d622815d8bb')


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_REPORT_ADMISSION_'+code)


def connect(original,reports):
    require(type(original) is FunctionType and original.__name__=='admit_report'
        and original.__code__.co_filename.replace('\\','/').endswith(SOURCE['path'])
        and 'reports' in original.__globals__,'ENTIRE_ORIGINAL_REPORT_ADMISSION_FUNCTION')
    env=dict(original.__globals__,reports=reports)
    revised=FunctionType(original.__code__,env,argdefs=original.__defaults__,closure=original.__closure__)
    revised.__kwdefaults__=original.__kwdefaults__
    require(all(env[n] is value for n,value in original.__globals__.items() if n!='reports')
        and set(env)==set(original.__globals__),'ONLY_NAMED_REPORT_API_DEPENDENCY')
    return revised,dict(entire_original_admission_code_retained=True,
        original_default_report_module_mutated=False,original_history_reclassification_guard_retained=True,
        actual_Native_Frame_or_product_qualified=False)


def declare_controls(cohort,controls,scope):
    require(set(controls)=={SELF,TEST},'ONLY_TWO_NAMED_ADMISSION_CONTROLS')
    return NS(**{**vars(cohort),'required':scope.extend(cohort.required,controls)})


def main():
    require(sys.argv[1:] in ([],['--generation2']),'CLOSED_ADMISSION_ARGUMENTS')
    generation=2 if sys.argv[1:] else 1
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('CURRENT805_REPORT_ADMISSION_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import current_stored_runtime_scope as scope,successor_preparation_workspace_v1 as publisher
    import owned_source_read_pressure as bytes_policy,packed_receipt_json as packed
    import native011_current_epoch_scope as epoch,native011_current_epoch_binding as binding
    import native011_current_cohort_listing as listing,native011_current_epoch_plan as projection
    import native011_current_epoch_plan_inspection as inspection
    import native011_current_epoch_report as report,native011_shared_parent as shared
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import native011_source_generation_audit as audit
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    path=f'implementation/p09/evidence/p09-361-native011-current805-report-admission{generation:03}.v1.json'
    row=dict(state='FAILED_CURRENT805_REPORT_ACTUAL_BATCH_ADMISSION_NOT_NATIVE',official_accepted_count=158,
        accepted_count_delta=0,GO_authorized=False,Frame_instances=0,worker_or_product_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        require(not(c.ROOT/path).exists(),'EXCLUSIVE_NEW_ADMISSION_RESULT')
        for name in (SELF,TEST,report.SELF,report.TEST,inspection.SELF,projection.SELF,projection.TEST,
            epoch.SELF,binding.SELF,'tools/p09/native011_current_cohort_listing.py',
            'tools/p09/packed_receipt_json.py'):q.pin(name)
        a.exact(q.pin(SOURCE['path']),SOURCE,'ENTIRE_ORIGINAL_ADMISSION_SOURCE')
        raw=q.text(report.SOURCE['path']).encode('utf-8');reports,report_proof=report.connect(raw)
        parent,loaded=inspection.private_parent(c.ROOT,q,a)
        prepare,prefix=inspection.scope_prefix(q.text(inspection.PARENT['path']),a.native.definitions,vars(parent))
        original=prepare(c.ROOT,q,a,parent.bootstrap_loader(c.ROOT),scope,bytes_policy,
            NS(inspect_oracle=False,inspect_shared=False),row,NS(shared=None))
        before=original.data.planned
        cohort=binding.prepare_binding(q,a,scope,epoch,listing.build_contract,packed)
        preimages=a.read_exact(q,epoch.PREIMAGES)
        controls=scope.pins([q.pin(name) for name in (projection.SELF,projection.TEST)])
        cohort=declare_controls(cohort,scope.pins([q.pin(SELF),q.pin(TEST)]),scope)
        data,change,versions=projection.apply(original.data,cohort,preimages['preimages'],controls,
            original.batch,scope,epoch.CHANGED,q.checkpoint)
        projected=data.planned
        admit,proof=connect(shared.admit_report,reports)
        admitted=admit(c.ROOT,q,a,original.batch,data,3)
        after=data.planned
        require(after.history==projected.history==before.history and len(after.history)==419,
            'ALL419_HISTORY_PINS_EXACT_UNCHANGED')
        require(original.data.planned is before and projected.batch.phase==before.batch.phase=='NEW'
            and after.batch.phase=='NEW' and after.batch.parent_connection is None,
            'OLD_OWNERS_UNMODIFIED_NEW_OWNER_UNOPENED')
        require(all(after.whole.get(n)==pin for n,pin in projected.whole.items())
            and all(after.current.get(n)==pin for n,pin in projected.current.items())
            and admitted.pin['path'] in after.current,'ALL_CURRENT805_INPUTS_RETAINED')
        require(data.declared.to_physical(list(after.logical.values()))==after.whole,
            'ENTIRE_LOGICAL_PHYSICAL_SCOPE_EQUALITY')
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'CLOSING_BYTES_NO_PROCESS')
        row.update(state='PASS_CURRENT805_REPORT_ACTUAL_UNOPENED_BATCH_ADMISSION_NOT_NATIVE',
            report_admission=admitted.proof,original_admission_dependency=proof,
            original_prefix=prefix,source_projection=change,named_report_roles=report_proof['named_current805_roles'],
            whole_inputs=len(after.whole),current_inputs=len(after.current),history_inputs=419,
            original162_manifest_unchanged=data.manifest==original.data.manifest,
            all_prior_current805_pins_retained=True,original_owners_unmodified=True,
            original_engine_constructed=False,whole_scope_byte_audit_qualified=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,SyntaxError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_CURRENT805_ADMISSION_FAILURE')
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),process_creation_attempts=len(denied),
            resource_summary=audit.sample_summary(g.samples))
        receipt=publisher.publish(c.ROOT,path,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),
            whole=row.get('whole_inputs'),current=row.get('current_inputs'),history=row.get('history_inputs'),
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),cleanup=g.cleanup,receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
