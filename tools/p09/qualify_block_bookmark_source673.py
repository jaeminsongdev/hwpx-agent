"""Bind retained 670 source XML/ranges/text after successful Native cleanup."""
import hashlib,json,re,sys,time,zipfile,io
from pathlib import Path
import block_bookmark_source670 as capture
import block_bookmark_xml672 as xml
import run_prepared_bookmark_native631 as p
from verify_prepared_bookmark631 import command
r=p.r
SELF='tools/p09/qualify_block_bookmark_source673.py'
TEST='tools/p09/tests/test_block_bookmark_xml672.py'
RECEIPT='implementation/p09/evidence/p09-361-block-bookmark-source670-native001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-source673-readback001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('BLOCK673_'+code)

def readback(q,path,expected,checkpoint):
    require(q.pin(path)==expected and 0<expected['bytes']<=4194304,'ORIGINAL_SOURCE_PIN')
    checkpoint();raw=(r.c.ROOT/path).read_bytes();checkpoint()
    require(len(raw)==expected['bytes']and hashlib.sha256(raw).hexdigest()==expected['sha256'],'PARSED_BYTES_EXACT_ORIGINAL')
    with zipfile.ZipFile(io.BytesIO(raw))as z:
        entries=z.infolist();names=[e.filename for e in entries]
        require(len(entries)<=128 and len(set(names))==len(entries)and sum(e.file_size for e in entries)<=16777216
            and all(0<=e.file_size<=4194304 and not e.flag_bits&1 for e in entries),'ZIP_LIMITS')
        sections=[n for n in names if n.startswith('Contents/section')and n.endswith('.xml')]
        require(sections==['Contents/section0.xml'],'ONE_FIXED_SECTION')
        checkpoint();section=z.read(sections[0]);checkpoint()
    rows=xml.read_section(section);checkpoint()
    return dict(source=expected,section_sha256=hashlib.sha256(section).hexdigest(),block_ranges=rows,
        logical_range_and_text_bound=True,raw_text_present=False)

def main():
    require(sys.argv[1:]==['--retained-source-readback-only']and not(r.c.ROOT/OUTPUT).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=None;start=time.monotonic();row=dict(state='FAILED673_BLOCK_SOURCE_XML_READBACK',steps=[],Native_started=False,
        previous_Native_trials_replayed=False,product_block_support_qualified=False,Content_positive_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for path in(SELF,TEST,'tools/p09/block_bookmark_xml672.py',capture.SELF,
            'tools/p09/block_bookmark_source_plan643.py','tools/p09/prepared_bookmark631_evidence.py'):q.pin(path)
        v=p.codec.unpack(q.json(RECEIPT));require(q.snapshots[RECEIPT]['bytes']==141370
            and q.snapshots[RECEIPT]['sha256']=='eb475304ebc05fabd77a84dc46b0b780dafea98cc864bc55f0c5774220b53b7d','EXACT_RETAINED_CAPTURE')
        require(v['state']=='CAPTURED670_FIXED_BLOCK_SOURCE_PRODUCER_BOUND_SEMANTICS_UNQUALIFIED'
            and v['source_capture_executed']is True and v['cleanup']is True and v['batch_closed_for_final_audit']is True
            and v['capture_worker']['exit_code']==0 and v['capture_worker']['requests']==55
            and v['capture_worker']['cleanup']is True and v['qualification_worker']['exit_code']==0
            and v['qualification_worker']['cleanup']is True and v['fresh_inputs']==v['final_fresh_hashes']==324,
            'WHOLE_CAPTURE_AND_FINAL_INPUT_CLOSURE')
        for name in('qualification_boundary','capture_boundary','final_audit_boundary'):
            require(capture.sections.closed_boundary(v[name]),'ORIGINAL_INPUT_BOUNDARIES_CLOSED')
        require(len(v['case_source_boundaries'])==1 and capture.sections.closed_boundary(v['case_source_boundaries'][0])
            and v['partial_case_source_boundary']is None,'ONE_FINAL_SOURCE_BOUNDARY')
        pins=v['artifacts']['artifacts'];trace=q.json(capture.DIRECTORY+'/case-trace.json')
        require(q.snapshots[capture.DIRECTORY+'/case-trace.json']==pins['case-trace.json'],'EXACT_RETAINED_TRACE')
        profiles=v['capture_worker']['handler_summary']['protocol']['scope']['retired_sessions']
        capture.prior.evidence.producer(trace,profiles);capture.validate_ranges(trace)
        require(trace['error_code']is None and trace['cleanup_error']is None and trace['source_identity_preserved']is True
            and trace['input_leases_closed']is True and set(trace['artifacts'])==capture.NAMES,'COMPLETE_TRACE')
        for name,expected in pins.items():
            require(q.pin(capture.DIRECTORY+'/'+name)==expected,'CURRENT_RETAINED_ARTIFACT')
            if name=='case-trace.json':continue
            observed=trace['artifacts'][name]
            owner=trace['sessions'][0 if name.startswith('created')else 1]['process']
            require(observed['pin']['bytes']==expected['bytes']and observed['pin']['sha256']==expected['sha256']
                and observed['owner']==owner,'ARTIFACT_TO_EXACT_NATIVE_PRODUCER')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        value=command(guard,[sys.executable,'-B',str(r.c.ROOT/TEST)],r.audit.environment(),row,'observed_block_XML_pairing_and_text_negative_controls12')
        require({k:value[k]for k in('run','errors','failures','skipped')}==dict(run=12,errors=0,failures=0,skipped=0),'READBACK_MODELS')
        stages={name:readback(q,capture.DIRECTORY+'/'+name,pins[name],guard.check)for name in('created.hwpx','reopened.hwpx')}
        require(stages['created.hwpx']['block_ranges']==stages['reopened.hwpx']['block_ranges'],'ALL_EIGHT_REOPEN_IDENTITIES_AND_LOGICAL_RANGES_PRESERVED')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_HWP_PROCESS_CHANGE')
        q.finish();guard.check(force=True)
        row.update(state='QUALIFIED673_FIXED_EIGHT_BLOCK_SOURCE_XML_NOT_PRODUCT_CONTENT_OR_F11',
            retained_capture=q.snapshots[RECEIPT],stages=stages,block_ranges_per_document=8,documents=2,
            actual_XML_mapping_observed=True,source_block_range_and_text_qualified=True,
            pair_key='fieldBegin.id_to_fieldEnd.beginIDRef_not_shared_fieldid',Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt,zipfile.BadZipFile)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'BLOCK67[23]_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-start,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        pin=p.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','documents','block_ranges_per_document','fresh_inputs',
            'final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED673_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
