"""315: standalone current stored/scoped-font product24; no prior suites/Native/DB replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_scoped_font_fixture_recovery as previous
import run_sql23_storage as closure
from run_scoped_font_recovery import snapshot
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-stored-font-components315.v1.json'
DRIVER='tools/p09/run_stored_font_components.py'
ROOT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
STORED=ROOT[:-3]+'/fonts.rs';REQUEST=PRODUCT[:-3]+'/fonts.rs'
TEST='crates/product-cli/tests/scoped_font_product.rs'
FIXTURE='crates/product-cli/tests/support/stored_source_fixture.rs'
SEARCH='crates/hwpx-package/src/document_import/search.rs'
FONT=previous.base.FONT_PARENT;CORE=previous.base.CORE;NAMES=previous.base.NAMES
NEW={DRIVER,STORED,REQUEST,TEST};CHANGED={ROOT,PRODUCT,SEARCH,FONT,CORE,NAMES}
LIMITS='''    /// # Errors
    /// Explicitly intersects a request maximum with the already validated server budget.
    pub fn restrict_match_limit(self,maximum:usize)->Result<Self,E>{
        if maximum==0||maximum>SourceSearchLimitConfig::default().matches{return Err(E::Limit);}
        Self::new(SourceSearchLimitConfig{matches:self.0.matches.min(maximum),..self.0})
    }
    #[must_use] pub const fn maximum_query_bytes(self)->usize{self.0.query_bytes}
'''
BUDGET='        if query.query.len()>limits.0.query_bytes||query.replacement.len()>limits.0.query_bytes{return Err(FontNameResolutionError::Limit.into());}\n'
NAME_WRAPPER='''        self.resolve_name_replacements_with_budget(query,maximum_mappings,4096,1024*1024,1024*1024)
    }
    pub(in crate::document_import) fn resolve_name_replacements_with_budget(&self,query:FontNameReplacementQuery<'_>,maximum_mappings:usize,
        query_bytes:usize,pattern_bytes:usize,dfa_bytes:usize)->Result<FontNameResolution,E>{
'''
NAME_GUARD='        if query_bytes==0||pattern_bytes==0||dfa_bytes==0||query.query.len()>query_bytes||query.replacement.len()>query_bytes{return Err(E::Limit);}\n'

def inverse(q,old):
    for path in (ROOT,PRODUCT):
        text=q.text(path);c.require(text.count('pub mod fonts;\n')==1,'ONE_SCOPED_FONT_MODULE_LINK')
        audit.inverse(text.replace('pub mod fonts;\n',''),old[path],'ALL_OTHER_STORED_AND_PRODUCT_MODULES_UNCHANGED')
    text=q.text(SEARCH);c.require(text.count(LIMITS)==1,'ONE_EXPLICIT_SERVER_BUDGET_INTERSECTION')
    audit.inverse(text.replace(LIMITS,''),old[SEARCH],'ALL_ORIGINAL_SEARCH_LIMIT_VALIDATION_AND_MATCHERS_UNCHANGED')
    text=q.text(FONT);c.require(text.count('use serde::{Deserialize, Serialize};')==1 and text.count('PartialOrd, Serialize, Deserialize)]')==1,'ONLY_FONT_LANGUAGE_INPUT_ENUM_DESERIALIZABLE')
    audit.inverse(text.replace('use serde::{Deserialize, Serialize};','use serde::Serialize;').replace('PartialOrd, Serialize, Deserialize)]','PartialOrd, Serialize)]'),old[FONT],'NO_IMPORTED_SOURCE_OR_RECEIPT_DESERIALIZATION_ADDED')
    text=q.text(CORE);c.require(text.count('use serde::Deserialize;\n')==1 and text.count(BUDGET)==2,'ONLY_AXIS_INPUT_AND_TWO_QUERY_BUDGET_GUARDS')
    text=text.replace('use serde::Deserialize;\n','').replace('PartialEq,Serialize,Deserialize)]','PartialEq,Serialize)]').replace(BUDGET,'')
    text=text.replace('        query.validate(128)?;\n        let rebuilt=','        query.validate(128)?;let rebuilt=')
    text=text.replace('fonts.resolve_name_replacements_with_budget(query,128,limits.0.query_bytes,limits.0.pattern_bytes,limits.0.dfa_bytes)?','fonts.resolve_name_replacements(query,128)?')
    audit.inverse(text,old[CORE],'SCOPED_CLONE_RENDER_PROTECTION_WRITER_AND_FULL_READBACK_ALGORITHMS_UNCHANGED')
    text=q.text(NAMES);c.require(text.count(NAME_WRAPPER)==text.count(NAME_GUARD)==1,'ONE_INTERNAL_REGEX_BUDGET_DELEGATION')
    text=text.replace(NAME_WRAPPER,'').replace(NAME_GUARD,'').replace('.size_limit(pattern_bytes.min(1024*1024))','.size_limit(1024*1024)').replace('.dfa_size_limit(dfa_bytes.min(1024*1024))','.dfa_size_limit(1024*1024)')
    audit.inverse(text,old[NAMES],'DEFAULT_NAME_API_HASH_MAPPING_AND_UNIQUENESS_ALGORITHMS_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_FONT_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_FONT_COMPONENTS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,old20_old24_official249_replayed=False,
        common_operation_compiler_or_dispatcher_qualified=False,output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='3b6fbc89aaacbd2321539d98b1adbe1ad7fb0ed715f0d9ca95dbdcfcc1857fea'and passed['cleanup']and passed['executed_cases']==11,'EXACT313_SCOPED_SOURCE_CLOSURE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW|CHANGED|{FIXTURE}
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in NEW|CHANGED:c.require(q.snapshots[n]==old[n],'ALL_OTHER_COMPILED_SERVICE_CRYPTO_ROUTE_RENDER_AND_TEST_INPUTS_UNCHANGED')
            elif n not in old:c.require(n in NEW|CHANGED|{FIXTURE},'ONLY_DECLARED_FONT_PRODUCT_FILES_ADDED_TO_SOURCE_CLOSURE')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)));c.require(len(cases)==24,'EXACT24_STANDALONE_STORED_FONT_CASES')
        scratch=c.ROOT/'target/p09-stored-font-scratch-315';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'STORED_FONT_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='STORED_FONT_PREFLIGHT',inputs=len(q.snapshots),new_standalone_cases=24,old_suites_replayed=False)),flush=True)
        harness.run_one('stored_font_product24',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--','--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'STORED_FONT_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_SCOPED_FONT_CURRENT_STORED_AND_STRICT_PRODUCT24_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=24,previous_algorithms_inverse_verified=True,next_work='source_edit_inventory_and_common_operation_compiler_and_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'STORED_FONT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'STORED_FONT_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
