"""Resource-aware read-only recovery. Immutable run IDs; no original/Native attempt replay."""
import argparse,json,math,re,subprocess,time
from types import SimpleNamespace as NS
import run_personal_info_catalog_mask_product as prior
r,layout=prior.r,prior.layout
DRIVER='tools/p09/run_personal_info_catalog_mask_product_recovery.py'
COMPLETED='implementation/p09/evidence/p09-361-personal-info-catalog-mask427.v1.json'


def memory_headroom(available,peak):
    for v in(available,peak):
        if type(v)not in(int,float)or not math.isfinite(v)or not 0<=v<=100:raise ValueError('CATALOG_PRODUCT_MEMORY_OBSERVATION_INVALID')
    # Workload-specific admission, not a lower global RAM ceiling. The original
    # global RAM/commit stop stays 95%, and observed allocations stay Job-bound.
    required=5+peak
    return dict(available_ram_percent=available,prior_completed_comparable_job_peak_percent=peak,
        original_global_ram_ceiling_percent=95,required_available_percent=required,admitted=available>required,
        prediction_not_memory_reservation=True,native_execution_authorized=False)


def admission_models():
    assert memory_headroom(12,6)['admitted']
    assert not memory_headroom(11,6)['admitted']
    assert not memory_headroom(6,6)['admitted']
    for value in(True,float('nan'),float('inf'),-1,101,'6'):
        try:memory_headroom(value,6)
        except ValueError:pass
        else:raise ValueError('CATALOG_PRODUCT_MEMORY_MODEL_FAILED')
    return dict(groups=4,errors=0,product_tests_executed=0)


