"""Freshly bind actual761 eight/three-role captures; XML observations, no Native."""
import hashlib,json,subprocess,sys,time,zipfile
from types import SimpleNamespace as NS
import xml.etree.ElementTree as ET
import run_prepared_bookmark_native761 as e
import inspect_prepared_bookmark633 as fields
import resource_bundle714 as journal
r=e.r;m=e.runtime
SELF='tools/p09/audit_renamed_bookmark763.py'
OUTPUT='implementation/p09/evidence/p09-361-renamed-bookmark763-readback001.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-renamed-bookmark764-inputs.v1.json'
HP=fields.HP

def require(ok,code):
    if not ok:raise ValueError('XREF_RENAMED763_'+code)

def hold(q,pin):
    require(q.pin(pin['path'])==pin,'CURRENT_BYTES_MATCH_CAPTURE')

def ranges(root):
    require(len(list(root))==9,'FIXED_NINE_PARAGRAPHS')
    result=[]
    for index,paragraph in enumerate(list(root)[:8]):
        text='';selected='';begin=end=None;start=stop=None;active=False
        for node in paragraph.iter():
            if node.tag==HP+'fieldBegin':
                require(begin is None and node.get('type')=='BOOKMARK','EXACT_BOOKMARK_RANGE')
                props=[x for x in node.iter()if x.tag==HP+'integerParam'and x.get('name')=='Prop']
                require(len(props)==1 and props[0].text=='2','BLOCK_NOT_POINT')
                begin=node;start=len(text);active=True
            elif node.tag==HP+'fieldEnd':
                require(active and end is None and node.get('beginIDRef')==begin.get('id'),'EXACT_RANGE_END')
                end=node;stop=len(text);active=False
            elif node.tag==HP+'t':
                require(len(node)==0,'PLAIN_SOURCE_TEXT');value=node.text or '';text+=value
                if active:selected+=value
        require(begin is not None and end is not None and not active and start<stop,'WHOLE_NONEMPTY_RANGE')
        result.append(dict(paragraph_index=index,name_sha256=fields.digest(begin.get('name','')),selected_sha256=fields.digest(selected),text_sha256=fields.digest(text),start=start,stop=stop))
    return result

