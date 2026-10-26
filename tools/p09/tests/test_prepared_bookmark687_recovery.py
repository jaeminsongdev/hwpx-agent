"""Only the failed current-source pin check; previous19 models retained."""
import json,sys,unittest
from test_prepared_bookmark684 import Contracts
suite=unittest.TestSuite([Contracts('test_09_ports_preserve_save_identity_BMP_and_no_force_kill')]);result=unittest.TestResult();suite.run(result)
print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),failed_tests=[str(t)for t,_ in result.errors+result.failures],actual_native_started=False)))
sys.exit(0 if result.wasSuccessful()else 2)
