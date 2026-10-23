"""Reuse201's unchanged checks with a new immutable output and pins for this wrapper/original failure."""
import hashlib,json
import run_number_control_review_sync as prior
FAILURE=prior.OUTPUT
OUTPUT='implementation/p09/evidence/p09-361-number-control-review-sync-recovery202.v1.json'
SELF='tools/p09/run_number_control_review_sync_recovery.py'


def main():
    # One small immutable docs-only receipt; never source/product/Native authority.
    path=prior.c.ROOT/FAILURE;prior.c.require(path.stat().st_size<=65536,'ORIGINAL201_SMALL_DOCS_RECEIPT_LIMIT')
    raw=path.read_bytes();failed=json.loads(raw)
    prior.c.require(hashlib.sha256(raw).hexdigest()=='6eb4bbf94480b78639d043744960444e29345d3928bf6816098c54d0efea0e16'
        and failed['state']=='FAILED_NUMBER_CONTROL_REVIEW_DOC_SYNC'and failed['cleanup']and not failed['actual_Cargo_or_tests']
        and failed['error_code']=='REAL_REVIEW_RECOVERY_LEGACY_REJECTIONS_HISTORICAL_FAILURES_AND_REMAINING_STORE_PRODUCT_BOUNDARY',
        'ORIGINAL201_DOC_EXPRESSION_CHECK_FAILURE_PRESERVED_NOT_PRODUCT_FAILURE')
    prior.OUTPUT=OUTPUT
    prior.DOCS=set(prior.DOCS)|{SELF,FAILURE}
    # Reuse all source, inverse, test-identity, docs and guard checks unchanged.
    return prior.main()


if __name__=='__main__':raise SystemExit(main())
