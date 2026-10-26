"""Eight captured cases from preserved684 six + fresh690 two; XML observation only.
No Native/retry, field refresh, output replacement or semantic Gate promotion.
"""
import copy,hashlib,json,re,subprocess,sys,time,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import run_prepared_bookmark_native690 as e
import inspect_prepared_bookmark633 as fields
import block_bookmark_xml672 as blocks
from block_bookmark_source_plan643 import cases as source_cases
r=e.r
SELF='tools/p09/audit_block_bookmark693.py'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark693-capture-readback001.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'

def require(ok,code):
    if not ok:raise ValueError('XREF_BLOCK693_'+code)

def hold(q,pin):
    observed=q.snapshots.get(pin['path'])
    if observed is None:observed=q.pin(pin['path'])
    require(observed==pin,'UNCHANGED_CURRENT_BYTES')

def block_rows(root):
    paragraphs=list(root)
    require(len(paragraphs)==9,'FIXED_DERIVED_NINE_PARAGRAPHS')
    original=ET.Element(root.tag,root.attrib)
    for child in paragraphs[:8]:original.append(copy.deepcopy(child))
    return blocks.read_section(ET.tostring(original,encoding='utf-8'))

def main():
    require(sys.argv[1:]==['--audit-existing-eight-no-native']and not(r.c.ROOT/OUTPUT).exists()and not(r.c.ROOT/MANIFEST).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=None;begin=time.monotonic()
    row=dict(state='FAILED693_EIGHT_BLOCK_CAPTURE_READBACK',actual_native_started=False,old_Native_or_passed_tests_replayed=False,
        semantic_product_or_render_qualified=False,P09_complete=False,cases=[])
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for name in(SELF,'tools/p09/inspect_prepared_bookmark633.py','tools/p09/block_bookmark_xml672.py','tools/p09/block_bookmark_source_plan643.py'):q.pin(name)
        actual=e.codec.unpack(q.json(e.OUTPUT),guard.check)
        require(q.snapshots[e.OUTPUT]['sha256']=='6a402d7e8f14d7affb4e940b9f4d0c6e9adde7753891e75b979449d7e4e47a52'
            and actual['state']=='CAPTURED690_NEW_BLOCK_TAIL_TWO_PRODUCER_BOUND_SEMANTICS_UNQUALIFIED'
            and actual['cleanup']is True and actual['remaining_two_executed']is True
            and actual['retained_six_plus_new_two_capture_complete']is True and actual['fixed_eight_executed']is False
            and actual['fresh_inputs']==actual['final_fresh_hashes']>0,'EXACT690_TAIL_SUCCESS_NOT_EIGHT_REPLAY')
        for pin in actual['source_pins']:hold(q,pin)
        require(len(actual['retained_six']['cases'])==6 and len(actual['artifacts']['cases'])==2
            and actual['artifacts']['fresh_inputs']==actual['artifacts']['final_fresh_hashes']==12
            and len(actual['case_source_boundaries'])==2
            and all(e.runtime.sections.closed_boundary(x)for x in actual['case_source_boundaries']),'WHOLE_CLOSED_TWO_PLUS_RETAINED_SIX')
        capture=actual['capture_worker'];host=capture['handler_summary'];scope=host['protocol']['scope']
        require(capture['cleanup']is True and host['worker_lease_closed']is True and len(scope['retired_sessions'])==4
            and scope['finished_cases']==[dict(case_index=i,case_status='returned')for i in(1,2)],'FOUR_EXACT_NATIVE_SESSIONS_CLOSED')
        tail=[]
        for ordinal in(1,2):
            profiles=scope['retired_sessions'][(ordinal-1)*2:ordinal*2]
            tail.append(e.runtime.evidence.captured(q,e.runtime.directory(ordinal),ordinal,profiles))
        captures=actual['retained_six']['cases']+tail
        require([x['source_case_index']for x in captures]==list(range(1,9)),'NO_GAP_DUPLICATE_OR_SOURCE_SUBSTITUTION')
        for case in captures:
            for pin in case['artifacts'].values():hold(q,pin)
        prepared=q.json(e.runtime.prepared.PREPARED);hold(q,prepared['source'])
        source=blocks_source=block_rows(fields.section(q,prepared['source']['path']))
        row['original_blocks']=source
        target=source[0];plan=source_cases()[0]
        require(target['bookmark_name_sha256']==hashlib.sha256(plan['bookmark_name'].encode()).hexdigest()
            and target['selected_text_sha256']==hashlib.sha256(plan['selected_text'].encode()).hexdigest(),'INDEPENDENT_SOURCE_NAME_AND_RANGE')
        entries=[]
        for index,(candidate,cap)in enumerate(zip(prepared['cases'],captures),1):
            require(candidate['case_index']==cap['source_case_index']==index,'EXACT_MATRIX_ORDER')
            stagepins=dict(candidate=candidate['output'],**{k[:-5]:v for k,v in cap['artifacts'].items()if k.endswith('.hwpx')})
            require(set(stagepins)=={'candidate','initial','saved','reopened'},'ALL_FOUR_DOCUMENT_STAGES')
            observed={};expected={}
            for stage,pin in stagepins.items():
                hold(q,pin);root=fields.section(q,pin['path']);observation=fields.observe(root)
                require(observation['crossref_count']==1,'ONE_CROSSREF_EACH_STAGE')
                field=observation['crossrefs'][0];block=block_rows(root)
                identity=[{k:v for k,v in x.items()if k not in('native_begin_id','native_fieldid')}for x in block]
                baseline=[{k:v for k,v in x.items()if k not in('native_begin_id','native_fieldid')}for x in source]
                observed[stage]=dict(field=field,original_eight_block_ranges_unchanged=identity==baseline)
                expected[stage]=dict(pin=pin,command_sha256=field['command_sha256'],display_sha256=field['display_sha256'])
            saved=observed['saved']['field'];reopened=observed['reopened']['field']
            native=all(observed[s]['field']['dirty']=='0'for s in('initial','saved','reopened'))
            exact_command=all(v['field']['command_sha256']==candidate['command_sha256']for v in observed.values())
            display_equal=all(observed[s]['field']['display_sha256']==saved['display_sha256']for s in('initial','reopened'))
            expected_sha={'bookmark_name':target['bookmark_name_sha256'],'content':target['selected_text_sha256'],'page':hashlib.sha256(b'1').hexdigest()}.get(candidate['display'])
            expected_display=None if expected_sha is None else all(observed[s]['field']['display_sha256']==expected_sha for s in('initial','saved','reopened'))
            image_initial=cap['artifacts']['initial-page-001.bmp'];image_reopen=cap['artifacts']['reopened-page-001.bmp']
            pixels_stable=image_initial['bytes']==image_reopen['bytes']and image_initial['sha256']==image_reopen['sha256']
            row['cases'].append(dict(case_index=index,display=candidate['display'],hyperlink=candidate['hyperlink'],stages=observed,
                Native_dirty_cleared=native,whole_command_unchanged=exact_command,saved_reopened_all_parameter_hashes_equal=saved['parameter_hashes']==reopened['parameter_hashes'],
                all_Native_cache_equal=display_equal,expected_source_name_content_or_page1=expected_display,
                source_expected_display_applies=expected_sha is not None,initial_reopened_exact_BMP_bytes_equal=pixels_stable))
            entries.append(dict(case_index=index,display=candidate['display'],hyperlink=candidate['hyperlink'],stages=expected))
        require(len(row['cases'])==8,'WHOLE_MATRIX_OBSERVED')
        # Observations remain observations; collect all cases before classifying any mismatch.
        manifest=dict(schema='hwpx-agent.p09.block-capture-product-input693/v1',state='FIXED32_DOCUMENT_INPUTS_NOT_PRODUCT_OR_NATIVE_AUTHORITY',
            source=prepared['source'],target_name_sha256=target['bookmark_name_sha256'],target_content_sha256=target['selected_text_sha256'],
            cases=entries,native_execution_authorized=False,P09_complete=False)
        row['product_inputs']=r.shared.publisher.publish(r.c.ROOT,MANIFEST,manifest,__import__('types').SimpleNamespace(require=r.c.require,exact=r.a.exact))
        q.finish();guard.check(force=True)
        row.update(state='OBSERVED693_ALL_EIGHT_PRODUCER_BOUND_CAPTURES_AND32_XML_READBACK_NOT_PRODUCT_OR_GATE',
            original_failed684_still_failed=True,retained_six_not_replayed=True,Native690_only_two_executed=True,
            operating_db_registration_execution_or_full_F11_qualified=False,
            native_run_resource_summary=dict(elapsed_seconds=actual['elapsed_seconds'],system_CPU_max=max(s['system_cpu_percent']for s in actual['resource_samples']),
                available_RAM_min_percent=min(s['available_ram_percent']for s in actual['resource_samples'])))
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,ET.ParseError,zipfile.BadZipFile,KeyboardInterrupt)as error:row.update(**e.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=e.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark693-capture-readback001-forensic',row)
        pin=e.publisher.publish(OUTPUT,value)
        keys=('case_index','display','hyperlink','Native_dirty_cleared','whole_command_unchanged','saved_reopened_all_parameter_hashes_equal','all_Native_cache_equal','expected_source_name_content_or_page1','initial_reopened_exact_BMP_bytes_equal')
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'cases':[{k:case.get(k)for k in keys}for case in row['cases']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED693_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
