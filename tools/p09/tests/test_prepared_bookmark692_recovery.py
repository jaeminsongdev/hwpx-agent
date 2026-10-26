"""Only the failed worker flag projection; retained23 are not rerun."""
import json,sys,unittest
from test_prepared_bookmark691 import Contracts
result=unittest.TestResult();unittest.TestSuite([Contracts('test_16_fixed_worker_selects_only_last_two')]).run(result)
print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),failed_tests=[str(t)for t,_ in result.errors+result.failures],actual_native_started=False)))
sys.exit(0 if result.wasSuccessful()else 2)