def main():
    require(sys.argv[1:]==['--audit-existing-renamed-eight-no-native'],'MODE')
    for path in(OUTPUT,MANIFEST):m.prepared.require_absent(r.c.ROOT,path)
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=observer=None;begin=time.monotonic()
    row=dict(state='FAILED763_RENAMED_CAPTURE_READBACK',cases=[],Native_started=False,old_passed_tests_or_Native_replayed=False,semantic_product_or_render_qualified=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding');q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        actual=e.codec.unpack(q.json(e.OUTPUT),guard.check)
        require(q.snapshots[e.OUTPUT]['sha256']=='ce781b13e006970ccc9fb9bdebe137c3699e679fd4e1c52f117208942aa2e63b'
            and actual['state']=='CAPTURED761_RENAMED_EIGHT_WITH_SAVED_PAGE_PRODUCER_BOUND_SEMANTICS_UNQUALIFIED'
            and actual['cleanup']is True and actual['renamed_eight_executed']is True and actual['fixed_eight_executed']is True
            and actual['fresh_inputs']==actual['final_fresh_hashes']==1320,'EXACT_WHOLE761_NOT_RETRY')
        for pin in actual['source_pins']:hold(q,pin)
        for name in m.prepared.loaded_dependencies(r.c.ROOT)|{SELF}:q.pin(name)
        prepared=m.prepared.validate_prepared(q,e.publisher.codec.unpack)
        require(len(actual['case_source_boundaries'])==8 and all(m.sections.closed_boundary(v)for v in actual['case_source_boundaries'])
            and m.sections.closed_boundary(actual['preparation_boundary'])and m.sections.closed_boundary(actual['final_audit_boundary'])
            and actual['batch_closed_for_final_audit']is True and actual['same_invocation_handoff_consumed']is True,'ALL_CLOSED_BOUNDARIES')
        capture=actual['capture_worker'];host=capture['handler_summary'];scope=host['protocol']['scope']
        require(capture['cleanup']is True and capture['exit_code']==0 and capture['requests']==153 and host['worker_lease_closed']is True
            and len(scope['retired_sessions'])==16 and scope['finished_cases']==[dict(case_index=i,case_status='returned')for i in range(1,9)]
            and actual['artifacts']['fresh_inputs']==actual['artifacts']['final_fresh_hashes']==56,'SIXTEEN_CLOSED_NATIVE_PRODUCERS')
        captures=[m.evidence.captured(q,m.directory(i),i,scope['retired_sessions'][(i-1)*2:i*2])for i in range(1,9)]
        require(captures==actual['artifacts']['cases'],'EXACT_CURRENT_CAPTURE_ARTIFACTS')
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check);require(not before,'NO_HWP_BEFORE')
        source=ranges(fields.section(q,prepared['source']['path']));target_name=fields.digest('p09_renamed737')
        expected=[dict(v)for v in source];expected[0]['name_sha256']=target_name
        entries=[];snapshots=[];observer.phase('readback')
        for candidate,cap in zip(prepared['cases'],captures,strict=True):
            index=candidate['case_index'];require(cap['source_case_index']==index,'ORDER')
            pins=dict(candidate=candidate['output'],**{k[:-5]:v for k,v in cap['artifacts'].items()if k.endswith('.hwpx')})
            observations={};stages={}
            for stage,pin in pins.items():
                hold(q,pin);root=fields.section(q,pin['path']);value=fields.observe(root)
                require(value['crossref_count']==1,'ONE_CROSSREF');bookmarks=ranges(root)
                field=value['crossrefs'][0]
                observations[stage]=dict(field=field,renamed_eight_source_ranges_preserved=bookmarks==expected)
                stages[stage]=dict(pin=pin,command_sha256=field['command_sha256'],display_sha256=field['display_sha256'])
                if stage!='candidate':
                    trace=cap['artifacts']['case-trace.json'];images=[v for k,v in sorted(cap['artifacts'].items())if k.startswith(stage+'-page-')]
                    require(len(images)==1,'FIXED_SINGLE_PAGE_OBSERVATION')
                    snapshots.append(dict(case_index=index,stage=stage,snapshot=pin,trace=trace,page_images=images,page_count=1,page_indices=[0],previously_closed_native_producer_bound=True))
            native_fields=[observations[s]['field']for s in('initial','saved','reopened')]
            expected_text={'page':fields.digest('1'),'bookmark_name':target_name,'content':source[0]['selected_sha256'],'relative_position':fields.digest('\uC704')}[candidate['display']]
            imagepins=[cap['artifacts'][s+'-page-001.bmp']for s in('initial','saved','reopened')]
            row['cases'].append(dict(case_index=index,display=candidate['display'],hyperlink=candidate['hyperlink'],stages=observations,
                all_source_ranges_preserved=all(v['renamed_eight_source_ranges_preserved']for v in observations.values()),
                all_commands_preserved=all(v['field']['command_sha256']==observations['candidate']['field']['command_sha256']for v in observations.values()),
                native_dirty_cleared=all(v['dirty']=='0'for v in native_fields),all_native_cache_matches_source_or_conditional_single_page=all(v['display_sha256']==expected_text for v in native_fields),
                saved_reopened_parameters_equal=observations['saved']['field']['parameter_hashes']==observations['reopened']['field']['parameter_hashes'],
                all_three_exact_BMP_bytes_equal=len({(p['bytes'],p['sha256'])for p in imagepins})==1))
            entries.append(dict(case_index=index,display=candidate['display'],hyperlink=candidate['hyperlink'],stages=stages))
        manifest=dict(schema='hwpx-agent.p09.renamed-capture-input764/v1',state='FIXED32_RENAMED_DOCUMENTS_AND24_PRODUCER_BOUND_PAGES_NOT_PRODUCT_OR_AUTHORITY',native_capture=q.snapshots[e.OUTPUT],source=prepared['source'],target_name_sha256=target_name,target_content_sha256=source[0]['selected_sha256'],cases=entries,snapshots=snapshots,native_execution_authorized=False,P09_complete=False)
        require(len(entries)==8 and len(snapshots)==24,'WHOLE_MATRIX')
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True);require(native.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        row['product_inputs']=r.shared.publisher.publish(r.c.ROOT,MANIFEST,manifest,NS(require=r.c.require,exact=r.a.exact))
        row.update(state='OBSERVED763_RENAMED_EIGHT_THREE_ROLE_CAPTURE_AND32_XML_NOT_PRODUCT_OR_GATE',Native_process_set_unchanged=True,Native761_resource_summary=dict(elapsed_seconds=actual['elapsed_seconds'],samples=len(actual['resource_samples']),system_CPU_max=max(s['system_cpu_percent']for s in actual['resource_samples']),available_RAM_min_percent=min(s['available_ram_percent']for s in actual['resource_samples'])))
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,ET.ParseError,zipfile.BadZipFile,KeyboardInterrupt)as error:row.update(**m.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),resource_samples=len(guard.samples),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=e.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-renamed-bookmark763-readback001-forensic',row);pin=e.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','resource_samples','system_CPU_max','available_RAM_min_percent','elapsed_seconds')},'cases':[{k:v for k,v in case.items()if k!='stages'}for case in row['cases']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED763_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
