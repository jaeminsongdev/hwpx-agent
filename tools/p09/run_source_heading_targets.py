"""418: direct OUTLINE source targets22, affected original targets2; no Native/source API promotion."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-source-heading-targets418.v1.json'
DRIVER='tools/p09/run_source_heading_targets.py'
BASE='implementation/p09/evidence/p09-361-personal-info-catalog-product417.v1.json'
PARENT='crates/hwpx-package/src/document_import/reference_targets.rs'
CORE='crates/hwpx-package/src/document_import/reference_targets/headings.rs'
ROOT_TEST='crates/hwpx-package/tests/document_import_reference_targets.rs'
TEST='crates/hwpx-package/tests/support/reference_heading_targets.rs'
SOURCE_API='crates/product-cli/src/reference_validation_product/source.rs'
LINK='#[path="support/reference_heading_targets.rs"]mod source_headings;\n'
CHANGED={PARENT,ROOT_TEST};NEW={DRIVER,CORE,TEST}
MODELS='fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/'
PINS={'Head/heading.cpp':(1815,'722cc2cf47d0ed6a24cd950ab3de53ce509895606d8ee3b6200422292e98042f'),
    'Head/heading.h':(1691,'7b70e5bdc0db701d2db7e89609dbf5d7ce0c432c71990ec70658a4caf1026db0'),
    'Head/ParaShapeType.cpp':(6786,'b43bc5e52df8ebcd9f962593a9b5431ae364f2a22b1b51bbad39f84b3b0a7459'),
    'Head/ParaShapeType.h':(3437,'8e0f375f1bb8f10eae3141fff13cc5316aea70388b11e5d2a43f852e540d051a'),
    'enumdef.h':(86455,'1c86392c934ac85f7ddd85c710b76be7649403a8404bce146db52558a0b95457')}
AFFECTED={'actual_source_target_identity_is_bound_without_fabricated_flow_or_reference_edges','original_package_and_document_binding_cannot_be_rebound'}


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_HEADING418_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_SOURCE_HEADING_TARGETS418',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        unaffected_successful_tests_replayed=False,source_API_schema_changed=False,source_API_unresolved_stages_cleared=False,
        native_number_or_navigation_qualified=False,effective_style_cascade_qualified=False,complete_reference_state_qualified=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);before=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='9bc1ae207554e7e616ee7946381b6c1f6934e381e9ff9d31a285007503ab4bb3'
            and before['cleanup']is True and before['fresh_inputs']==before['final_fresh_hashes']==775 and before['current_distinct_cases']==36,
            'EXACT417_VERIFIED_CURRENT_PRODUCT_AND_SOURCE_GRAPH')
        old={p['path']:p for p in before['source_pins']}
        for path in sorted(set(old)|r.closure.inventory(guard.check)|NEW|CHANGED|{MODELS+p for p in PINS}):
            pin=q.pin(path)
            if path in old and path not in CHANGED:c.require(pin==old[path],'ALL_OTHER_SOURCE_PRODUCT_MATCHER_AND_RESOURCE_GUARD_INPUTS_UNCHANGED')
        text=q.text(PARENT);added='pub mod headings;\n';c.require(text.count(added)==1,'ONE_SOURCE_HEADING_MODULE_EXPORT')
        r.audit.inverse(text.replace(added,''),old[PARENT],'ALL_PREVIOUS_BOOKMARK_NOTE_TABLE_OBJECT_CAPTION_AND_NUMBERING_TARGETS_UNCHANGED')
        text=q.text(ROOT_TEST);c.require(text.count(LINK)==1,'ONE_NEW_HEADING_TEST_CHILD')
        r.audit.inverse(text.replace(LINK,''),old[ROOT_TEST],'ALL_PREVIOUS_TARGET_TEST_BODIES_UNCHANGED')
        for path,(size,sha)in PINS.items():
            pin=q.snapshots[MODELS+path];c.require(pin['bytes']==size and pin['sha256']==sha,'EXACT_OBSERVED_PINNED_UPSTREAM_HEADING_DECLARATION_MODEL')
        model=q.text(MODELS+'Head/heading.cpp');enum=q.text(MODELS+'enumdef.h')
        for key in('type','idRef','level'):c.require('GetAttribute(att, L"'+key+'"'in model,'ALL_THREE_DECLARED_NATIVE_ATTRIBUTES_READ_EXPLICITLY')
        for value in('NONE','OUTLINE','NUMBER','BULLET'):c.require('L"'+value+'"'in enum,'EXACT_FOUR_OFFICIAL_HEADING_TYPES_NO_INVENTED_NATIVE_LEVEL_SEMANTICS')
        c.require(q.pin(SOURCE_API)==old[SOURCE_API]and 'reference-source-assessment/v12'in q.text(SOURCE_API),'CURRENT_V12_SOURCE_API_AND_FOUR_UNRESOLVED_STAGES_NOT_PROMOTED')
        text=q.text(TEST);cases={'source_headings::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
        c.require(len(cases)==22 and '#[ignore]'not in text,'EXACT_NEW22_SOURCE_HEADING_CASES_NO_SKIPS')
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        scratch=c.ROOT/'target/p09-source-heading-targets-scratch-418';c.require(not scratch.exists()and scratch.parent.is_dir()
            and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'HEADING418_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));selected=cases|AFFECTED
        print(json.dumps(dict(state='SOURCE_HEADING418_PREFLIGHT',inputs=len(q.snapshots),new_cases=22,affected_cases=2,actual_native_or_old_suites=False)),flush=True)
        r.harness.run_one('new_source_heading22_affected_targets2',[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test',
            'document_import_reference_targets','--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],selected);c.require(row['steps'][-1]['diagnostics']==[],'HEADING_SOURCE22_AND_AFFECTED2_NO_WARNINGS')
        c.require(not any(scratch.iterdir()),'HEADING418_COMPILER_TEMP_EMPTY');final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_DIRECT_OUTLINE_SOURCE_TARGETS22_AFFECTED2_NOT_API_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=22,affected_cases=2,next_work='versioned_actual_reference_source_API_heading_target_integration_while_retaining_four_unresolved_stages')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'SOURCE_HEADING418_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            try:final_attempted=True;q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
