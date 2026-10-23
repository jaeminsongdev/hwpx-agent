"""310: source font name matching + preserving scoped run/text edits20, no official queue replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_embedding_components as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-scoped-font-components310.v1.json'
DRIVER='tools/p09/run_scoped_font_components.py'
IDS=previous.IDS;FONT_PARENT=previous.baseline.prior.PARENT;RESOURCE=previous.CORE
STYLES='crates/hwpx-package/src/document_import/search/replacement/atoms/styles.rs'
TEXT=STYLES[:-3]+'/text.rs';RENDER=STYLES[:-3]+'/text/render.rs'
CORE=STYLES[:-3]+'/fonts.rs';CATALOG=CORE[:-3]+'/catalog.rs';READBACK=CORE[:-3]+'/readback.rs';NAMES=FONT_PARENT[:-3]+'/names.rs'
TEST='crates/hwpx-package/tests/document_import_scoped_fonts.rs'
FIXTURES={f'crates/hwpx-package/tests/support/{n}.rs'for n in ('search_definition_fixture','document_import_fonts_fixture','document_import_catalog_fixture','document_import_field_fixture')}
NEW={DRIVER,CORE,CATALOG,READBACK,NAMES,TEST};CHANGED={IDS,FONT_PARENT,RESOURCE,STYLES,TEXT,RENDER}
METHOD='''    /// Explicit union of immutable font-binary/v10 and text-style/v9 for scoped font edits.
    /// No new vocabulary, implicit inheritance, chart/caption-owner or Native qualification.
    #[must_use]
    pub const fn hwpml_2011_scoped_font_v11() -> Self {
        Self(ProfileKind::Hwpml2011ScopedFontV11)
    }

'''

def inverse(q,old):
    text=q.text(IDS)
    for marker,count in [('    Hwpml2011ScopedFontV11,\n',1),(METHOD,1),
        ('            ProfileKind::Hwpml2011ScopedFontV11 => "hwpml-2011-scoped-font-static/v11",\n',1),
        ('                | ProfileKind::Hwpml2011ScopedFontV11\n',5),
        ('            ProfileKind::Hwpml2011ScopedFontV11 => {\n                PreservationRuleProfile::Hangul2020PreviewTextV2\n            }\n',1)]:
        c.require(text.count(marker)==count,'EXACT_EXPLICIT_SCOPED_PROFILE_UNION');text=text.replace(marker,'')
    for kind in ('Hwpml2011TextStyleV9','Hwpml2011FontBinaryV10'):
        current=f'{kind} | ProfileKind::Hwpml2011ScopedFontV11';c.require(text.count(current)==1,'ONE_UNION_CHAIN_PER_EXISTING_RULE_DOMAIN');text=text.replace(current,kind)
    audit.inverse(text,old[IDS],'ALL_ORIGINAL_V1_THROUGH_V10_RULES_AND_ENGINE_BODIES_UNCHANGED')
    for path,marker in [(FONT_PARENT,'pub mod names;\n'),(STYLES,'pub mod fonts;\n')]:
        text=q.text(path);c.require(text.count(marker)==1,'ONE_NEW_MODULE_LINK');audit.inverse(text.replace(marker,''),old[path],'ORIGINAL_FONT_IMPORT_OR_STYLE_COMPILER_BODY_UNCHANGED')
    for path,current,before in [(RESOURCE,'pub(in crate::document_import) fn require_binary_resources(','fn require_binary_resources('),
        (TEXT,'pub(super) mod render;','mod render;'),
        (RENDER,'pub(in crate::document_import::search::replacement::atoms::styles) fn text(','pub(super) fn text(')]:
        text=q.text(path);c.require(text.count(current)==1,'ONE_INTERNAL_REUSE_VISIBILITY_CHANGE');audit.inverse(text.replace(current,before),old[path],'ALL_ORIGINAL_BINARY_GUARD_TEXT_RENDER_AND_COMPILER_ALGORITHMS_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SCOPED_FONT_COMPONENTS_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SCOPED_FONT_COMPONENTS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='dce90579eba99baf0e604c29dd854c7d81dece12231e1e47310d44fd85364997'and passed['cleanup']and passed['total_cases']==24,'EXACT308_PRIOR_FONT_BINARY24_AND_SOURCE_CLOSURE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW|CHANGED|FIXTURES
        for n in sorted(names):
            q.pin(n)
            if n not in NEW|CHANGED and n in old:c.require(q.snapshots[n]==old[n],'ALL_OTHER_COMPILED_SCANNERS_WRITERS_AND_PREVIOUS_TESTS_UNCHANGED')
            elif n not in NEW|CHANGED:c.require(n in FIXTURES,'ONLY_DECLARED_SOURCE_FIXTURES_NEW_TO_CLOSURE')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'scoped::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))};c.require(len(cases)==20,'EXACT20_SCOPED_FONT_IDENTITIES')
        scratch=c.ROOT/'target/p09-scoped-font-scratch-310';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'SCOPED_FONT_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='SCOPED_FONT_PREFLIGHT',inputs=len(q.snapshots),new_cases=20,old24_and_official249_replayed=False)),flush=True)
        harness.run_one('source_font_names_and_scoped_clone20',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_scoped_fonts','--message-format=short','--','scoped::','--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'SCOPED_FONT_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_SCOPED_FONT_NAME_AND_RUN_TEXT_CLONE20_NOT_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=20,
            old24_and_official249_replayed=False,previous_algorithms_inverse_verified=True,next_work='current_stored_access_and_strict_product_binding_of_scoped_font_candidates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'SCOPED_FONT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'SCOPED_FONT_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
