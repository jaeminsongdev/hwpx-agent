"""Recover already generated eight files after the obsolete64KiB preparation check.
No generator/build/Native rerun; original failure remains immutable.
"""
import json,re,sys,time,subprocess
from pathlib import Path
from verify_block_bookmark_candidates682 import r,p,payloads,hashlib,ET,io,zipfile,ARCHIVE,HOST,HELPER,EXAMPLE,EXE,DEP,NATIVE,DIRECTORY,PRIOR,MANIFEST,require
FAILED='implementation/p09/evidence/p09-361-block-bookmark681-preparation682.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark681-recovery683.v1.json'
SELF='tools/p09/verify_block_bookmark_candidates683.py'
def inspect_outputs(q,actual):
    require(actual['state']=='block_bookmark681_eight_stored_candidate_private_copies_not_Native_or_revision'
        and len(actual['cases'])==8 and actual['actual_native_started']is False
        and actual['source_overwritten']is False and actual['head_changed']is False
        and actual['result_ingested']is False and actual['memory_repository_scanner_and_commits_are_fixtures']is True,'WHOLE_INERT_EIGHT')
    source=actual['source'];require(source['path']==DIRECTORY+'/source.hwpx'and q.pin(source['path'])==source,'DERIVED_SOURCE')
    before=payloads((r.c.ROOT/source['path']).read_bytes());original=payloads((r.c.ROOT/NATIVE).read_bytes())
    part='Contents/section0.xml'
    require(set(before)==set(original)and all(before[k]==original[k]for k in before if k!=part),'OTHER_SOURCE_PARTS_UNCHANGED')
    ns='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
    def blocks(data):
        root=ET.fromstring(data);return [ET.tostring(e)for e in root.iter()if e.tag in(ns+'fieldBegin',ns+'fieldEnd')]
    require(blocks(before[part])==blocks(original[part])and len(blocks(before[part]))==16,'ORIGINAL_EIGHT_BLOCK_PAIRS_UNCHANGED')
    rows=[]
    for index,case in enumerate(actual['cases'],1):
        require(type(case['case_index'])is int and case['case_index']==index and case['display']==('page','bookmark_name','content','relative_position')[(index-1)//2]
            and type(case['hyperlink'])is bool and case['hyperlink']is(index%2==0)and case['stored_metadata_and_head_unchanged']is True,'CASE_MODES_AND_SOURCE_HEAD')
        pin=case['output'];receipt=case['output_receipt']
        require(pin['path']==DIRECTORY+f'/case-{index:02}.hwpx'and 0<pin['bytes']<=4194304 and q.pin(pin['path'])==pin,'EXACT_OUTPUT')
        require(bytes(receipt['source_package_sha256']).hex()==source['sha256']and bytes(receipt['output_package_sha256']).hex()==pin['sha256']
            and receipt['original_fields']==8 and receipt['inserted_fields']==1
            and all(receipt[k]is True for k in('outside_insertions_exact','original_selected_run_exact','existing_display_text_is_not_evaluated_or_refreshed'))
            and receipt['native_currentness_execution_or_publication_qualified']is False,'PRODUCT_PRESERVATION_RECEIPT')
        parts=payloads((r.c.ROOT/pin['path']).read_bytes());require(set(parts)==set(before)and all(parts[k]==before[k]for k in parts if k!=part),'ONLY_SELECTED_SECTION')
        elements=ET.fromstring(parts[part]);old=blocks(before[part]);new=[ET.tostring(e)for e in elements.iter()if e.tag in(ns+'fieldBegin',ns+'fieldEnd')and e.get('type')!='CROSSREF']
        # fieldEnd has no type: compare the complete original elements as an ordered subsequence.
        complete=blocks(parts[part]);cursor=0
        for item in complete:
            if cursor<len(old)and item==old[cursor]:cursor+=1
        require(cursor==len(old)and len(complete)==18,'ORIGINAL_PAIRS_PRESERVED_ONE_NEW_PAIR')
        commands=[e for e in elements.iter(ns+'fieldBegin')if e.get('type')=='CROSSREF'];require(len(commands)==1,'ONE_CROSSREF')
        values=[e.text or ''for e in commands[0].iter()if e.get('name')=='Command']
        require(len(values)==1 and hashlib.sha256(values[0].encode()).hexdigest()==bytes(receipt['command_sha256']).hex(),'EXACT_COMMAND_RECEIPT')
        rows.append(dict(case_index=index,display=case['display'],hyperlink=case['hyperlink'],output=pin,command_sha256=bytes(receipt['command_sha256']).hex()))
    require(len(list((r.c.ROOT/DIRECTORY).iterdir()))==9,'NINE_FRESH_FILES')
    return dict(schema='hwpx-agent.private.block-bookmark681-prepared-batch/v1',state='EIGHT_BLOCK_PRODUCT_CANDIDATES_NOT_NATIVE_OR_AUTHORITY',
        source_receipt=OUTPUT,source=source,cases=rows,native_execution_authorized=False,P09_complete=False)

def main():
    require(sys.argv[1:]==['--audit-existing-eight-no-rerun']and not(r.c.ROOT/OUTPUT).exists()and not(r.c.ROOT/MANIFEST).exists(),'RECOVERY_MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=binary=outputs=None;begin=time.monotonic()
    row=dict(state='FAILED683_EXISTING_BLOCK_CANDIDATES',steps=[],generator_build_or_Native_rerun=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        failed=p.codec.unpack(q.json(FAILED))
        require(q.snapshots[FAILED]['sha256']=='a3de2c031369c2bf7e01236f4e0e27d89a99556953ffc0fb5bd355c2902aec06'
            and failed['state']=='FAILED682_BLOCK_PRODUCT_EIGHT'and failed['error_code']=='BLOCK682_EXACT_OUTPUT'
            and failed['cleanup']is True and len(failed['steps'])==2
            and all(s['cleanup']and s['exit_code']==0 for s in failed['steps']),'EXACT_FAILED_AUDIT_AFTER_SUCCESSFUL_GENERATION')
        for pin in failed['source_pins']:require(q.pin(pin['path'])==pin,'ORIGINAL_SOURCE_UNCHANGED')
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for pin in failed['compiled']:require(binary.pin(pin['path'])==pin,'EXACT_ALREADY_USED_BINARY')
        q.pin(SELF)
        old=q.text('tools/p09/verify_block_bookmark_candidates682.py')
        current=q.text(SELF)
        expected=old[old.index('def inspect_outputs('):old.index('\ndef main():')].replace("0<pin['bytes']<=65536","0<pin['bytes']<=4194304")
        require(current[current.index('def inspect_outputs('):current.index('\ndef main():')]==expected,'ONLY_REPLACE_OBSOLETE_PREPARATION_SIZE_CAP_WITH_ORIGINAL_WRITER_PORT_LIMIT')
        outputs=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        manifest=inspect_outputs(outputs,failed['steps'][1]['result']);manifest['source_receipt']=OUTPUT
        row['prepared_manifest']=r.shared.publisher.publish(r.c.ROOT,MANIFEST,manifest,__import__('types').SimpleNamespace(require=r.c.require,exact=r.a.exact))
        require(row['prepared_manifest']['bytes']<16384,'BOUNDED_MANIFEST')
        binary.finish();outputs.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED683_EXISTING_EIGHT_BLOCK_CANDIDATES_NO_BUILD_GENERATOR_OR_NATIVE_RERUN',source=manifest['source'],cases=manifest['cases'],
            retained_successful_generation=failed['steps'][1],original682_failure_reclassified=False,original_CPU_RAM_and_port_limits_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'BLOCK682_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            outputs_final_fresh_hashes=0 if outputs is None else outputs.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        normalized,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark681-recovery683-forensic',row);pin=p.publish(OUTPUT,normalized)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','outputs_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED683_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
