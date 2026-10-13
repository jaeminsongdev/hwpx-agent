"""P176 original17+7 fixture checks and new10; no full scans or child launch."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import xml_initial_capacity_binding as b
import weighted_audit_io as weighted

SELF='tools/p09/verify_weighted_audit_io.py'
TEST='tools/p09/tests/test_weighted_audit_io.py'
COUNT=34

def contracts():
    sys.path.insert(0,str(b.c.ROOT/'tools/p09/tests'))
    from tests.test_audit_evidence_io import AuditEvidenceIOTests
    from tests.test_live_sql_evidence_reader import LiveSQLReaderTests
    # Avoid the original fixture's global patch.stopall cleanup removing outer
    # child/thread guards. Exact same fake reader/source, individual patch cleanup.
    def fixture_reader(self,source,**kwargs):
        reader=weighted.original.AuditEvidenceReader('unused-fixture-root',lambda:None,**kwargs)
        p=patch.object(reader,'_source',return_value=source);p.start();self.addCleanup(p.stop);return reader
    names=unittest.defaultTestLoader.getTestCaseNames(LiveSQLReaderTests)
    names=[n for n in names if n!='test_immutable_manifest_whole_reads_under_real_pre_hash_admission']
    b.require(len(names)==7,'READER_ORIGINAL7_FIXTURES_NOT_REAL_MANIFEST')
    suite=unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromTestCase(AuditEvidenceIOTests),
        unittest.TestSuite(LiveSQLReaderTests(n) for n in names),
        unittest.defaultTestLoader.loadTestsFromName('test_weighted_audit_io')))
    with patch.object(AuditEvidenceIOTests,'reader',fixture_reader), \
            patch('subprocess.Popen',side_effect=AssertionError('P176_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P176_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P176_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    b.require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'ORIGINAL17_PLUS7_PLUS_NEW10')
    return dict(contract_tests_passed=COUNT,actual_authority_audit_or_child_started=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,default=1,choices=range(1,100));args=parser.parse_args()
    destination=b.s.scoped_path(f'implementation/p09/evidence/p09-176-weighted-audit-io.light-run{args.run:02}.v1.json',fresh=True)
    resources=b.s.SQLRuntimeResources();q=None
    row=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False)
    try:
        resources.admit();q=weighted.WeightedLiveReader(resources)
        for name in (SELF,TEST,weighted.SELF,'tools/p09/audit_evidence_io.py','tools/p09/live_sql_evidence_reader.py',
                     'tools/p09/tests/test_audit_evidence_io.py','tools/p09/tests/test_live_sql_evidence_reader.py'):
            q.pin(name)
        row.update(contracts());q.finish()
        row.update(state='PASS_WEIGHTED_AUDIT_READER_FIXTURES_ONLY_NOT_SOURCE_CLOSING_OR_GATE')
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
