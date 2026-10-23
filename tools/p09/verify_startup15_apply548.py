"""Adopt the exact qualified15-second startup bytes. No model, SQL, Hancom, Native or consumed-case replay."""
import ast,json,re,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import search_sql_receipt as layout
SELF='tools/p09/verify_startup15_apply548.py'
BASE='implementation/p09/evidence/p09-361-startup15-and-sql-snapshot547.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-startup15-applied548.v1.json'
LIVE='tools/p09/crossref_startup_input_idle.py'
CANDIDATE='tools/p09/crossref_startup_input_idle_candidate546.py'
def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--no-native-apply-check'],'P548_NO_NATIVE_CHECK_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'P548_IMMUTABLE_RECEIPT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=None
    row=dict(state='FAILED_QUALIFIED_STARTUP15_ADOPTION',own_cpu_selection=selection,actual_Hancom_COM_or_native_wait_or_SQL_or_Cargo_started=False,
        previous_models_or_SQL545_or_external003_or_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        execution_inputs_changed_requalification_required=True,current_session_or_new_fixed_eight_qualified=False,original003_failed_cleanup_preserved=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE));q.pin(SELF)
        c.require(q.snapshots[BASE]['sha256']=='d3b249ad729a0b849b8157bb1dc68a5bbd6ea525d98572c4417a231535661a4a'
            and base['state']=='PASS_STARTUP15_CANDIDATE_NEW8_AFFECTED2_AND_SQL_DENIED_SNAPSHOT5_NOT_NATIVE_OR_545_CLOSURE'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==213
            and base['contracts']==dict(run=15,errors=0,failures=0,skipped=0),'P548_CURRENT_QUALIFIED_CANDIDATE_AND_MODEL_RESULTS')
        for pin in base['source_pins']:
            actual=q.pin(pin['path'])
            if pin['path']!=LIVE:c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'P548_ALL_QUALIFIED_INPUTS_AND_ORIGINAL_GUARDS_BYTE_EXACT')
        original=base['qualified_startup_candidate'];live=q.snapshots[LIVE];candidate=q.snapshots[CANDIDATE]
        c.require((live['bytes'],live['sha256'])==(candidate['bytes'],candidate['sha256'])==(original['bytes'],original['sha256'])
            and live['sha256']=='b246b70db4f7292772683a9c20579ae576363e7c1fc4744080d58e95267eb98b','P548_APPLIED_BYTES_EXACTLY_MATCH_QUALIFIED_CANDIDATE')
        node=ast.parse(q.text(LIVE));constants={n.targets[0].id:n.value.value for n in node.body if isinstance(n,ast.Assign)
            and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and isinstance(n.value,ast.Constant)}
        c.require(constants['BOUND_SECONDS']==15.0 and constants['POLL_SECONDS']==.05,'P548_ONLY_INITIAL_WAIT_BOUND15_PRODUCT10_AND_NATIVE_GUARDS_UNCHANGED')
        q.finish();guard.check(force=True);row.update(state='PASS_EXACT_QUALIFIED_STARTUP15_APPLIED_NO_NEW_SESSION_OR_NATIVE_AUTHORITY',
            applied_initial_bound_seconds=15.0,original_poll_seconds=.05,qualified_candidate=original,all_other_qualified_inputs_preserved=True,
            product10_second_limit_or_CPU_RAM_owner_input_policy_changed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P548_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:v for k,v in row.items()if k not in('source_pins','resource_samples')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
