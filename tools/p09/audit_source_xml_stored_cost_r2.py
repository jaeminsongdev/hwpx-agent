"""Independent current r04 diagnostic accounting; never full/Gate acceptance."""
import json
from unittest.mock import patch
import audit_current_graph_cost as prior
import run_source_xml_stored_cost as d

SELF='tools/p09/audit_source_xml_stored_cost_r2.py'
ACTUAL='implementation/p09/evidence/p09-166-source-xml-stored-cost.actual-run01.v1.json'
PASS='PASS_CURRENT_SOURCE_XML_ADAPTIVE_COST_TERMINAL_ACCOUNTED_ONLY_NOT_FULL249_OR_GATE'

def main():
    destination=d.p.s.scoped_path('implementation/p09/evidence/p09-166-source-xml-stored-cost.terminal-audit-run02.v1.json',fresh=True)
    scoped=d.p.s.scoped_path;dump=json.dump;check_native=prior.check_native;extra={}
    def native(row,cap):
        check_native(row,cap)
        d.require(row['adaptive_native_diagnostic_callback'] and row['source_XML_current_r04_not_previous_r03']
            and row['source_xml_stop_closing_pin']==d.PARENT and row['legacy_total_samples_counts_host_polls']
            and row['native_cold_periods_explicitly_not_observed']
            and row['actual_adaptive_counts_unverified_without_footer'],'AUDIT_ADAPTIVE_CURRENT_SCOPE')
        d.require(cap['adaptive_footer_limit_bytes']==512 and cap['legacy_total_samples_counts_host_polls']
            and cap['resume_warm_sample_discard_required'] and cap['cold_periods_are_not_native_observations'],
            'AUDIT_ADAPTIVE_CAPTURE')
        schedule=cap['adaptive_schedule']
        extra.update(adaptive_schedule=schedule,adaptive_schedule_complete=schedule is not None,
            cold_native_periods_explicitly_not_observed=True,original_every_second_query_recipe_not_reintroduced=True,
            query_reduction_actual_verified=False,hot_resume_native_actual_verified=False)
        if schedule is not None:
            with patch.object(d.old.s,'MAX_SAVED',6):d.adaptive.validate_schedule(schedule)
            close=cap['host_cpu_records'][-1]
            d.require(cap['adaptive_schedule_error_code'] is None and close['kind']=='closed'
                and close['query_cleanup_confirmed'] and close['total_samples']==schedule['host_polls']
                and close['saved_samples']==schedule['emitted_samples']
                and close['high_samples']==schedule['high_host_polls']
                and close['unsaved_high_samples']==schedule['skipped_budget_polls'],'AUDIT_CLOSED_FOOTER_COUNTS')
            extra.update(query_reduction_actual_verified=schedule['skipped_cold_polls']+schedule['skipped_budget_polls']>0,
                hot_resume_native_actual_verified=schedule['discarded_resume_warm_calls']>0)
        elif row['state']=='DIAGNOSTIC_ALL249_FINISHED_NOT_FULL_QUALIFICATION_OR_GATE':
            d.require(False,'AUDIT_SUCCESS_REQUIRES_FOOTER')
    def path(name,**kw):
        if name=='implementation/p09/evidence/p09-160-current-graph-cost.terminal-audit-run01.v1.json':return destination
        return scoped(name,**kw)
    def write(row,stream,**kw):
        if row.get('state')=='PASS_CURRENT_GRAPH_COST_TERMINAL_ACCOUNTED_ONLY_NOT_FULL249_OR_GATE':
            d.require(row['contract_tests_passed']==80,'ORIGINAL_CONTRACT_LITERAL')
            row.update(schema_version='hwpx-agent.p09-source-xml-adaptive-case-cost-closing/v1',state=PASS,
                contract_tests_passed=112,contract_tests_run=112,**extra)
        return dump(row,stream,**kw)
    with patch.object(prior,'d',d),patch.object(prior,'SELF',SELF),patch.object(prior,'ACTUAL',ACTUAL), \
            patch.object(prior,'check_native',native),patch.object(d.p.s,'scoped_path',path),patch.object(json,'dump',write):
        return prior.main()

if __name__=='__main__':raise SystemExit(main())
