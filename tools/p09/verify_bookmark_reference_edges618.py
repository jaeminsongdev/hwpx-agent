"""Guarded source-bookmark graph edges + real stored read path, never Native."""
import json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_inline_receipt567 as layout
import crossref_lossless_receipt610 as receipt
import metadata_forensic_retention615 as retention
import crossref_native_startup as startup
SELF='tools/p09/verify_bookmark_reference_edges618.py'
OUTPUT='implementation/p09/evidence/p09-361-bookmark-reference-edges618-audit003.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-bookmark-reference-edges618-audit003-forensic'
PRIOR='implementation/p09/evidence/p09-361-bookmark-reference-edges618-audit002.v1.json'
NEW='crates/product-cli/tests/bookmark_reference_edges618.rs'
CORE='crates/hwpx-package/tests/document_import_field_semantics.rs'
INTEGRATED='crates/product-cli/tests/bookmark_field_semantics616.rs'
SOURCE='crates/product-cli/tests/reference_source_product.rs'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-edges618/'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
RECOVERY='implementation/p09/evidence/p09-361-capture010-lossless-recovery611.v1.json'
def tests(q,path,prefix=''):
    text=q.text(path);r.c.require('#[ignore]'not in text,'P618_NO_IGNORES')
    return {prefix+v for v in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--bounded-graph-and-stored-reads'],'P618_BOUNDED_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'P618_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None;row=dict(state='FAILED618_BOOKMARK_GRAPH_EDGES',steps=[],own_cpu_selection=selection,
        actual_Hancom_COM_Native_or_DB_started=False,official249_or_large_stored_suite_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_display_or_navigation_qualified=False,
        source_main_schema_unchanged='v14',source_field_meaning_schema_unchanged='v2')
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=receipt.unpack(q.json(PRIOR));c.require(q.snapshots[PRIOR]['sha256']=='aed13cc75418df41b7b771332a1ad898d3341291bf34dc4cbedb091dae1dd5d5'
            and prior['state']=='PASS618_SAME_SOURCE_BOOKMARK_GRAPH_EDGES_STORED_READS28_NOT_NATIVE_OR_GATE'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==927,'P618_PRIOR002_CLOSED_PRODUCT_EVIDENCE')
        for pin in prior['source_pins']:
            if pin['path']not in(SELF,NEW):c.require(q.pin(pin['path'])==pin,'P618_RETAINED10_COMPILED_INPUTS_IDENTICAL')
        def retained_bodies(text):
            start=text.index('fn exact_delta(');end=text.index('fn check_edges(',start+8)
            return text[:start]+text[end:]
        c.require(retained_bodies(q.text(NEW))==retained_bodies(q.text(ARCHIVE+'tests-audit002.rs')),'P618_ONLY_STRONGER_DELTA_HELPER_CHANGED')
        prior_cases={name for step in prior['steps']for name,status in step['tests']if status=='ok'}|set(prior['retained_new_tests'])
        c.require(len(prior_cases)==28,'P618_PRIOR28_CASES_PRESENT')
        row.update(retained_bodies_reexecuted=False,prior_closed_receipt=q.snapshots[PRIOR],graph_delta_checks_strengthened_not_product_changed=True)
        recovery=layout.unpack(q.json(RECOVERY));c.require(q.snapshots[RECOVERY]['sha256']=='88eb3f144e32e0bd1fc7378c8c84eaf8e1968d12c933c5a8193ae196a628cab4'
            and recovery['cleanup']is True and recovery['fresh_inputs']==recovery['final_fresh_hashes']==307,'P618_EXACT_CLOSED611')
        carrier=recovery['derived_carrier'];c.require(q.pin(carrier['path'])==carrier,'P618_DERIVED_CARRIER_UNCHANGED')
        native=receipt.unpack(q.json(carrier['path']),guard.check)
        c.require(native['captured_cases']==8 and native['cleanup']is True and native['crossref_semantics_qualified']is False,'P618_ORIGINAL_NATIVE_FLAGS_NOT_PROMOTED')
        trace_rows=[]
        for case in native['artifacts']['cases']:
            for pin in case['artifacts'].values():c.require(q.pin(pin['path'])==pin,'P618_ALL40_ORIGINAL_ARTIFACTS')
            trace=q.json(case['artifacts']['target-trace.json']['path'])
            c.require(trace['state']=='lifecycle_callbacks_returned_semantics_unqualified'
                and trace['operations']['sdk_insert']['execute_returned']is True,'P618_RECORDED_CALLBACK_NOT_DISPLAY_PROOF')
            c.require(set(trace['operations'])=={'capture009_source_guard','opened_save','opened_probe','sdk_insert','saved_save','saved_probe',
                'fresh_saved_open','capture009_saved_guard','reopened_save','reopened_probe'},'P618_CAPTURE_OPERATION_SCOPE')
            c.require(set(trace['probe_observations'])=={'opened','saved','reopened'}and all(
                p['schema_version']=='hwpx-agent.private.crossref-worker-source-probe/v1'
                and p['native_target_resolution_qualified']is False and p['native_execution_attested']is False
                for p in trace['probe_observations'].values()),'P618_SOURCE_PROBES_ARE_NOT_DISPLAY_EVALUATION')
            trace_rows.append(dict(case_index=case['case_index'],recorded_SDK_callback_returned=True,
                original_effect_unknown=trace['operations']['sdk_insert']['effect_unknown'],
                native_display_or_navigation_qualified=False,source_snapshot_probes=3))
        row['retained_trace_audit']=dict(cases=trace_rows,closed_prior_execution_lineage=True,
            source_probe_only_not_native_display=True,prior_qualification_flags_changed=False)
        names=inventory.inventory(guard)|includes.test_inputs((NEW,CORE,INTEGRATED,SOURCE),guard)|{SELF,RECOVERY,CORPUS,
            'tools/p09/metadata_forensic_retention615.py','tools/p09/crossref_lossless_receipt610.py',
            ARCHIVE+'semantics.rs',ARCHIVE+'full_document.rs',PRIOR,ARCHIVE+'tests-audit001.rs',ARCHIVE+'verifier-audit001.py',
            ARCHIVE+'tests-audit002.rs',ARCHIVE+'verifier-audit002.py'}
        corpus=q.json(CORPUS);c.require(q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P618_FIXED_CORPUS')
        c.require(q.pin(corpus['source']['path'])==corpus['source'],'P618_ORIGINAL_SOURCE')
        formula='implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json';manifest=q.json(formula);names.add(formula)
        for case in manifest['cases']:
            for key in('input','output'):
                pin=case[key];actual=q.pin(pin['path']);c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'P618_ORIGINAL_FORMULA16');names.add(pin['path'])
        names.add('implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx')
        for name in sorted(names):q.pin(name)
        before=q.text(ARCHIVE+'semantics.rs');current=q.text('crates/hwpx-package/src/document_import/fields/semantics.rs')
        c.require(current[current.index('fn read_meanings('):]==before[before.index('fn read_meanings('):],'P618_ALL_READERS_LIMITS_RECONSTRUCTION_HELPERS_UNCHANGED')
        original=q.text(ARCHIVE+'full_document.rs');current=q.text('crates/product-cli/src/form_value_operation/full_document.rs')
        needle='        if draft.metadata.iter().any(|(key, value)| {\n            matches!((key, value), ("field_semantics_import_profile"'
        start=original.index(needle);end=original.index('        if draft.metadata.iter().any',start+12)
        begin=current.index('        // These reserved keys always mark a partial field-semantics import.')
        finish=current.index('        if draft.metadata.iter().any(|(key, value)| {',begin)
        restored=current[:begin]+original[start:end]+current[finish:]
        c.require(restored==original,'P618_ONLY_FIELD_SEMANTICS_PARTIAL_MARKER_GUARD_CHANGED_OTHER_GUARDS_BYTE_EXACT')
        all_new=tests(q,NEW);stored={name for name in all_new if name.startswith(('authenticated_stored_','cached_stored_'))}
        new=(all_new-stored)|{'stored::'+name for name in stored};c.require(len(new)==11 and len(stored)==3,'P618_NEW11_INCLUDING_STORED3')
        current_cases=new-{'stored::'+name for name in stored}
        c.require(len(current_cases)==8,'P618_EIGHT_DELTA_DEPENDENT_CASES')
        core={name for name in('source_https_tuple_is_typed_without_approval_or_label_inference',
            'all_sixteen_locked_table_sources_import_actual_formula_ast_and_unverified_cache',
            'shared_fresh_reconstruction_keeps_all_layers_exact_and_rejects_changed_non_field_bytes',
            'verified_reconstruction_is_original_bound_redacted_and_preserves_whole_models',
            'unsupported_date_is_explicit_and_source_fresh_verification_is_whole',
            'no_fields_preserves_original_graph_and_resources','nested_supported_link_keeps_unsupported_parent_and_all_source_positions')}
        c.require(core<=tests(q,CORE),'P618_AFFECTED_CORE7_PRESENT')
        integrated=tests(q,INTEGRATED);c.require(len(integrated)==9,'P618_PREVIOUS_INTEGRATED9')
        source={'source_field_meanings617::actual010_twenty_four_outputs_are_connected_to_main_source_v14_not_only_side_api'}
        retained=({'stored::'+name for name in stored})|core|integrated|source
        c.require(len(retained)==20 and prior_cases==new|core|integrated|source,'P618_RETAINED20_AND_CURRENT8_EXACT_COVERAGE')
        row.update(retained_tests=sorted(retained),retained_tests_count=20)
        c.require(next(iter(source)).split('::')[-1]in tests(q,'crates/product-cli/tests/reference_source_product/field_meanings617.rs'),'P618_ACTUAL_MAIN_SOURCE24_REGRESSION')
        probe=q.pin('target/debug/examples/p09_crossref_capture010_probe.exe');c.require(probe['sha256']=='379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c','P618_CONSUMED010_IMAGE_UNCHANGED')
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P618_NO_HWP_BEFORE')
        scratch=c.ROOT/'target/p09-bookmark-edges618-audit003-scratch';c.require(not scratch.exists(),'P618_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        artifact=a.AcceptanceReader(c.ROOT,guard.check);row['compiled_inputs']=[]
        # The source/meaning/graph consumer and security code is byte-identical.
        # Recheck prior compiler artifacts instead of replaying unaffected tests.
        for item in prior['compiled_inputs'][1:]:
            for pin in item['artifacts']:
                for key in('dep_info','binary'):c.require(artifact.pin(pin[key]['path'])==pin[key],'P618_RETAINED20_COMPILED_ARTIFACTS_UNCHANGED')
                c.require(deps.dependencies(c.ROOT/pin['dep_info']['path'])<=set(q.snapshots),'P618_RETAINED20_COMPILED_INPUTS_PREPINNED')
        configs=[('hwpx-agent-cli','bookmark_reference_edges618',current_cases)]
        print(json.dumps(dict(state='P618_FRESH_PREFLIGHT',inputs=len(q.snapshots),new_tests=11,retained_tests=20,current_tests=8,affected_tests=17,stored_tests=3,
            Native_or_large_stored_suite_authorized=False,CPU_RAM_guards_unchanged=True)),flush=True)
        for package,target,cases in configs:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target]
            if package=='hwpx-agent-cli':args+=['--features','p09-installed-format-fixture']
            args+=['--message-format=short','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
                '--config','profile.test.package.hwpx-agent-cli.codegen-units=2','--',*sorted(cases),'--exact','--test-threads=1']
            build_begin=time.time_ns();r.harness.run_one(target,args,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'P618_NO_WARNINGS')
            found=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                if path.stat().st_mtime_ns<build_begin:continue
                declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P618_ALL_COMPILED_INPUTS_PREPINNED')
                found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),
                    binary=artifact.pin(path.with_suffix('.exe').relative_to(c.ROOT).as_posix()),dependency_count=len(declared)))
            c.require(bool(found),'P618_FRESH_COMPILED_ARTIFACTS');row['compiled_inputs'].append(dict(target=target,artifacts=found))
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P618_NO_HWP_AFTER');c.require(not any(scratch.iterdir()),'P618_SCRATCH_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS618_SAME_SOURCE_BOOKMARK_GRAPH_EDGES_STORED_READS28_NOT_NATIVE_OR_GATE',new_tests=11,
            affected_tests=17,total_tests=28,actual010_outputs=24,source_bookmark_edges_in_saved_and_reopened=16,
            current_executed_tests=8,retained_tests_total=20,unrelated_reference_targets_checked_before_delta_reversal=True,
            full_context_reserved_partial_markers_fail_closed=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,
            error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P618_FAILURE_NO_RAW_VALUES')
        print(json.dumps(dict(state='P618_FAILURE_RECORDED_BEFORE_ENCODING',error_code=row['error_code'],work_continuing=False)),flush=True)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        normalized,retained=retention.retain(c.ROOT,SPOOL,row);pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(normalized,lambda:None),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','total_tests','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),cleanup=v.get('cleanup'),diagnostics=v.get('diagnostics'),
                locations=v.get('locations'),panic_locations=v.get('panic_locations'),safe_error_variants=v.get('safe_error_variants'))for v in row['steps']],
            'receipt':pin,'retained_metadata':retained}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS618_')else 2
if __name__=='__main__':raise SystemExit(main())
