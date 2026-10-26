"""Only failed fixed32 readonly executable; no build/test/Native replay."""
import json,sys,time
import product_result_capture698 as result
import run_prepared_bookmark_native631 as p
r=p.r
SELF='tools/p09/diagnose_block_product698.py'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark696-product002.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark698-product-diagnostic001.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
def main():
    r.c.require(sys.argv[1:]==['--failed-reader-only-no-build-native']and not(r.c.ROOT/OUTPUT).exists(),'XREF_DIAG698_MODE')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=b=None;begin=time.monotonic()
    row=dict(state='FAILED698_PRODUCT_DIAGNOSTIC',steps=[],Native_started=False,passed9_tests_or_build_replayed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check);prior=p.codec.unpack(q.json(PRIOR),guard.check)
        r.c.require(q.snapshots[PRIOR]['sha256']=='ed27f639b1b8d18570fd51247744af56eb8fb7bc5472e296a5de398e9b144de9'
            and prior['cleanup']is True and prior['error_type']=='JSONDecodeError','XREF_DIAG698_EXACT_FAILED_PRODUCT_CALL')
        pins={x['path']:x for x in prior['source_pins']}
        for path in(SELF,'tools/p09/product_result_capture698.py'):q.pin(path)
        manifest=q.json(MANIFEST);r.c.require(q.snapshots[MANIFEST]==pins[MANIFEST],'XREF_DIAG698_EXACT_COMPILED_MANIFEST')
        for pin in [manifest['source']]+[s['pin']for c in manifest['cases']for s in c['stages'].values()]:r.c.require(q.pin(pin['path'])==pin,'XREF_DIAG698_CURRENT32_BYTES')
        b=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for pin in prior['compiled_example']:r.c.require(b.pin(pin['path'])==pin,'XREF_DIAG698_EXACT_FAILED_EXECUTABLE')
        actual=result.command(guard,[str(r.c.ROOT/prior['compiled_example'][0]['path']),'--fixed32-readonly-no-native'],r.audit.environment(),row,'only_failed_fixed32_reader_with_bounded_error')
        b.finish();q.finish();guard.check(force=True)
        row.update(state='OBSERVED698_FIXED_PRODUCT_REJECTION_DIAGNOSTIC_NOT_ACCEPTANCE'if actual is None else'OBSERVED698_FIXED_PRODUCT_RESULT_NOT_GATE',product=actual)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,compiled_final_fresh_hashes=0 if b is None else b.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark698-product-diagnostic001-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds')},'steps':[{k:s.get(k)for k in('stage','exit_code','safe_error_code','stdout_bytes','stderr_bytes')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED698_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