def main(argv=None):
    parser=argparse.ArgumentParser(description='One guarded, immutable read-only product verification; no Native or execution route.')
    parser.add_argument('--run',type=int,choices=range(432,441),required=True);args=parser.parse_args(argv)
    output=f'implementation/p09/evidence/p09-361-personal-info-catalog-mask-product-recovery{args.run}.v1.json'
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/output).exists(),'CATALOG_PRODUCT_RECOVERY_IMMUTABLE_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_CATALOG_MASK_PRODUCT_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        prior_source30_or_stored20_replayed=False,private_user_catalog_accessed=False,installed_catalog_mutated=False,
        original431_resource_failure_preserved=True,loaders_share_one_borrowed_catalog_adapter=True,request_match_and_component_caps_are_separate=True,
        source_document_mutation=False,ingest_commit_or_publication=False,native_execution_authorized=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(prior.OUTPUT));completed=layout.unpack(q.json(COMPLETED))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='48f0a103fd625bcbdbc54aaaf0daebab601e48e53d6da38a260e49225e30fd1e'
            and base['cleanup']is True and base['error_code']=='CURRENT_EPOCH_ACCEPT_ORIGINAL_RESOURCE_STOP'
            and len(base['steps'])==1 and not base['steps'][0]['bounded_output_observation']['observed_harness_started'],'EXACT431_RAM95_STOP_WITHOUT_ACCEPTED_CASES_RETAINED')
        c.require(q.snapshots[COMPLETED]['sha256']=='9b766f491502fb82b2c96726795339600d3286235ebe487cd0d5561dc2f5cf80'
            and completed['cleanup']is True and completed['fresh_inputs']==completed['final_fresh_hashes']==842,'EXACT_COMPLETED_COMPARABLE_COMPILER_RESOURCE_RECORD')
        peak=max(s['owned_job']['last_job_accounting']['peak_job_private_percent']for s in completed['steps'])
        row['admission_models']=admission_models()
        # Even a deferred run pins the changed implementation and model inputs.
        for path in(DRIVER,prior.DRIVER,prior.PRODUCT,prior.COMPILER,prior.TEST,prior.PARENT,prior.COMMON,prior.SERVICE,prior.LINK):q.pin(path)
        guard.check(force=True);row['memory_admission']=memory_headroom(guard.samples[-1]['available_ram_percent'],peak)
        if not row['memory_admission']['admitted']:
            row.update(state='DEFERRED_CARGO_PREDICTED_RAM95_HEADROOM_NOT_PRODUCT_OR_GATE',cargo_started=False,
                product_cases_executed=0,complete_compile_input_closure_checked=False)
        else:
            old={p['path']:p for p in base['source_pins']};changed={prior.PRODUCT,prior.COMPILER,prior.TEST}
            for path in sorted(set(old)|r.shared.source_inventory(guard.check)|{DRIVER}):
                pin=q.pin(path)
                if path in old and path not in changed:c.require(pin==old[path],'ALL_PRIOR_PASSED_SOURCE_STORED_LEGACY_COMPILER_TESTS_AND_GUARDS_PRESERVED')
            # Re-run the old-to-new structural preservation checks for the only
            # legacy changes. Failed 431 itself is never acceptance evidence.
            accepted=layout.unpack(q.json(prior.BASE));pins={p['path']:p for p in accepted['source_pins']}
            text=q.text(prior.PARENT);r.audit.inverse(text.replace('pub mod catalog;\n',''),pins[prior.PARENT],'ORIGINAL_SELECTED_MASK_PRODUCT_UNCHANGED')
            text=q.text(prior.LINK);r.audit.inverse(text.replace('mod product{include!("personal_info_catalog_mask_product.rs");}\n',''),pins[prior.LINK],'ORIGINAL_STORED20_TEST_BODIES_UNCHANGED')
            r.audit.inverse(prior.original_service(q.text(prior.SERVICE)),pins[prior.SERVICE],'ORIGINAL_SOURCE_STORED_CURRENT_ACCESS_AND_DELIVERY_ALGORITHMS_UNCHANGED')
            r.audit.inverse(prior.original_common(q.text(prior.COMMON)),pins[prior.COMMON],'ORIGINAL_SHARED_COMPILER_RECEIPT_BODY_UNCHANGED')
            text=q.text(prior.TEST);new={prior.PREFIX+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
            c.require(len(new)==42 and '#[ignore]'not in text,'EXACT41_SYNTHETIC_ONE_INSTALLED_NEW_CASES')
            cases=new|prior.AFFECTED;c.require(len(cases)==45,'NEW42_AND_DIRECTLY_AFFECTED3_ONLY')
            config=prior.CONFIG;image=a.AcceptanceReader(config.parent,guard.check);pin=image.pin(config.name)
            c.require((pin['bytes'],pin['sha256'])==(17020,'fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434'),'EXACT_UNMODIFIED_FIXED_INSTALLED_CONFIG')
            expected=set(accepted['actual_stored_test_inputs'][0]['dependency_paths'])|{prior.TEST}
            c.require(expected<=set(q.snapshots),'COMPLETE_BEFORE_COMPILE_TEST_INPUTS_PINNED')
            guard.check(force=True);row['memory_admission_before_cargo']=memory_headroom(guard.samples[-1]['available_ram_percent'],peak)
            if not row['memory_admission_before_cargo']['admitted']:
                row.update(state='DEFERRED_CARGO_PREDICTED_RAM95_HEADROOM_NOT_PRODUCT_OR_GATE',cargo_started=False,
                    product_cases_executed=0,complete_compile_input_closure_checked=True)
            else:
                scratch=c.ROOT/f'target/p09-catalog-mask-product-scratch-{args.run}';c.require(not scratch.exists()and scratch.parent.is_dir()
                    and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'PRODUCT_RECOVERY_UNIQUE_COMPILER_TEMP')
                scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
                command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','personal_info_mask_product','--features','p09-installed-format-fixture','--message-format=short','--',*sorted(cases),'--test-threads=1']
                row['cargo_started']=True;print(json.dumps(dict(state='CATALOG_PRODUCT_RECOVERY_PREFLIGHT',run=args.run,inputs=len(q.snapshots),new=42,affected=3)),flush=True)
                r.harness.run_one('optimized_catalog_products_shared_compiler45',command,cases,guard,env,row,observe_capture=r.snapshot)
                r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'CATALOG_PRODUCTS45_NO_WARNINGS')
                row['actual_compiled_test_inputs']=prior.prior.compiled_inputs(prior.prior.CONFIGS[1],expected,guard)
                c.require(not any(scratch.iterdir()),'PRODUCT_RECOVERY_COMPILER_TEMP_EMPTY')
                row.update(state='PASS_CATALOG_MASK_PRODUCT42_AFFECTED3_NOT_NATIVE_OR_GATE',product_cases_executed=45,new_product_cases=42,affected_product_cases=3,
                    complete_compile_input_closure_checked=True)
        final_attempted=True
        if image is not None:image.finish();row['installed_config_final_fresh_hashes']=image.final_fresh_hashes
        q.finish();guard.check(force=True);row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CATALOG_PRODUCT_RECOVERY_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            final_attempted=True
            try:
                if image is not None:image.finish();row['installed_config_final_fresh_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),installed_config_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','memory_admission','memory_admission_before_cargo','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[]),'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith(('PASS_','DEFERRED_'))else 2


if __name__=='__main__':raise SystemExit(main())
