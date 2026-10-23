"""Recover bounded first-read diagnosis from immutable failed evidence only."""
import json
import re
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_source_generation_recovery.py'
FAILED='implementation/p09/evidence/p09-361-native011-current-source-generation-drift002.v1.json'
FAILED_PIN=dict(path=FAILED,bytes=158493,sha256='7e86d005ef24eb31236aad8a93e73af3f947a2fee023c244b8a05cd664da4ca2')


def main():
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('RECOVERY_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,successor_preparation_workspace_v1 as publisher
    import native011_source_generation_audit as audit
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_RECORDED_SOURCE_DRIFT_RECOVERY',accepted_count_delta=0,
             product_or_build_executed=False,official_accepted_count=158,GO_authorized=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        for name in (SELF,audit.SELF,'tools/p09/current_stored_runtime_scope.py'):q.pin(name)
        failed=a.read_exact(q,FAILED_PIN);listing=a.read_exact(q,scope.LIST_PIN)
        c.require(failed['state']=='FAILED_SOURCE_GENERATION_AUDIT_NOT_BUILD_OR_RUNTIME'
            and failed['error_code']=='STOP_PREPARATION_SYSTEM_PRESSURE90'
            and failed['cleanup_confirmed'] and failed['process_creation_attempts']==0,
            'ORIGINAL_STOP_PRESERVED_NOT_PASS')
        compiled={n:p for n,p in scope.listing_inputs(listing).items()
            if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        c.require(len(compiled)==787,'ORIGINAL_RUST787_NOT_REBASED')
        comparison=audit.compare_observed(compiled,failed['source_pins'])
        q.finish();g.check(force=True)
        c.require(q.final_fresh_hashes==len(q.snapshots) and not denied,'RECOVERY_CLOSING_ONLY_RECEIPTS')
        row.update(state='RECOVERED_RECORDED_FIRST_READ_SOURCE_DRIFT_NOT_CURRENT_OR_GATE',
            comparison=comparison,compiled_Rust_files=len(compiled),original_failure_pin=FAILED_PIN,
            original_failure_promoted=False,source_or_binary_or_pin_modified=False,
            official158_preserved=True,source_generation_reconciliation_required=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_RECOVERY_FAILURE')
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),
            resource_summary=audit.sample_summary(g.samples),process_creation_attempts=len(denied))
        receipt=publisher.publish(c.ROOT,
            'implementation/p09/evidence/p09-361-native011-recorded-source-drift-recovery001.v1.json',
            row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],comparison=row.get('comparison'),
            error_code=row.get('error_code'),cleanup=g.cleanup,receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('RECOVERED_') and g.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
