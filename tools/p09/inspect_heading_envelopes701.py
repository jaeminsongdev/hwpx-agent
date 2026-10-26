"""Observe conditional heading declarations in current32 files; select no branch."""
import hashlib,json,sys,time,zipfile,xml.etree.ElementTree as ET
import run_prepared_bookmark_native631 as p
r=p.r
SELF='tools/p09/inspect_heading_envelopes701.py'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
PRODUCT='implementation/p09/evidence/p09-361-block-bookmark700-field-api002.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark701-heading-observation001.v1.json'
HH='{http://www.hancom.co.kr/hwpml/2011/head}'
HP='{http://www.hancom.co.kr/hwpml/2011/paragraph}'
def require(ok,code):
    if not ok:raise ValueError('XREF_HEAD701_'+code)
def inspect(root,path):
    with zipfile.ZipFile(root/path)as z:
        infos=z.infolist();require(len(infos)<=128 and sum(i.file_size for i in infos)<=8388608,'ZIP_BOUND')
        info=z.getinfo('Contents/header.xml');require(info.file_size<=4194304,'HEADER_BOUND');raw=z.read(info)
    require(b'<!DOCTYPE'not in raw.upper()and b'<!ENTITY'not in raw.upper(),'NO_DTD_ENTITY')
    head=ET.fromstring(raw);require(head.tag==HH+'head','HEADER_NAMESPACE')
    parents={c:parent for parent in head.iter()for c in parent};decls=list(head.iter(HH+'heading'));conditions=[]
    for para in head.iter(HH+'paraPr'):
        for switch in para:
            if switch.tag!=HP+'switch'or not any(x.tag==HH+'heading'for x in switch.iter()):continue
            branches=[]
            for branch in switch:
                kinds=[x for x in branch if x.tag==HH+'heading'];require(len(kinds)==1,'OBSERVED_SINGLE_HEADING_BRANCH')
                value=kinds[0];branches.append(dict(kind=branch.tag.removeprefix(HP),required_namespace=branch.get(HP+'required-namespace'),
                    heading_type=value.get('type'),id_ref=value.get('idRef'),level=value.get('level')))
            conditions.append(dict(paragraph_property_id=para.get('id'),branches=branches,
                branches_equivalent=len({(x['heading_type'],x['id_ref'],x['level'])for x in branches})==1))
    return dict(header_sha256=hashlib.sha256(raw).hexdigest(),heading_elements=len(decls),
        direct_heading_elements=sum(parents[x].tag==HH+'paraPr'for x in decls),conditional_definitions=conditions,
        effective_branch_selected=False,Native_heading_or_numbering_qualified=False)
def main():
    require(sys.argv[1:]==['--observe-existing-header-only']and not(r.c.ROOT/OUTPUT).exists(),'MODE_IMMUTABLE')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=None;begin=time.monotonic()
    row=dict(state='FAILED701_HEADING_ENVELOPES',cases=[],Native_started=False,heading_importer_or_main_Source_changed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check);q.pin(SELF)
        product=p.codec.unpack(q.json(PRODUCT),guard.check);require(q.snapshots[PRODUCT]['sha256']=='e6a58b22e9d292f55f5ed432c57d1380bf8751e2a114053306380d4e6fe2394b'
            and product['cleanup']is True and product['actual_current_product_documents']==32,'EXACT_FIELD_API_PRODUCT_PROOF')
        manifest=q.json(MANIFEST)
        for case in manifest['cases']:
            stages={}
            for stage,item in case['stages'].items():
                pin=item['pin'];require(q.pin(pin['path'])==pin,'CURRENT_FILE_PIN');guard.check();stages[stage]=inspect(q.root,pin['path'])
            row['cases'].append(dict(case_index=case['case_index'],stages=stages))
        q.finish();guard.check(force=True);row['state']='OBSERVED701_CONDITIONAL_CANDIDATE_HEADERS_AND_NATIVE_SAVED_HEADERS_NO_BRANCH_SELECTION'
    except(ValueError,OSError,KeyError,TypeError,AttributeError,ET.ParseError,zipfile.BadZipFile,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark701-heading-observation001-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds')},
            'stage_counts':{stage:sorted(set((x['stages'][stage]['heading_elements'],x['stages'][stage]['direct_heading_elements'],len(x['stages'][stage]['conditional_definitions']))for x in row['cases']))for stage in('candidate','initial','saved','reopened')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED701_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
