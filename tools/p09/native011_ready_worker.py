"""Fixed inherited-event/EOF worker; no product-enabled invocation exists.

An owner must assign the real Job before the separate preparation-start token.
The original worker's P149_GO, ReadyReader and EOF rejection remain unchanged.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_ready_worker.py'
TASK='case165-current-r011-tests'
START=b'P09_NATIVE011_PREPARATION_START\n'
RESULT='implementation/p09/evidence/p09-361-native011-inherited-event-worker001.v1.json'
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
ORIGINAL=dict(path='tools/p09/native009_worker_entry_v1.py',bytes=5740,
    sha256='0124e1c8bd05363be0fe8194d4d67778d74ab0d494af7e69b3f621c8a138d602')
COMMON=dict(path='tools/p09/batch_worker_launch.py',bytes=13040,
    sha256='a643b9c1fc1cf570e688e4e8d34ef2ff38e4277aecdc96ecdd6505be45b0c02f')
PROTOCOL=dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,
    sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45')
PUBLISHER=dict(path='tools/p09/successor_preparation_workspace_v1.py',bytes=9656,
    sha256='003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98')


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_READY_WORKER_'+code)


def bootstrap(root):
    path=root/LOADER['path']
    for parent in (path,*path.parents):
        require(not parent.is_symlink() and not parent.is_junction(),'DIRECT_LOADER_ANCESTORS')
        if parent==root:break
    with path.open('rb') as stream:raw=stream.read(LOADER['bytes']+1)
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_LOADER')
    env=dict(__name__='_native011_ready_loader',__file__=LOADER['path'])
    exec(compile(raw,LOADER['path'],'exec'),env)
    return NS(**env)


class EOFOnly:
    def __init__(self,original):self.original=original;self.reads=0
    def __getattr__(self,name):return getattr(self.original,name)
    def readline(self,*args,**kwargs):
        require(self.reads==0,'ONE_ACTUAL_ORIGINAL_INPUT_READ');self.reads+=1
        raw=self.original.readline(*args,**kwargs)
        require(type(raw) is str and raw=='','ONLY_REAL_EOF_NOT_PRODUCT_GO')
        return raw


def main():
    sys.dont_write_bytecode=True
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('NATIVE011_READY_WORKER_PRODUCT_PROCESS_DENIED')
    sys.addaudithook(deny)
    require(len(sys.argv)==5 and sys.argv[1::2]==['--ready-handle','--task'] and sys.argv[4]==TASK,
        'EXACT_CLOSED_ARGUMENTS')
    # Raw one-byte reads cannot steal bytes from the original worker stdin.
    start=bytearray()
    for _ in range(len(START)+1):
        value=os.read(sys.stdin.fileno(),1);require(bool(value),'OWNER_START_REQUIRED')
        start.extend(value)
        if value==b'\n':break
    require(bytes(start)==START,'EXACT_PREPARATION_START_NOT_PRODUCT_GO')
    root=Path(__file__).resolve().parents[2]
    require(not (root/RESULT).exists(),'NEW_WORKER_RESULT')
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    host.configure_host_policy(c)
    started=time.monotonic()
    def checkpoint():require(time.monotonic()-started<600,'ORIGINAL600_PREPARATION_BOUND')
    q=a.AcceptanceReader(root,checkpoint)
    for name in (SELF,LOADER['path']):q.pin(name)
    loader=bootstrap(root)
    paths=('tools/p09/native011_preparation.py','tools/p09/native011_worker_transport.py',
        'tools/p09/native011_zlib_binding.py','tools/p09/native011_worker_preparation.py')
    pins=[q.pin(name) for name in paths]+[ORIGINAL,COMMON,PROTOCOL,PUBLISHER]
    allowed={p['path']:p for p in pins}
    class Source:
        def __init__(self,name):self.name=name
        def __fspath__(self):return os.fspath(root/self.name)
        def open(self,mode):
            require(mode=='rb' and self.name in allowed,'DECLARED_NAMESPACE_SOURCE')
            pin=allowed[self.name];before=q.maximum_parse_bytes
            try:
                q.maximum_parse_bytes=min(before,pin['bytes']+1)
                actual,raw=q._read(self.name,parse=True);q._bind(self.name,actual)
            finally:q.maximum_parse_bytes=before
            a.exact(actual,pin,'READY_WORKER_FRESH_NAMESPACE_SOURCE')
            return io.BytesIO(raw)
    class Root:
        def __fspath__(self):return os.fspath(root)
        def __truediv__(self,name):return Source(name)
    libraries,_=loader.load(Root(),pins,{})
    common=libraries.batch_worker_launch;original=libraries.native009_worker_entry_v1
    worker=libraries.native011_worker_preparation;protocol=libraries.worker_readiness_v1
    publisher=libraries.successor_preparation_workspace_v1
    require(original.TASK=='case165-current-r009-tests','ORIGINAL_ENTRY_IDENTITY')
    api=common.family(original,dict(__file__=str(root/SELF),SELF=SELF,TASK=TASK,STEP=worker.STEP))
    prepared=[];published=[]
    def prepare(actual):
        require(actual==root and not prepared,'ONE_PREPARATION_NO_RETRY');prepared.append(None)
        result=worker.prepare(root,q,a,scope,bytes_policy,loader)
        q.finish();checkpoint()
        require(q.final_fresh_hashes==len(q.snapshots) and result.linked.state.calls==0,
            'PREPARATION_CLOSING_BEFORE_REAL_READY_BOUNDARY')
        prepared[0]=result
        return result.linked,protocol
    eof=EOFOnly(sys.stdin)
    def measured(row,**options):
        require(not published and len(prepared)==1 and prepared[0] is not None,'ONE_ACTUAL_TERMINAL_REPORT')
        valid=(row.get('terminal')=='WORKER_NOT_AUTHORIZED' and row.get('actual_worker_attempts')==1
            and row.get('actual_worker_calls')==1 and row.get('raw_policy_restored') is True
            and eof.reads==1 and not denied)
        receipt_row=dict(state='PASS_ORIGINAL_INHERITED_EVENT_EOF_WORKER_NOT_PRODUCT' if valid else
            'FAILED_ORIGINAL_INHERITED_EVENT_EOF_WORKER',terminal=row,preparation=prepared[0].proof,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            closing_boundary='Preparation before original inherited-event ReadyReader; STEP fresh afterward',
            source_pins=list(q.snapshots.values()),process_creation_attempts=len(denied),
            actual_EOF_reads=eof.reads,preparation_start_authorized_by_owner=True,
            actual_product_GO_received=False,Native_Frame_or_dispatch_qualified=False)
        pin=publisher.publish(root,RESULT,receipt_row,NS(require=require,exact=a.exact));published.append(pin)
        return json.dumps(dict(row,preparation_receipt_pin=pin,actual_EOF_reads=eof.reads,
            process_creation_attempts=len(denied),actual_product_GO_received=False),**options)
    api.main.__globals__.update(prepare=prepare,json=NS(**{**vars(json),'dumps':measured}))
    before=sys.stdin
    try:
        sys.stdin=eof
        return api.main()
    finally:sys.stdin=before


if __name__=='__main__':
    raise SystemExit(main())
