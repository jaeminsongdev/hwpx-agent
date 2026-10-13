"""P176 exact current-r4 inverse then all original IO oracles; first failure retained."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import verify_weighted_audit_io as prior
import current_audit_reader_context as context

b=prior.b;weighted=prior.weighted
SELF='tools/p09/verify_weighted_audit_io_r2.py'
TEST='tools/p09/tests/test_current_audit_reader_context.py'
COUNT=37

def contracts():
    sys.path.insert(0,str(b.c.ROOT/'tools/p09/tests'))
    from tests.test_audit_evidence_io import AuditEvidenceIOTests
    from tests.test_current_authority_sql_receipts import CurrentAuthoritySQLReceiptTests
    with patch.object(AuditEvidenceIOTests,'test_current_auditor_keeps_all_non_io_authority_checks_unchanged',
                      context.original_io_oracle_with_current_context):
        result=prior.contracts()
    suite=unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromName('test_current_audit_reader_context'),
        unittest.TestSuite((CurrentAuthoritySQLReceiptTests('test_whole_legacy_validator_changes_only_explicit_resource_branch'),))))
    with patch('subprocess.Popen',side_effect=AssertionError('P176_R2_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P176_R2_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P176_R2_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    b.require(result['contract_tests_passed']==34 and checked.wasSuccessful() and checked.testsRun==3
        and not checked.skipped,'CURRENT_R4_CONTEXT34_PLUS3')
    return dict(contract_tests_passed=COUNT,actual_authority_audit_or_child_started=False,
                all_original_reader_oracles_retained=True,current_r4_whole_declared_extension_inverse_exact=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,default=1,choices=range(1,100));args=parser.parse_args()
    destination=b.s.scoped_path(f'implementation/p09/evidence/p09-176-weighted-audit-io.light-r2-run{args.run:02}.v1.json',fresh=True)
    resources=b.s.SQLRuntimeResources();q=None
    row=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False)
    try:
        resources.admit();q=weighted.WeightedLiveReader(resources)
        for name in (SELF,TEST,context.SELF,context.SOURCE,context.ARCHIVE,prior.SELF,prior.TEST,weighted.SELF,
                     'tools/p09/tests/test_current_authority_sql_receipts.py','tools/p09/audit_evidence_io.py',
                     'tools/p09/live_sql_evidence_reader.py','tools/p09/tests/test_audit_evidence_io.py',
                     'tools/p09/tests/test_live_sql_evidence_reader.py',
                     'implementation/p09/evidence/p09-176-weighted-audit-io.light-run01.v1.json'):
            q.pin(name)
        row.update(contracts());q.finish()
        row.update(state='PASS_WEIGHTED_AUDIT_READER_AND_CURRENT_CONTEXT_FIXTURES_ONLY_NOT_SOURCE_CLOSING_OR_GATE')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        row['error_code']=b.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,row);row['resource_stop_reason']=resources.reason
        if resources.reason or not row.get('resource_watcher_cleanup_confirmed'):row['state']='FAILED_NOT_ACCEPTED'
        if q is not None:row.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        row['resource_tail']=weighted.resource_tail(resources)
        with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
        print(json.dumps({k:row.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if row['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
