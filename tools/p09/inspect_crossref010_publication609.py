"""Bounded forensic inspection of retained010 only; never Native/retry/acceptance."""
import json,re,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_generation010_publication as old
import crossref_inline_receipt567 as layout
import compact_receipt_json as compact
SELF='tools/p09/inspect_crossref010_publication609.py'
OUTPUT='implementation/p09/evidence/p09-361-capture010-retained-inspection609.v1.json'
RAW_SHA='8b3b52e328fe106e0d4485626e2e46a8441bc5d0b435b7b7222517d332e6b547'

def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--inspect-only'],'P609_INSPECT_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P609_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_RETAINED010_INSPECTION',own_cpu_selection=selection,actual_Native_COM_or_Hancom_started=False,
        consumed010_replayed=False,original010_republished=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        manifest=q.json(old.SPOOL+'/'+old.MANIFEST);c.require(manifest['bytes']==831005 and manifest['sha256']==RAW_SHA,'P609_FIXED_RAW010')
        for pin in manifest['parts']:c.require(q.pin(old.SPOOL+'/'+pin['path'])['sha256']==pin['sha256'],'P609_PART_HASH')
        value=old.retained_row(c.ROOT);c.require(len(compact.raw(value))==831005,'P609_WHOLE_CANONICAL_RAW')
        for pin in value['source_pins']:c.require(q.pin(pin['path'])==pin,'P609_CONSUMED010_CURRENT_INPUTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=r.Path(file).absolute()if hasattr(r,'Path')else __import__('pathlib').Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        encoded=layout.encode(value)
        try:layout.pack(value);error=None
        except ValueError as failure:error=failure.args[0]
        row.update(retained_raw_sha256=RAW_SHA,raw_bytes=len(compact.raw(value)),inline_bytes=len(compact.raw(encoded)),
            original_codec_error=error,retained_state=value['state'],retained_cleanup=value['cleanup'],
            fixed_eight_executed=value['fixed_eight_executed'],captured_cases=value.get('captured_cases'),
            fresh_inputs_recorded=value.get('fresh_inputs'),final_fresh_hashes_recorded=value.get('final_fresh_hashes'),
            section_timing=value.get('section_timing'),
            worker_summary={key:{field:value[key].get(field)for field in('exit_code','requests','cleanup','io_threads_joined')}for key in('qualification_worker','fixed_worker')},
            artifact_cases=len(value.get('artifacts',{}).get('cases',[])),
            actual010_system_CPU_max=value.get('system_CPU_max'),actual010_available_RAM_min_percent=value.get('available_RAM_min_percent'),
            original_result_present=(c.ROOT/old.OUTPUT).exists())
        c.require(error in('COMPACT_RECEIPT_PAYLOAD_LIMIT','COMPACT_RECEIPT_OUTER_LIMIT'),'P609_REPRODUCED_ENCODING_SIZE_FAILURE')
        q.finish();guard.check(force=True);row['state']='PASS_RETAINED010_SIZE_FAILURE_INSPECTED_NOT_NATIVE_RETRY_OR_GATE'
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P609_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3))
        pin=s.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','retained_state','retained_cleanup','captured_cases','artifact_cases','raw_bytes','inline_bytes',
            'original_codec_error','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','actual010_system_CPU_max','actual010_available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
