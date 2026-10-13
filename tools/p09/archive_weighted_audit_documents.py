"""Whole r53 documents before P176 progress; bounded text-only reads."""
import base64
import hashlib
import json
import xml_initial_capacity_binding as b
import weighted_audit_io as w
SELF='tools/p09/archive_weighted_audit_documents.py'
ARCHIVE='implementation/p09/source-archive/p09-176-pre-progress-r54/document-preimages.v1.json'

def main():
    destination=b.s.scoped_path(ARCHIVE,fresh=True);resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',product_complete=False,P09_gate='OPEN',goal_status='active')
    try:
        resources.admit();q=w.WeightedLiveReader(resources);q.pin(SELF);files=[]
        for name in b.DOCS:
            raw=q.text(name).encode();pin=q.reader.snapshots[name]
            b.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'P176_RAW_DOCUMENT_BYTES')
            files.append(dict(**pin,base64=base64.b64encode(raw).decode()))
        q.finish();out.update(state='WHOLE_P176_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('WHOLE_') else 2

if __name__=='__main__':raise SystemExit(main())
