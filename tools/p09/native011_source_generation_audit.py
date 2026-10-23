"""Read-only current Rust/compiled-cohort drift audit; no build or product."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_source_generation_audit.py'
SOURCE='tools/p09/current_issuer_build_inputs.py'
CHANGED='crates/hwpx-package/src/document_import.rs'
DECLARED=dict(path=CHANGED,bytes=26919,sha256='193b092f6288f7d47ce3d0d1c9917e7ba317f4949a50dd26ab7e0cfd414f2edc')
ADDITIVE=b'pub mod reference_targets;\n'


def sample_summary(samples):
    """Keep every sample in aggregates; bound repeated telemetry, not checks."""
    return dict(count=len(samples),last_eight=samples[-8:],
        system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
        available_RAM_min=min((s['available_ram_percent'] for s in samples),default=None),
        commit_used_max=max((s['commit_used_percent'] for s in samples),default=None))


def compare_observed(compiled,snapshots):
    """Compare recorded first reads only; do not claim a live closing boundary."""
    observed={}
    for pin in snapshots:
        name=pin['path']
        if name in observed:raise ValueError('DUPLICATE_OBSERVED_INPUT')
        observed[name]=pin
    rust={name:pin for name,pin in observed.items()
          if name.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
          and (name.endswith('.rs') or name.endswith('/Cargo.toml'))}
    return dict(observed_Rust_files=len(rust),
        changed=[dict(path=name,declared=pin,observed=rust[name])
                 for name,pin in sorted(compiled.items()) if name in rust and rust[name]!=pin],
        added=[rust[name] for name in sorted(set(rust)-set(compiled))],
        unobserved_compiled=sorted(set(compiled)-set(rust)),
        current_live_freshness_qualified=False,closing_boundary_qualified=False)


def main():
    sys.dont_write_bytecode=True;denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('SOURCE_GENERATION_AUDIT_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,locked_runtime_inputs as locks
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    output='implementation/p09/evidence/p09-361-native011-current-source-generation-drift002.v1.json'
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_GENERATION_AUDIT_NOT_BUILD_OR_RUNTIME',
        source_or_binary_or_pin_modified=False,GO_authorized=False,official_accepted_count=158,accepted_count_delta=0)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        c.require(not (c.ROOT/output).exists(),'EXCLUSIVE_GENERATION_AUDIT')
        q.pin(SELF);raw=q.text(SOURCE)
        code=a.native.definitions(raw,('rust_inputs',),dict(require=c.require,Path=Path,os=os))
        pacer=locks.OpenPacer(guard.check,rate=20)
        live=code.rust_inputs(c.ROOT,pacer.reserve)
        listing=a.read_exact(q,scope.LIST_PIN);declared=scope.listing_inputs(listing)
        compiled={n:p for n,p in declared.items() if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        c.require(len(compiled)==787,'ORIGINAL_COMPILED_RUST787_NOT_REBASED')
        row.update(compiled_Rust_files=len(compiled),current_Rust_files=len(live),
                   phase='first_read',closing_boundary_qualified=False)
        changed=[];missing=[]
        for name,pin in compiled.items():
            if name not in live:missing.append(name);continue
            current=q.pin(name)
            if current!=pin:changed.append(dict(path=name,declared=dict(pin),actual=dict(current)))
        additions=[dict(q.pin(name)) for name in sorted(live-set(compiled))]
        a.exact(q.pin(scope.EXE_PIN['path']),scope.EXE_PIN,'ORIGINAL_COMPILED_BINARY_UNCHANGED_NOT_EXECUTED')
        actual,payload=q._read(CHANGED,parse=True);q._bind(CHANGED,actual)
        raw=bytes(payload);inverse=raw.replace(ADDITIVE,b'',1)
        inverse_pin=dict(path=CHANGED,bytes=len(inverse),sha256=hashlib.sha256(inverse).hexdigest())
        exact_inverse=raw.count(ADDITIVE)==1 and inverse_pin==DECLARED
        row.update(first_read_comparison=compare_observed(compiled,list(q.snapshots.values())),
                   document_import_exact_inverse=exact_inverse,inverse_pin=inverse_pin,phase='closing')
        after=code.rust_inputs(c.ROOT,pacer.reserve)
        c.require(after==live,'TWO_ACTUAL_RUST_INVENTORY_OBSERVATIONS_STABLE')
        q.finish();guard.check(force=True)
        c.require(q.final_fresh_hashes==len(q.snapshots) and not denied,'FULL_CURRENT_SOURCE_CLOSING_NO_PROCESS')
        row.update(state='DIAGNOSED_CURRENT_SOURCE_GENERATION_DRIFT_NOT_BUILD_OR_RUNTIME',
            compiled_Rust_files=len(compiled),current_Rust_files=len(live),added_Rust_inputs=additions,
            changed_Rust_inputs=changed,missing_compiled_Rust_inputs=missing,
            document_import_exact_inverse=exact_inverse,one_added_declaration=ADDITIVE.decode('ascii').strip(),
            inverse_pin=inverse_pin,original_binary_pin=dict(scope.EXE_PIN),original_binary_bytes_unchanged=True,
            original_binary_executed=False,current_source_matches_compiled_declaration=not(changed or additions or missing),
            previous158_acceptance_preserved_not_current_source_promoted=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            no_hash_rebase_no_source_revert=True,source_generation_reconciliation_required=True)
        row.update(phase='complete',closing_boundary_qualified=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_GENERATION_AUDIT_FAILURE')
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),resource_summary=sample_summary(guard.samples),
            process_creation_attempts=len(denied))
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),cleanup=guard.cleanup,
            compiled=row.get('compiled_Rust_files'),current=row.get('current_Rust_files'),
            changed=[v['path'] for v in row.get('changed_Rust_inputs',[])],
            added=[v['path'] for v in row.get('added_Rust_inputs',[])],missing=row.get('missing_compiled_Rust_inputs'),
            exact_inverse=row.get('document_import_exact_inverse'),fresh=row.get('fresh_inputs'),
            final=row.get('final_fresh_hashes'),elapsed=row['elapsed_seconds'],receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('DIAGNOSED_') and guard.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
