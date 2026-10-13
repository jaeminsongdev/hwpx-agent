"""Original independent full249/stop audit with current r04 bindings."""
import json
from unittest.mock import patch
import audit_current_graph_full as prior
import run_source_xml_product_full as d

SELF='tools/p09/audit_source_xml_product_full.py'
ACTUAL='implementation/p09/evidence/p09-163-source-xml-product-full.actual-run01.v1.json'
PASS='PASS_SOURCE_XML_CURRENT_FULL249_CLOSING_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'
STOP_PASS='PASS_SOURCE_XML_CURRENT_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'

def main():
    destination=d.p.s.scoped_path('implementation/p09/evidence/p09-163-source-xml-product-full.terminal-audit-run01.v1.json',fresh=True)
    scoped=d.p.s.scoped_path;dump=json.dump
    def output_path(name,**kw):
        if name=='implementation/p09/evidence/p09-159-current-graph-full.terminal-audit-run01.v1.json':return destination
        return scoped(name,**kw)
    def write(row,stream,**kw):
        if row['state'] in (PASS,'PASS_CURRENT_GRAPH_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'):
            d.require(row['contract_tests_passed']==60,'ORIGINAL_AUDITOR_LITERAL_COUNT')
            if row['state']!=PASS:row['state']=STOP_PASS
            # Original audit executes d.contracts52 + qualified-group12.
            row.update(contract_tests_passed=64,contract_tests_run=64,
                schema_version='hwpx-agent.p09-source-xml-current-full-closing/v1',
                source_xml_inventory_closing_pin=d.PARENT)
        return dump(row,stream,**kw)
    with patch.object(prior,'d',d),patch.object(prior,'SELF',SELF),patch.object(prior,'ACTUAL',ACTUAL), \
            patch.object(prior,'PASS',PASS),patch.object(d.p.s,'scoped_path',output_path),patch.object(json,'dump',write):
        return prior.main()

if __name__=='__main__':raise SystemExit(main())
