"""Closed missing-test selection with exact executed IDs/counts; never products."""
import importlib
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
from types import SimpleNamespace as NS

SELF='tools/p09/native011_scoped_test_runner.py'
TARGETS={
    'test_native011_build_start':4,
    'test_native011_build_generation2':3,
    'test_native011_current_epoch_metadata_roles':2,
    'test_native011_current_epoch_batch_plan':3,
    'test_native011_current_epoch_plan_prefix':2,
    'test_native011_scoped_test_selection':3,
}
PRIOR_SELECTIONS=(
    ('136','test_native011_build_start','test_native011_current_cohort_build'),
    ('139','test_native011_build_generation2','test_native011_current_cohort_plan'),
    ('141','test_native011_build_generation2','test_native011_current_cohort_build'),
    ('151','test_native011_current_epoch_metadata_roles','test_native011_current_epoch_binding'),
    ('155','test_native011_current_epoch_batch_plan','test_native011_current_epoch_plan'),
    ('156','test_native011_current_epoch_plan_prefix','test_native011_current_epoch_plan'),
)


def require(ok,code):
    if not ok:raise ValueError('SCOPED_TEST_SELECTION_'+code)


def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from flatten(item)
        else:yield item


def checked_suite(modules,expected):
    require(set(modules)==set(expected),'EXACT_MODULE_SELECTION')
    selected=[];by_module={}
    for name,count in expected.items():
        module=modules[name];require(module.__name__==name,'MODULE_NAME_MATCHES_REQUEST')
        cases=list(flatten(unittest.defaultTestLoader.loadTestsFromModule(module)))
        ids=[case.id() for case in cases]
        require(type(count) is int and len(ids)==count and len(set(ids))==count
            and all(value.startswith(name+'.') for value in ids),'EXACT_EXECUTED_TEST_IDS_AND_COUNT')
        selected.extend(cases);by_module[name]=ids
    require(len(selected)==sum(expected.values()),'NO_OLD_OR_EXTRA_TESTS')
    return unittest.TestSuite(selected),by_module


def main():
    require(not sys.argv[1:],'CLOSED_FIXED_TEST_SET')
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('MISSING_MODEL_TESTS_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import successor_preparation_workspace_v1 as publisher
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import native011_source_generation_audit as audit
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_CLOSED_MISSING_MODEL_SELECTION_NOT_PRODUCT',official_accepted_count=158,
        accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        q.pin(SELF)
        sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        modules={}
        for name in TARGETS:
            path='tools/p09/tests/'+name+'.py';q.pin(path)
            module=importlib.import_module(name)
            require(Path(module.__file__).absolute()==c.ROOT/path,'EXACT_REQUESTED_TEST_FILE')
            modules[name]=module
        # This is unit-test source witnessing only, not a Native scope proposal.
        # No imported module is hidden, removed or inserted into a product plan.
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':
                    name=path.relative_to(c.ROOT).as_posix()
                    if name not in q.snapshots:q.pin(name)
        suite,ids=checked_suite(modules,TARGETS)
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),
            skipped=len(result.skipped)),executed_test_ids=ids,
            errors_test_ids=[case.id() for case,_ in result.errors],
            failures_test_ids=[case.id() for case,_ in result.failures],
            selection_corrections=[dict(prior_receipt_suffix=id,previously_requested=expected,
                previous_command_selected=actual,prior_record_preserved=True,
                prior_record_qualifies_requested_module=False,previous_156_process_started=False if id=='156' else None)
                for id,expected,actual in PRIOR_SELECTIONS])
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'ALL_SELECTED_SOURCE_BYTES_CLOSING')
        require(row['contracts']==dict(run=17,errors=0,failures=0,skipped=0),'ALL17_EXACT_MISSING_MODELS_PASS')
        row.update(state='PASS_EXACT17_MISSING_MODELS_AND_SELECTION_CORRECTION_NOT_PRODUCT',
            previous_passed_product_or_preparation_suites_replayed=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            test_source_witnesses_not_used_to_expand_Native_scope=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_MISSING_TEST_FAILURE')
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),
            process_creation_attempts=len(denied),resource_summary=audit.sample_summary(g.samples))
        receipt=publisher.publish(c.ROOT,
            'implementation/p09/evidence/p09-361-native011-scoped-test-selection-correction001.v1.json',
            row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],contracts=row.get('contracts'),
            errors=row.get('errors_test_ids'),failures=row.get('failures_test_ids'),
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),cleanup=g.cleanup,
            receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
