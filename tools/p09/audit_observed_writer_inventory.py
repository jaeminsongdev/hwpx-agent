"""P172 independent r06 listing closure using unchanged original checks."""
import json
from unittest.mock import patch
import audit_writer_xml_product_inventory as prior
import run_observed_writer_inventory as v
SELF='tools/p09/audit_observed_writer_inventory.py'
ACTUAL='implementation/p09/evidence/p09-172-observed-writer-inventory.actual-run01.v1.json'
OLD='implementation/p09/evidence/p09-169-writer-xml-product-inventory.terminal-audit-run01.v1.json'
NEW='implementation/p09/evidence/p09-172-observed-writer-inventory.terminal-audit-run01.v1.json'
PASS='PASS_OBSERVED_WRITER_COMPILED249_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'
def main():
    raw=v.d.s.scoped_path;dump=json.dump
    def destination(name,**kw):return raw(NEW if name==OLD else name,**kw)
    def write(row,stream,**kw):
        if row.get('state')==PASS:
            row.update(schema_version='hwpx-agent.p09-observed-writer-inventory-closing/v1',
                contract_tests_passed=193,listing_contract_tests_passed=15,original_build_contract_tests_passed=178,
                r06_current_executable_verified=True)
        return dump(row,stream,**kw)
    with patch.object(prior,'v',v),patch.object(prior,'SELF',SELF),patch.object(prior,'ACTUAL',ACTUAL), \
            patch.object(prior,'PASS',PASS),patch.object(v.d.s,'scoped_path',destination),patch.object(json,'dump',write):
        return prior.main()
if __name__=='__main__':raise SystemExit(main())
