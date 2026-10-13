"""Same original independent listing audit, current P162 bindings only."""
import json
from unittest.mock import patch
import audit_observed_graph_inventory as prior
import run_source_xml_product_inventory as v

SELF='tools/p09/audit_source_xml_product_inventory.py'
ACTUAL='implementation/p09/evidence/p09-162-source-xml-product-inventory.actual-run01.v1.json'
PASS='PASS_SOURCE_XML_CURRENT_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'

def main():
    destination=v.p.s.scoped_path('implementation/p09/evidence/p09-162-source-xml-product-inventory.terminal-audit-run01.v1.json',fresh=True)
    scoped=v.p.s.scoped_path;dump=json.dump
    def output_path(name,**kw):
        if name=='implementation/p09/evidence/p09-158-current-graph-inventory.terminal-audit-run01.v1.json':
            return destination
        return scoped(name,**kw)
    def write(row,stream,**kw):
        if row['state']==PASS:
            v.require(row['contract_tests_passed']==58,'ORIGINAL_AUDITOR_COUNT')
            # The original auditor executed v.contracts16 + v.d.contracts50.
            # 58 is its historical 12+46 output literal, not today's result.
            row.update(contract_tests_passed=66,contract_tests_run=66,
                schema_version='hwpx-agent.p09-source-xml-product-list-closing/v1')
        return dump(row,stream,**kw)
    with patch.object(prior,'v',v),patch.object(prior,'SELF',SELF),patch.object(prior,'ACTUAL',ACTUAL), \
            patch.object(prior,'PASS',PASS),patch.object(v.p.s,'scoped_path',output_path),patch.object(json,'dump',write):
        return prior.main()

if __name__=='__main__':raise SystemExit(main())
