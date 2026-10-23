"""Pure codec + exact retained010 regression, no Native or original-result publication."""
import hashlib,importlib.util,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import crossref_lossless_receipt610 as codec
import crossref_generation010_publication as old
import crossref_inline_receipt567 as layout
import compact_receipt_json as compact
SELF='tools/p09/verify_crossref_lossless610.py'
TEST='tools/p09/tests/test_crossref_lossless_receipt610.py'
OUTPUT='implementation/p09/evidence/p09-361-lossless-codec610-models-audit002.v1.json'

def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--models-only'],'P610_MODELS_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P610_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CODEC610_MODELS',own_cpu_selection=selection,actual_Native_COM_or_Hancom_started=False,
        consumed010_replayed=False,original010_republished=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        inspection='implementation/p09/evidence/p09-361-capture010-retained-inspection609.v1.json';prior=layout.unpack(q.json(inspection))
        c.require(q.snapshots[inspection]['sha256']=='964e85f5953895444b6f8d4ccb50e457e9b6bf48d2193a771f0ecf73d22f6742'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']>0,'P610_EXACT609_RETAINED')
        for pin in prior['source_pins']:
            if pin['path'].startswith(old.SPOOL+'/'):c.require(q.pin(pin['path'])==pin,'P610_ORIGINAL_RAW_SPOOL_UNCHANGED')
        names={SELF,TEST,'tools/p09/crossref_lossless_receipt610.py'}
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(names):q.pin(name)
        spec=importlib.util.spec_from_file_location('codec610_models',c.ROOT/TEST);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=unittest.TestResult()
        with patch('subprocess.Popen',side_effect=AssertionError('P610_PROCESS_TRAP'))as trap:
            unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
            row['process_constructor_trap_calls']=trap.call_count
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=16,errors=0,failures=0,skipped=0)and trap.call_count==0,'P610_ALL16_MODELS')
        original=old.retained_row(c.ROOT);raw=compact.raw(original);value=codec.encode(original,guard.check)
        row.update(original_raw_bytes=len(raw),encoded_bytes=len(compact.raw(value)),compressed_bytes=value['compressed_bytes'],retained_sha256=hashlib.sha256(raw).hexdigest())
        packet=codec.pack(original,guard.check);published=(json.dumps(packet,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode()
        c.require(len(published)<=compact.MAXIMUM and compact.raw(codec.unpack(packet,guard.check))==raw,'P610_EXACT010_BYTES_ROUND_TRIP_UNDER_UNCHANGED_WRITER_CAP')
        row.update(original010_state=original['state'],original010_cleanup=original['cleanup'],original010_captured_cases=original['captured_cases'],published_bytes=len(published))
        q.finish();guard.check(force=True);row['state']='PASS_CODEC610_EXACT010_LOSSLESS_ROUND_TRIP_NOT_NATIVE_OR_GATE'
    except(ValueError,OSError,KeyError,TypeError,AttributeError,AssertionError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P610_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        pin=s.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','original_raw_bytes','encoded_bytes','compressed_bytes','published_bytes',
            'fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
