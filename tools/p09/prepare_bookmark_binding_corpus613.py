"""Fixed already-captured010 corpus metadata only. No Native/probe/test replay."""
import hashlib,json,re,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_inline_receipt567 as layout
import crossref_lossless_receipt610 as codec
import crossref_external010_runtime as runtime
SELF='tools/p09/prepare_bookmark_binding_corpus613.py'
RECOVERY='implementation/p09/evidence/p09-361-capture010-lossless-recovery611.v1.json'
OBSERVATIONS='implementation/p09/evidence/p09-361-capture010-parameter-shapes612-validated.v1.json'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-bookmark-binding-corpus613-preparation.v1.json'

def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--prepare-captured-only'],'P613_PREPARE_ONLY')
    for name in(OUTPUT,CORPUS):c.require(not(c.ROOT/name).exists(),'P613_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED613_CORPUS_PREPARATION',own_cpu_selection=selection,actual_Hancom_COM_or_Native_started=False,
        existing_probe_bodies_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        recovery=layout.unpack(q.json(RECOVERY));observed=layout.unpack(q.json(OBSERVATIONS))
        c.require(q.snapshots[RECOVERY]['sha256']=='88eb3f144e32e0bd1fc7378c8c84eaf8e1968d12c933c5a8193ae196a628cab4'
            and q.snapshots[OBSERVATIONS]['sha256']=='c82eea6f95739cb082d4f84d679f6313f997e738c75e953575992c5d3e1a2e73'
            and all(v['cleanup']is True and v['fresh_inputs']==v['final_fresh_hashes']>0 for v in(recovery,observed)),'P613_EXACT_PRIOR_CLOSED_EVIDENCE')
        pin=recovery['derived_carrier'];c.require(q.pin(pin['path'])==pin,'P613_DERIVED_CARRIER');original=codec.unpack(q.json(pin['path']),guard.check)
        packet=q.json(runtime.original.PACKET);expected=runtime.fixed_input_pins()[runtime.original.PACKET];pin=q.snapshots[runtime.original.PACKET]
        c.require((pin['bytes'],pin['sha256'])==expected and len(packet['cases'])==len(original['artifacts']['cases'])==8,'P613_SOURCE_PACKET8')
        source=q.pin(runtime.SOURCE);expected=runtime.INPUT_PINS[runtime.SOURCE]
        c.require((source['bytes'],source['sha256'])==expected,'P613_ORIGINAL_INPUT')
        cases=[];displays=('page','bookmark_name','content','relative_position')
        for i,case in enumerate(original['artifacts']['cases']):
            c.require(case['case_index']==i+1 and observed['cases'][i]['case_index']==i+1,'P613_EXACT_CASE_ORDER')
            for pin in case['artifacts'].values():c.require(q.pin(pin['path'])==pin,'P613_ACTUAL40_UNCHANGED')
            cases.append(dict(case_index=i+1,display=displays[i//2],hyperlink=bool(i%2),
                command_sha256=hashlib.sha256(packet['cases'][i]['sdk_command'].encode()).hexdigest(),
                artifacts={stage:case['artifacts'][stage+'.hwpx']for stage in('opened','saved','reopened')}))
        corpus=dict(state='FIXED_CAPTURE010_CORPUS_NOT_NATIVE_OR_ACCEPTANCE_PERMIT',schema_version='hwpx-agent.private.captured010-bookmark-corpus/v1',
            source=source,cases=cases,lineage=dict(recovery=q.snapshots[RECOVERY],observations=q.snapshots[OBSERVATIONS]),
            native_execution_authorized=False,semantic_binding_qualified=False,P09_complete=False)
        pin=s.publisher.publish(c.ROOT,CORPUS,corpus,NS(require=c.require,exact=a.exact));c.require(q.pin(CORPUS)==pin,'P613_ACTUAL_CORPUS_FILE')
        q.finish();guard.check(force=True);row.update(state='PASS613_FIXED_CAPTURE010_CORPUS_PREPARED_NOT_COMPILED_OR_GATE',corpus=pin,captured_cases=8)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P613_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3))
        pin=s.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','corpus','captured_cases','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS613_')else 2
if __name__=='__main__':raise SystemExit(main())
