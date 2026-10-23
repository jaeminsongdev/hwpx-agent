"""308: isolated font-binary ID profile, resource binding10 and affected original14."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_reference_followup as baseline
import run_sql23_storage as compile_closure
shared,c,a,tools,compact,harness,audit=baseline.shared,baseline.c,baseline.a,baseline.tools,baseline.compact,baseline.harness,baseline.audit
OUTPUT='implementation/p09/evidence/p09-361-font-embedding-components308.v1.json'
DRIVER='tools/p09/run_font_embedding_components.py'
GOOD='implementation/p09/evidence/p09-361-font-reference-followup304.v1.json'
SYNC='implementation/p09/evidence/p09-361-font-reference-sync307.v1.json'
IDS='crates/hwpx-package/src/id_index.rs';CORE=baseline.prior.CORE;TEST=baseline.prior.TEST
CHILD='crates/hwpx-package/tests/support/font_reference_embedding.rs'
OFFICIAL_ROOT='fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/Head/'
OFFICIAL={OFFICIAL_ROOT+n for n in ('font.cpp','substFont.cpp')}
CHANGED={IDS,CORE,TEST};NEW={DRIVER,CHILD}|OFFICIAL
METHOD='''    /// Immutable shape/v6 plus header font/substFont binaryItemIDRef -> package manifest item.
    /// Static vocabulary: pinned Hancom model1453388472c703a4b299a0834f425cdac16644b9,
    /// OWPML/Class/Head/font.cpp and substFont.cpp ReadAttribute/WriteElement.
    /// Payload validity, font activation, text-style, charts and caption-owner rules are not added.
    #[must_use]
    pub const fn hwpml_2011_font_binary_v10() -> Self {
        Self(ProfileKind::Hwpml2011FontBinaryV10)
    }

'''
RULE='''const FONT_BINARY_REFERENCE_RULES: &[ReferenceRule] = &[
    reference(PartSelector::Exact(HEADER_PART), HWPML_2011_HEAD_NAMESPACE, "font",
        "binaryItemIDRef", TargetSelector::PackageDocument, IdKind::ManifestItem, ValueSyntax::Text),
    reference(PartSelector::Exact(HEADER_PART), HWPML_2011_HEAD_NAMESPACE, "substFont",
        "binaryItemIDRef", TargetSelector::PackageDocument, IdKind::ManifestItem, ValueSyntax::Text),
];

'''

def inverse(q,old):
    text=q.text(IDS)
    for marker,count in [
        ('    Hwpml2011FontBinaryV10,\n',1),(METHOD,1),
        ('            ProfileKind::Hwpml2011FontBinaryV10 => "hwpml-2011-font-binary-static/v10",\n',1),
        ('                | ProfileKind::Hwpml2011FontBinaryV10\n',5),
        ('            ProfileKind::Hwpml2011FontBinaryV10 => {\n                PreservationRuleProfile::Hangul2020PreviewTextV2\n            }\n',1),
        (RULE,1),('        .chain(if matches!(profile.0, ProfileKind::Hwpml2011FontBinaryV10) { FONT_BINARY_REFERENCE_RULES } else { &[] })\n',1)]:
        c.require(text.count(marker)==count,'EXACT_INDEPENDENT_FONT_PROFILE_ADDITION');text=text.replace(marker,'')
    audit.inverse(text,old[IDS],'ALL_OLD_V1_THROUGH_V9_RULES_AND_MATCHING_BODY_UNCHANGED')
    text=q.text(CORE);start=text.index('fn require_binary_resources(');end=text.index('fn readback(',start)
    text=(text[:start]+text[end:]).replace('    #[error("FONT_REFERENCE_REPLACEMENT_BINARY_RESOURCE_REJECTED")] BinaryReference,\n','').replace(
        '        require_binary_resources(self)?;\n','').replace('hwpml_2011_font_binary_v10()','hwpml_2011_shape_v6()')
    audit.inverse(text,old[CORE],'ONLY_NEW_BINARY_BINDING_GUARD_AND_NEW_PROFILE_SELECTION')
    text=q.text(TEST);marker='#[path="support/font_reference_embedding.rs"] mod embedding_v1;\n';extra='    let original=embedding_v1::attach_binary_resource(&original)?;\n'
    c.require(text.endswith(marker)and text.count(extra)==1,'ONLY_VALID_RESOURCE_ADDED_TO_PREVIOUS_EMBEDDING_FIXTURE')
    audit.inverse(text[:-len(marker)].replace(extra,''),old[TEST],'ALL14_PREVIOUS_TEST_BODIES_PRESERVED_EXCEPT_ACTUAL_IN_MEMORY_RESOURCE')
    for n in OFFICIAL:
        code=q.text(n)
        for marker in ('L"binaryItemIDRef"','ReadAttribute','WriteElement'):c.require(marker in code,'PINNED_PRIMARY_SOURCE_FONT_BINARY_VOCABULARY')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_EMBEDDING_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_EMBEDDING_COMPONENTS',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,prior_Native_replayed=False,
        actual_DB_or_Hangul_or_COM_started=False,synthetic_opaque_binary_not_a_valid_or_activated_font=True,
        full_SEARCH024_or_scoped_product_execution_qualified=False,affected_old13_replayed_reason='changed_validation_profile_and_binary_guard')
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(GOOD));sync=q.json(SYNC)
        c.require(q.snapshots[GOOD]['sha256']=='ba6b467d617feb6aecc704bcc84beaa99bdb8fe128e24e753bb6d377d234b1ed'and passed['cleanup'],'EXACT304_PREVIOUS_CURRENT_SOURCE_CLOSURE')
        c.require(q.snapshots[SYNC]['sha256']=='06d64467f124b26cc2b2c68749989cd2a010698d7fa3f3ec0432dd0da4cd1f05'and sync['cleanup']and sync['distinct_passed_component_cases']==13,'EXACT307_PARTIAL13_AND_FAILURE_PRESERVED')
        old={p['path']:p for p in passed['source_pins']};names=compile_closure.inventory(guard.check)|set(old)|CHANGED|NEW
        for n in sorted(names):
            q.pin(n)
            if n not in CHANGED|NEW:c.require(q.snapshots[n]==old[n],'ALL_OTHER_CURRENT_COMPILED_SCANNER_PATCH_WRITER_SOURCE_FIXTURES_AND_OLD_TESTS_UNCHANGED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        root=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        added={'embedding_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(CHILD))}
        c.require(len(root)==14 and len(added)==10,'EXACT14_AFFECTED_AND10_NEW_CASES');cases=root|added
        scratch=c.ROOT/'target/p09-font-embedding-scratch-308';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_EMBEDDING_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='FONT_EMBEDDING_PREFLIGHT',inputs=len(q.snapshots),new_cases=10,affected_cases=14,official249_replayed=False)),flush=True)
        harness.run_one('font_binary10_and_affected14',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_font_replacement','--message-format=short','--','--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'FONT_EMBEDDING_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_BINARY_BINDING10_AND_AFFECTED14_NOT_VALID_FONT_NATIVE_OR_PRODUCT_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=10,affected_cases=14,total_cases=24,official249_reexecuted=False,all_old_ID_profiles_inverse_verified=True,
            next_work='font_name_query_and_scoped_selection_without_mutating_unselected_shared_properties')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_EMBEDDING_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_EMBEDDING_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
