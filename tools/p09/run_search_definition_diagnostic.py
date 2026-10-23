"""Only the independent typed-header diagnostic; original failures are never replayed."""
import json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_definition_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-search-definition-header-diagnostic053.v1.json'
DIAGNOSTIC='definition_fixture_original_typed_readers_and_catalog_join_are_independently_admissible'


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'DEFINITION_DIAGNOSTIC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_DEFINITION_HEADER_DIAGNOSTIC',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        prior=q.json(base.OUTPUT);old={p['path']:p for p in prior['source_pins']}
        c.require(prior['state']=='FAILED_SEARCH_DEFINITION_COMPONENTS'and prior['cleanup']and len(prior['steps'])==1
            and sum(s=='ok'for n,s in prior['steps'][0]['tests'])==3,'PRESERVED_THREE_PASSES_AND_SIX_DEFINITION_FAILURES')
        for name in names-{base.TEST}:c.require(q.snapshots[name]==old[name],'UNCHANGED_PRODUCTION_AND_FIXTURE_FOR_DIAGNOSTIC')
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),CARGO_PROFILE_TEST_OPT_LEVEL='0',
            CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',CARGO_PROFILE_DEV_CODEGEN_UNITS='16',
            CARGO_PROFILE_TEST_CODEGEN_UNITS='16',CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        harness.run_one('one_independent_typed_header_and_catalog_diagnostic',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_search_definitions','--',DIAGNOSTIC,'--exact','--test-threads=1'],{DIAGNOSTIC},guard,env,row)
        q.finish();guard.check(force=True);row.update(state='PASS_DEFINITION_HEADER_INDEPENDENT_DIAGNOSTIC',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'HEADER_DIAGNOSTIC_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples)
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_HEADER_DIAGNOSTIC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),cleanup=row['cleanup'],steps=[{k:s.get(k)for k in('exit_code','diagnostics','locations','summaries','tests','safe_error_variants')}for s in row['steps']],pin=pin)),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
