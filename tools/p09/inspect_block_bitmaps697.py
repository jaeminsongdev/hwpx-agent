"""Inspect current captured24-bit BMP pixel occupancy; no Native or image rewrite."""
import hashlib,json,struct,sys,time
import run_prepared_bookmark_native631 as p
r=p.r
SELF='tools/p09/inspect_block_bitmaps697.py'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark693-capture-readback001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark697-bitmap-observation001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('XREF_BITMAP697_'+code)

def pixels(raw,checkpoint):
    require(type(raw)is bytes and 54<=len(raw)<=16777216 and raw[:2]==b'BM','BMP_BYTES')
    size,offset,dib=struct.unpack_from('<I4xII',raw,2)
    width,height,planes,depth,compression=struct.unpack_from('<iiHHI',raw,18)
    require(size==len(raw)and dib>=40 and 0<width<=4096 and 0<abs(height)<=4096
        and planes==1 and depth==24 and compression==0 and 54<=offset<len(raw),'FIXED_RGB24_PROFILE')
    stride=((width*24+31)//32)*4;n=abs(height)
    require(offset+stride*n==len(raw),'EXACT_IMAGE_ALLOCATION')
    nonwhite=0;sha=hashlib.sha256()
    order=range(n-1,-1,-1)if height>0 else range(n)
    for index,row in enumerate(order):
        if index%64==0:checkpoint()
        data=raw[offset+row*stride:offset+row*stride+width*3]
        nonwhite+=len(data)-data.count(255);sha.update(data)
    return dict(width=width,height=n,nonwhite_RGB_channels=nonwhite,all_pixels_white=nonwhite==0,
        pixel_rows_sha256=sha.hexdigest(),text_or_semantic_content_qualified=False)

def main():
    require(sys.argv[1:]==['--inspect-existing-bmp-only']and not(r.c.ROOT/OUTPUT).exists(),'MODE_IMMUTABLE')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=None;begin=time.monotonic()
    row=dict(state='FAILED697_BITMAP_OCCUPANCY',Native_started=False,images_modified=False,P09_complete=False,cases=[])
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check);q.pin(SELF)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='63412d6663f04184b91a58045eca3ecf1f84f2a4264e93afc7c2207669ba60f3'
            and prior['cleanup']is True and len(prior['cases'])==8,'EXACT693_EIGHT_OBSERVED')
        pins={pin['path']:pin for pin in prior['source_pins']}
        for index in range(1,9):
            prefix='implementation/p09/evidence/private/p09-361-prepared-bookmark'+('684'if index<=6 else'690')+f'-native001-c{index:02}/'
            observed={}
            for stage in('initial','reopened'):
                path=prefix+stage+'-page-001.bmp';require(path in pins and q.pin(path)==pins[path],'ACTUAL_PRODUCER_BOUND_IMAGE')
                observed[stage]=pixels((q.root/path).read_bytes(),guard.check)
            row['cases'].append(dict(case_index=index,stages=observed,pixel_rows_equal=observed['initial']['pixel_rows_sha256']==observed['reopened']['pixel_rows_sha256']))
        q.finish();guard.check(force=True)
        row.update(state='OBSERVED697_CURRENT_BMP_OCCUPANCY_NOT_RENDER_OR_TEXT_ACCEPTANCE',
            initial_blank_cases=[x['case_index']for x in row['cases']if x['stages']['initial']['all_pixels_white']],
            reopened_nonblank_cases=[x['case_index']for x in row['cases']if not x['stages']['reopened']['all_pixels_white']],
            initial_render_qualified=False,reopened_text_semantics_qualified=False,Native_rerun=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark697-bitmap-observation001-forensic',row)
        pin=p.publish(OUTPUT,value);print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent','initial_blank_cases','reopened_nonblank_cases')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED697_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
