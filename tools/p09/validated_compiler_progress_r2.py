"""P170 r2 critical Rust target aliases/reserved diagnostic slots, no new build."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import validated_compiler_progress as prior

d=prior.d
SELF='tools/p09/validated_compiler_progress_r2.py'
TEST='tools/p09/tests/test_validated_compiler_progress_r2.py'
GROUPS={**prior.GROUPS,'hwpx_package':'hwpx-package','domain_ir':'domain-ir','hwpx_agent_cli':'product-cli'}
DEPENDENCY_SLOTS=16

class CargoStream(prior.CargoStream):
    def __init__(self,emit=prior.emit_event):
        super().__init__(emit);self.dependency_saved=0;self.critical_saved=set()

    def accept(self,raw):
        # Bypass ONLY the older observational budget, never original validation.
        d.b.CargoStream.accept(self,raw)
        if not raw.strip():return
        row=json.loads(raw.decode('utf-8'),object_pairs_hook=d.b.legacy.stream.unique_object)
        if row.get('reason')!='compiler-artifact':return
        self.observed_artifacts+=1;group=GROUPS.get(row.get('target',{}).get('name'))
        keep=(group is not None and group not in self.critical_saved) or (
            group is None and self.dependency_saved<DEPENDENCY_SLOTS)
        if not keep:self.omitted+=1;return
        if group is None:self.dependency_saved+=1
        else:self.critical_saved.add(group)
        self.saved+=1;prior.require(self.saved<=prior.MAX_ARTIFACT_EVENTS,'RESERVED_TOTAL_BUDGET')
        fresh=row.get('fresh')
        self.emit(dict(kind='artifact',sequence=self.saved,group=group or 'dependency',
            fresh=fresh if type(fresh) is bool else None,omitted_artifacts=self.omitted))

def contracts():
    prior.contracts();sys.path.insert(0,str(d.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_validated_compiler_progress_r2')
    with patch('subprocess.Popen',side_effect=AssertionError('P170_R2_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P170_R2_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P170_R2_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    prior.require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'CONTRACT6_PLUS10')
    return dict(contract_tests_run=16,contract_tests_passed=16)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--light',action='store_true',required=True);parser.parse_args()
    prior.require(d.c.Path.cwd().resolve()==d.c.ROOT,'CWD')
    destination=d.s.scoped_path('implementation/p09/evidence/p09-170-validated-compiler-progress.light-run02.v1.json',fresh=True)
    resources=d.s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=d.s.LiveSQLReader(resources)
        for n in (SELF,TEST,prior.SELF,prior.TEST,d.b.SELF,'tools/p09/signed_durable_build_stream.py'):q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_RESERVED_COMPILER_PROGRESS_CONTRACTS_ONLY_NOT_ACTUAL_BUILD_OR_GATE',
            actual_child_or_new_thread_started=False,actual_compiler_progress_observed=False,
            original_Cargo_validation_and_raw_SHA_unchanged=True,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.writer.b.prior.d.original.closed_error(e)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
