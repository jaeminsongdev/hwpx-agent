"""P233: 현재 case64의 CPU 순간 피크를 원 Reader/검증된 null-safe 요약으로 확인."""
import argparse
import json
import resume_current_queue_runtime as r
import review_packed_cpu_peak_r2 as peak
SELF='tools/p09/review_current_queue_peak.py'
ROOT_PIN=dict(path=r.p.DIR+'/p230-case-064-run004.v1.json',bytes=574668,
    sha256='31c661809288bd35b03361bbce41e7d3784c7c47187f6831be016411a99e1150')
SUPPORT=dict(path=r.p.DIR+'/p224-cpu-peak-review-run01.v1.json',bytes=8727,
    sha256='659a277ae8be29c1ca60b7b76c3df4a445008145fd6fabee2fd66f72bb12a254')
PASS='PASS_CURRENT_QUEUE_CPU_PEAK_REVIEW_NOT_CAUSE_OR_GATE'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    r.require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'PEAK_CWD_RUN')
    path=r.p.c.ROOT/f'{r.p.DIR}/p233-current-peak-review-run{args.run:02}.v1.json'
    r.require(not path.exists(),'PEAK_FRESH_ONLY')
    context=r.g.observation.Context();owner=r.g.observation.Resources(context);q=candidate=None
    out=dict(schema_version='hwpx-agent.p09-current-queue-cpu-peak-review/v1',
        state='FAILED_NOT_ACCEPTED',**r.p.r.flags(),product_body_reexecuted=False,
        original_files_rewritten=False,CPU_cause_or_PC_freeze_resolution_established=False)
    try:
        owner.admit();q=r.Reader(owner,context)
        r.require(q.pin(SUPPORT['path'])==SUPPORT,'PEAK_LITERAL_SUPPORT')
        support=q.json(SUPPORT['path'])
        r.require(support['state']==peak.PASS and support.get('error_code') is None
            and support['resource_stop_reason'] is None and support['resource_watcher_cleanup_confirmed'] is True
            and support['IO']['finished'] is True and support['IO']['bound_inputs']==support['IO']['final_fresh_hashes']==6,
            'PEAK_COMPLETE_SUPPORT')
        for name in (peak.SELF,peak.TEST):
            pins=[pin for pin in support['bound_input_pins'] if pin['path']==name]
            r.require(len(pins)==1 and q.pin(name)==pins[0],'PEAK_UNCHANGED_REVIEW_CODE')
        q.pin(SELF);out['peak_summary_contract_tests_passed']=peak.contracts()
        r.require(q.pin(ROOT_PIN['path'])==ROOT_PIN,'PEAK_LITERAL_ROOT64')
        root=q.json(ROOT_PIN['path']);r.closed_attempt(root)
        r.require(root['state']==r.PASS and root['selected_test_index']==64,'PEAK_EXACT_CASE64')
        pin=root['case_receipt_pin']
        r.require(pin['path']==r.p.DIR+'/cases/p230-case-064-run004.json','PEAK_EXACT_BODY')
        body=q.json(pin['path'])
        r.require(q.reader.snapshots[pin['path']]==pin and body['state']=='PASS_SCOPED_NOT_GATE'
            and body['tests_passed']==1 and body['exit_code']==0 and body['stop_reason'] is None
            and body['job_final']['active_processes']==0,'PEAK_COMPLETED_BODY')
        out.update(metadata_peak_review=peak.summarize(root['metadata_observation']['samples']),
            original_parent_peak_review=peak.summarize(body['samples']),
            native_pressure=root['closing_component']['source_frame']['handles']['native_open_backpressure'],
            owned_read_pressure=[{k:v for k,v in row.items() if 'pressure' in k}
                for row in body['owned_source_reader_passes']],
            phase_counter_interpretation='caller phase tag is not external CPU cause')
        q.finish();candidate=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=r.p.b.run.original.closed_error(e)
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,candidate,lambda row:r.require(row['IO']['finished'] is True
            and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==6
            and row['peak_summary_contract_tests_passed']==8,'PEAK_ALL_FRESH'))
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason',
            'resource_watcher_cleanup_confirmed','metadata_peak_review','original_parent_peak_review',
            'owned_read_pressure','peak_summary_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2

if __name__=='__main__':raise SystemExit(main())
