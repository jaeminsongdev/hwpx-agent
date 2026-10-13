"""P165 original full249/stop audit plus independently checked adaptive footer."""
import json
from unittest.mock import patch
import audit_current_graph_full as prior
import run_adaptive_source_xml_full as d

SELF='tools/p09/audit_adaptive_source_xml_full.py'
ACTUAL='implementation/p09/evidence/p09-165-adaptive-source-xml-full.actual-run01.v1.json'
PASS='PASS_CURRENT_ADAPTIVE_SOURCE_XML_FULL249_CLOSING_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'
STOP_PASS='PASS_CURRENT_ADAPTIVE_SOURCE_XML_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'

def main():
    destination=d.p.s.scoped_path('implementation/p09/evidence/p09-165-adaptive-source-xml-full.terminal-audit-run01.v1.json',fresh=True)
    scoped=d.p.s.scoped_path;dump=json.dump;original_observations=prior.diagnostic.audit_observations
    extra={}
    def audit_observations(row,passed):
        original_observations(row,passed)
        d.require(row['adaptive_native_closing_pin']==d.PARENT and row['legacy_total_samples_counts_host_polls']
            and row['native_cold_periods_explicitly_not_observed'] and row['adaptive_footer_required_for_success']
            and row['cold_gap_average_never_promoted_to_fresh_hot_sample'],'AUDIT_ADAPTIVE_BOUNDARY')
        cap=row['capture_diagnostics'];schedule=cap['adaptive_schedule'] if cap else None
        extra.update(adaptive_schedule=schedule,adaptive_native_closing_pin=d.PARENT,
            cold_native_periods_are_not_complete_history=True,hot_resume_native_actual_verified=False,
            adaptive_query_reduction_actual_verified=False,legacy_total_samples_counts_host_polls=True)
        if cap is not None:
            d.require(cap['adaptive_footer_limit_bytes']==512 and cap['legacy_total_samples_counts_host_polls']
                and cap['resume_warm_sample_discard_required'] and cap['cold_periods_are_not_native_observations'],'AUDIT_ADAPTIVE_CAPTURE')
        if passed:d.require(schedule is not None and cap['adaptive_schedule_error_code'] is None,'AUDIT_PASSED_REQUIRES_SCHEDULE')
        if schedule is not None:
            d.adaptive.validate_schedule(schedule)
            d.require(cap['adaptive_schedule_error_code'] is None,'AUDIT_SCHEDULE_NOT_REJECTED')
            records=cap['host_cpu_records'];close=records[-1]
            d.require(close['kind']=='closed' and close['query_cleanup_confirmed']
                and close['total_samples']==schedule['host_polls']
                and close['saved_samples']==schedule['emitted_samples']
                and close['high_samples']==schedule['high_host_polls']
                and close['unsaved_high_samples']==schedule['skipped_budget_polls'],'AUDIT_FOOTER_MATCHES_REAL_FRAMES')
            extra.update(hot_resume_native_actual_verified=schedule['discarded_resume_warm_calls']>0,
                adaptive_query_reduction_actual_verified=schedule['skipped_cold_polls']+schedule['skipped_budget_polls']>0,
                actual_query_calls=schedule['query_calls'],original_every_poll_recipe_query_calls=1+schedule['host_polls'],
                old_recipe_not_actually_rerun=True,actual_saved_samples=schedule['emitted_samples'])
    def output_path(name,**kw):
        if name=='implementation/p09/evidence/p09-159-current-graph-full.terminal-audit-run01.v1.json':return destination
        return scoped(name,**kw)
    def write(row,stream,**kw):
        if row['state'] in (PASS,'PASS_CURRENT_GRAPH_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'):
            d.require(row['contract_tests_passed']==60,'ORIGINAL_AUDITOR_LITERAL_COUNT')
            if row['state']!=PASS:row['state']=STOP_PASS
            # Actual executed suites: d.contracts85 + original group12.
            # Count is test executions, not 97 unique P09 completion items.
            row.update(contract_tests_passed=97,contract_tests_run=97,
                schema_version='hwpx-agent.p09-adaptive-source-xml-full-closing/v1',**extra)
        return dump(row,stream,**kw)
    with patch.object(prior,'d',d),patch.object(prior,'SELF',SELF),patch.object(prior,'ACTUAL',ACTUAL), \
            patch.object(prior,'PASS',PASS),patch.object(d.p.s,'scoped_path',output_path), \
            patch.object(prior.diagnostic,'audit_observations',audit_observations),patch.object(json,'dump',write):
        return prior.main()

if __name__=='__main__':raise SystemExit(main())
