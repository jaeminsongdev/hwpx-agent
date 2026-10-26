"""Generate only eight new stored candidates; retain the prior26 without replay."""
import hashlib,json,re,subprocess,sys,time,zipfile,io
from pathlib import Path
import xml.etree.ElementTree as ET
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import verify_prepared_bookmark631 as command
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_block_bookmark_candidates682.py'
HOST='crates/product-cli/tests/stored_bookmark_insertion628.rs'
HELPER='crates/product-cli/tests/support/block_bookmark_authoring679.rs'
EXAMPLE='crates/product-cli/examples/p09_block_bookmark_candidates681.rs'
ARCHIVE='implementation/p09/source-archive/p361-block-bookmark-preparation681/'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark-authoring680-product004.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark681-preparation682.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark681-prepared-batch.v1.json'
DIRECTORY='implementation/p09/evidence/private/p09-361-block-bookmark681-prepared001'
EXE='target/debug/examples/p09_block_bookmark_candidates681.exe'
DEP=EXE[:-4]+'.d'
NATIVE='implementation/p09/evidence/private/p09-361-block-bookmark670-source-document001/created.hwpx'

def require(ok,code):
    if not ok:raise ValueError('BLOCK682_'+code)

def payloads(raw):
    with zipfile.ZipFile(io.BytesIO(raw))as z:
        require(len(z.infolist())<=128 and len({i.filename for i in z.infolist()})==len(z.infolist()),'ZIP_UNIQUE_BOUNDED')
        require(all(i.file_size<=4194304 for i in z.infolist()),'PART_BOUNDED')
        return {i.filename:z.read(i.filename)for i in z.infolist()}

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
        require(pin['path']==DIRECTORY+f'/case-{index:02}.hwpx'and 0<pin['bytes']<=65536 and q.pin(pin['path'])==pin,'EXACT_OUTPUT')
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
    require(sys.argv[1:]==['--prepare-eight-no-native']and not(r.c.ROOT/OUTPUT).exists()and not(r.c.ROOT/MANIFEST).exists()
        and not(r.c.ROOT/DIRECTORY).exists(),'MODE_AND_NEW_NAMESPACE')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=binary=outputs=None;begin=time.monotonic()
    row=dict(state='FAILED682_BLOCK_PRODUCT_EIGHT',steps=[],actual_native_started=False,previous26_replayed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR));require(q.snapshots[PRIOR]['sha256']=='d017b5500d02fc1cf3dcb2c24afeb3dddb56faf19d14c71380b6c3520cffffdc'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==931,'EXACT_PRIOR26')
        for pin in prior['source_pins']:
            if pin['path'].startswith('crates/')and Path(pin['path']).suffix in('.rs','.toml'):
                name=ARCHIVE+pin['path']if pin['path']in(HOST,HELPER)else pin['path'];bound=q.pin(name)
                require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRIOR_PRODUCT_AND_TESTS_UNCHANGED')
        old=q.text(ARCHIVE+HOST);new=q.text(HOST)
        require(new==old.replace('mod block679;\n','mod block679;\npub fn fixed_block_output_batch681() -> Result<Value> { block679::fixed_block_output_batch681() }\n',1),'ONLY_HOST_GENERATOR_WRAPPER')
        helper=q.text(HELPER);start=helper.index('/// Fixed private files only');end=helper.index('#[test]',start)
        require(helper[:start]+helper[end:]==q.text(ARCHIVE+HELPER),'ONLY_NEW_GENERATOR_RETAIN_TESTS')
        names=inventory.inputs(guard.check)|includes.test_inputs((HOST,EXAMPLE),guard)|{SELF,HOST,HELPER,EXAMPLE,NATIVE}
        for name in sorted(names):q.pin(name)
        require(q.snapshots[NATIVE]['sha256']=='aa0ae8f3042a0b3be43733deb0196488bdd1bac14e6025f7785915cca5660076','EXACT_NATIVE_SOURCE')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        args=[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--features','p09-installed-format-fixture',
            '--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2',
            '--example','p09_block_bookmark_candidates681','--message-format=short']
        env=r.audit.environment();r.harness.run_one('new_normal_example681_only',args,set(),guard,env,row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NEW_EXAMPLE_CLEAN_BUILD')
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check);row['compiled']=[binary.pin(EXE),binary.pin(DEP)]
        require(deps.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'BUILD_INPUTS_PREBOUND')
        actual=command.command(guard,[str(r.c.ROOT/EXE),'--fixed-eight-private-candidates-once'],env,row,'new_product_eight_once')
        outputs=r.a.AcceptanceReader(r.c.ROOT,guard.check);manifest=inspect_outputs(outputs,actual)
        row['prepared_manifest']=p.runtime.r.shared.publisher.publish(r.c.ROOT,MANIFEST,manifest,__import__('types').SimpleNamespace(require=r.c.require,exact=r.a.exact))
        require(row['prepared_manifest']['bytes']<16384,'BOUNDED_NATIVE_INPUT_MANIFEST')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        binary.finish();outputs.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED682_EIGHT_CURRENT_STORED_BLOCK_CANDIDATES_NOT_NATIVE_OR_GATE',cases=manifest['cases'],source=manifest['source'],
            retained26_not_replayed=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'BLOCK682_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,outputs_final_fresh_hashes=0 if outputs is None else outputs.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        normalized,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark681-preparation682-forensic',row)
        pin=p.publish(OUTPUT,normalized)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','outputs_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED682_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
