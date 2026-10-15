"""Exact production worker entry; original GO, Job, policy and worker retained.

This is not a Native dispatcher. Its caller must admit and hold the complete
source Frame, qualify the current cost/helper path, and own the actual Job.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

SELF='tools/p09/native009_worker_entry_v1.py'
TASK='case165-current-r009-tests'
PREFIX='implementation/p09/evidence/p09-361-case165-'
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
PROTOCOL=dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,
    sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45')
HINT=dict(path=PREFIX+'successor-worker-bootstrap009.v3.json',bytes=11606,
    sha256='c09c3d7ad4129fc83b1181de4a595e12e8cd93108a3a4af24b12336806712c5c')
WIRE=dict(path=PREFIX+'successor-worker-capsule009.compact.v3.json',bytes=10295,
    sha256='e75ab40944945f0a7ae995041dbc6c9a56dae405066156869e2b8910d4e49556')
STEP=dict(path=PREFIX+'step-config001.v1.json',bytes=685,
    sha256='2b549a20ad4f46b7d146b935b0ff103e92db0411ad195f6038457e994b973e7c')


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_WORKER_ENTRY_'+label)


def arguments(argv):
    require(type(argv) is list and len(argv)==4 and argv[::2]==['--ready-handle','--task']
        and argv[3]==TASK,'EXACT_READY_HANDLE_AND_CURRENT_TASK9')
    value=argv[1]
    require(type(value) is str and re.fullmatch('[1-9][0-9]{0,19}',value) is not None
        and int(value)<2**64,'EXACT_INHERITED_HANDLE_INTEGER')
    return int(value)


def read(root,pin,limit=16384):
    require(type(pin['bytes']) is int and 0<pin['bytes']<=limit,'BOUNDED_SOURCE_METADATA')
    path=root/pin['path']
    for ancestor in (path.parent,*path.parent.parents):
        require(ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction(),'DIRECT_ANCESTORS')
        if ancestor==root:break
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_FILE')
    with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
    require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'FRESH_EXACT_PIN')
    return raw


def prepare(root):
    sys.path.insert(0,str(root/'tools/p09'))
    import conservative_maintenance as c
    c.Windows();require(c.ROOT==root,'SAME_ROOT')
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    bootstrap,_=envelope.namespace_bundle.load(root,[CONSTRUCTION,PROTOCOL],{})
    construction=bootstrap.native009_full72_construction_v1
    selected={'prepared_run_closure_v1','ast_clone_namespace_v1','ast_copy_namespace_connection_v1',
        'receipt_xz_envelope_v1','bounded_successor_capsule_wire_v2','native009_full72_transport_v1',
        'post_product_recovery_window_v1','post_product_recovery_connection_v1'}
    pins=[p for p in construction.PINS if p['path'].rsplit('/',1)[-1][:-3] in selected]
    require(len(pins)==len(selected),'CLOSED_PRODUCTION_SOURCE_GRAPH8')
    libs,_=envelope.namespace_bundle.load(root,pins,{})
    libs.prepared_run_closure_v1.configure_host_policy(c)
    loader,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
    loader,proofs=construction.private_runtime_imports(loader)
    hint=json.loads(read(root,HINT));wire=read(root,WIRE);read(root,STEP)
    api=libs.native009_full72_transport_v1.connect(root,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
        libs.bounded_successor_capsule_wire_v2,lambda:None,a.exact)
    graph,_=api.reconstruct(hint,wire,lambda:None)
    linked=api.build(root,loader,api,graph,envelope.prior,libs.post_product_recovery_connection_v1,
        libs.post_product_recovery_window_v1,lambda:None)
    require(linked.state.calls==linked.state.attempts==0 and len(graph.binding.descriptors())==72,'WHOLE72_NOT_YET_EXECUTED')
    require(len(proofs)==1 and linked.window.WINDOW.SECONDS==10,'PRIVATE_IMPORT_AND_ORIGINAL_WINDOW10')
    return linked,bootstrap.worker_readiness_v1


def execute(linked,protocol,handle):
    event=protocol.WindowsEvent(handle);stdin=sys.stdin
    try:
        sys.stdin=protocol.ReadyReader(stdin,event)
        return linked.execute(TASK)
    finally:sys.stdin=stdin;event.close()


def main():
    handle=arguments(sys.argv[1:]);root=Path(__file__).resolve().parents[2]
    linked,protocol=prepare(root)
    try:return execute(linked,protocol,handle)
    except ValueError as error:
        # Closed failure metadata only, never raw logs or arbitrary values.
        code='WORKER_NOT_AUTHORIZED' if error.args==('WORKER_NOT_AUTHORIZED',) else 'NATIVE009_WORKER_EXECUTION_FAILED'
        read(root,STEP)
        helpers={Path(filename).absolute() for module in tuple(sys.modules.values()) if (filename:=getattr(module,'__file__',None))
            and Path(filename).absolute().is_relative_to(root/'tools/p09')}
        print(json.dumps(dict(terminal=code,task=TASK,descriptor_count=len(linked.graph.binding.descriptors()),
            actual_worker_attempts=linked.state.attempts,actual_worker_calls=linked.state.calls,
            raw_policy_restored=linked.policy.restored,original_worker_code=Path(linked.original_worker.__code__.co_filename).name,
            child_default_project_helper_count=len(helpers),source_step_pin_checked_before_after=True,
            Native_source_Frame_or_acceptance_qualified=False)),file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
