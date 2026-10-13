"""P178 r3 helper inventory excludes not-yet-written active run receipts.

The first lower-rate fixture receipt and helper stay frozen. Only the receipt
inventory adapter is corrected; worker, rate, compiler and guards are unchanged.
"""
import sys
import io
import unittest
from unittest.mock import patch
import build_xml_capacity_product_r2 as prior
SELF='tools/p09/build_xml_capacity_product_r3.py'
TEST='tools/p09/tests/test_xml_product_r3_inventory.py'
LIGHT='implementation/p09/evidence/p09-178-owned-hash-pressure.light-r3-run01.v1.json'
RAW_CONTRACTS=prior.contracts

def helpers():
    # Original P177 helpers conditionally include its completed preparation.
    # Add immutable P177 terminal records by literal path, not mutable globals
    # patched to the current not-yet-created actual/preparation destinations.
    return sorted(set(prior.RAW_HELPERS())|{SELF,TEST,prior.SELF,prior.TEST,prior.pressure.SELF,
        'implementation/p09/evidence/p09-177-xml-capacity-product-build.actual-run01.v1.json',
        'implementation/p09/evidence/p09-177-xml-capacity-product-build.preparation-run01.v1.json',
        'implementation/p09/evidence/p09-178-owned-hash-pressure.light-run01.v1.json'})

def contracts():
    RAW_CONTRACTS();sys.path.insert(0,str(prior.prior.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_xml_product_r3_inventory')
    with patch('subprocess.Popen',side_effect=AssertionError('P178_R3_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P178_R3_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P178_R3_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    prior.prior.require(result.wasSuccessful() and result.testsRun==2 and not result.skipped,'CONTRACT260_PLUS2')
    return dict(contract_tests_passed=262,contract_tests_run=262)

def worker(task):return prior.worker(task)

def main():
    with patch.object(prior,'SELF',SELF),patch.object(prior,'LIGHT',LIGHT), \
            patch.object(prior,'helpers',helpers),patch.object(prior,'contracts',contracts):return prior.main()

if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
    raise SystemExit(main())
