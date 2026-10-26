"""Only the two previously failed projection comparisons; no previous18 replay."""
import json,sys,unittest
from test_prepared_bookmark684 import Contracts
names=('test_09_ports_preserve_save_identity_BMP_and_no_force_kill','test_10_worker_whole_eight_exact_input_projection')
suite=unittest.TestSuite(Contracts(name)for name in names);result=unittest.TestResult();suite.run(result)
print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),failed_tests=[str(t)for t,_ in result.errors+result.failures],actual_native_started=False)))
sys.exit(0 if result.wasSuccessful()else 2)
