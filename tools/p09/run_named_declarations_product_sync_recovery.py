"""361: absent final-fresh metadata stays absent, not success; source/doc audit only, no Rust replay."""
import run_named_declarations_product_sync as sync
FAILED=sync.OUTPUT
sync.OUTPUT='implementation/p09/evidence/p09-361-named-declarations-product-sync-recovery361.v1.json'
sync.DRIVER='tools/p09/run_named_declarations_product_sync_recovery.py'
original_inverse=sync.base.inverse

def inverse(q,old):
    original_inverse(q,old);failed=q.json(FAILED)
    sync.c.require(q.snapshots[FAILED]['sha256']=='6fa9fc546ae98f2b06dffc7fff5401dbc4d8a1b3e277f12c1bfe0c63d567dcbc'
        and failed['state']=='FAILED_NAMED_DECLARATIONS_PRODUCT_SYNC'and failed['error_type']=='KeyError'and failed['cleanup']
        and failed['Cargo_tests_DB_or_Native_replayed']is False,'EXACT360_MISSING_FINAL_FRESH_KEY_METADATA_FAILURE_RETAINED_NO_TEST_REPLAY')
    q.pin('tools/p09/run_named_declarations_product_sync.py')
sync.base.inverse=inverse
if __name__=='__main__':raise SystemExit(sync.main())
