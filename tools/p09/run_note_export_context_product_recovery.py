"""Retain the 52 passes and fix only a new product test's assertion syntax, then run two."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import run_note_export_context_components as base
shared,c,a,harness=base.shared,base.c,base.a,base.harness
PRIOR='implementation/p09/evidence/p09-361-note-export-context-components037.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-note-export-context-product-recovery038.v1.json'
BEFORE='''    for (name,value) in [("lang","fr"),("space","default")] {assert!(p.attributes().iter().any(|a|a.name().namespace()==Some("http://www.w3.org/XML/1998/namespace")&&a.name().local_name()==name&&{let span=a.value_span();section.get(span.start()..span.end())==Some(value.as_bytes())})));}'''
AFTER='''    for (name,value) in [("lang","fr"),("space","default")] {
        let attribute=p.attributes().iter().find(|a|a.name().namespace()==Some("http://www.w3.org/XML/1998/namespace")&&a.name().local_name()==name).ok_or("XML context attribute")?;
        let span=attribute.value_span();assert_eq!(section.get(span.start()..span.end()),Some(value.as_bytes()));
    }'''


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'CONTEXT_PRODUCT_RECOVERY_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_NOTE_CONTEXT_PRODUCT_RECOVERY',steps=[],actual_Hangul_or_COM=False,Native011_executed=False,
        prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);prior=q.json(PRIOR)
        c.require(q.snapshots[PRIOR]['sha256']=='5b429d7bcc6a7b71409488471091d9985cb50946617255eca1b2716abdd15fe6','EXACT_PRESERVED_CONTEXT_RESULT')
        c.require(prior['state']=='FAILED_NOTE_EXPORT_CONTEXT_COMPONENTS' and prior['cleanup'] and len(prior['steps'])==2,'PRESERVED_PRODUCT_SYNTAX_FAILURE')
        first,second=prior['steps'];c.require(first['exit_code']==0 and len(first['tests'])==52 and all(s=='ok' for n,s in first['tests']),
            'EXACT_FIFTY_TWO_EXISTING_PASSES_RETAINED')
        c.require(second['exit_code']==101 and second['tests']==[] and any('unexpected closing delimiter' in s for s in second['diagnostics']),
            'TWO_PRODUCT_TESTS_NEVER_EXECUTED_IN_FAILED_RESULT')
        for step in prior['steps']:
            job=step['owned_job'];c.require(step['cleanup'] and job['cleanup_confirmed'] and job['owned_tree_empty'] and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'BOTH_PREVIOUS_JOBS_TERMINAL')
        pins={p['path']:p for p in prior['source_pins']};names=base.inventory(guard.check)
        c.require(names<=set(pins),'NO_NEW_SOURCE_INVENTORY_SINCE_CONTEXT_RESULT')
        for name,pin in pins.items():
            q.pin(name)
            if name!=base.TEST:c.require(q.snapshots[name]==pin,'PRODUCTION_CORE_TESTS_AND_OTHER_INPUTS_UNCHANGED')
        text=q.text(base.TEST);c.require(text.count(AFTER)==1,'EXACT_ONE_SYNTAX_ASSERTION_FIX')
        inverse=text.replace(AFTER,BEFORE)
        c.require(pins[base.TEST]['sha256'] in {hashlib.sha256(inverse.encode()).hexdigest(),hashlib.sha256(inverse.replace('\n','\r\n').encode()).hexdigest()},
            'FULL_PRODUCT_TEST_SOURCE_INVERSE_ONLY_ASSERTION_SYNTAX_CHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',
            CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        harness.run_one('only_two_previously_unexecuted_product_context_cases',
            [harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(base.PRODUCT),'--exact','--test-threads=1'],base.PRODUCT,guard,env,row)
        c.require(base.inventory(guard.check)==names,'FINAL_CONTEXT_RECOVERY_SOURCE_INVENTORY')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NOTE_EXPORT_XML_CONTEXT_TWO_PRODUCT_TESTS_FIFTY_TWO_PRIOR_PASSES_PRESERVED_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,product_tests=2,retained_core_tests=52,
            production_and_core_tests_unchanged=True,only_product_test_assertion_syntax_changed=True,prior_fifty_two_tests_reexecuted=False,
            inherited_language_space_qualified_only_at_source_component_level=True,intermediate_xml_base_and_native_container_layout_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'CONTEXT_PRODUCT_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_CONTEXT_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
