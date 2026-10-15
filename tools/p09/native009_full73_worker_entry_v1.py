"""Production73 startup; original main/GO/Job/execute functions are retained.

The new preparation path selects the qualified73 transport and exact v4 pins.
Not a Native dispatcher, product permission or current whole-Frame acceptance.
No diagnostic denial is installed in this production entry.
"""
import sys
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native009_full73_worker_entry_v1.py'
TASK='case165-current-r009-tests'
PREFIX='implementation/p09/evidence/p09-361-case165-'
OLD_ENTRY=dict(path='tools/p09/native009_worker_entry_v1.py',bytes=5740,
    sha256='0124e1c8bd05363be0fe8194d4d67778d74ab0d494af7e69b3f621c8a138d602')
OLD_LAUNCH=dict(path='tools/p09/native009_worker_launch_v1.py',bytes=4057,
    sha256='30088c308a7294dec10c295bcaba1d396382a7194541e5e21bd599dc03762f4b')
TRANSPORT=dict(path='tools/p09/native009_full73_transport_v1.py',bytes=23590,
    sha256='ad415de73edfefbf6263266511807a707330480eac996697e36c9101bbf2bc26')
CONSTRUCTION=dict(path='tools/p09/native009_full72_construction_v1.py',bytes=20322,
    sha256='2303cfa1be8e3d5f3468a4891cc9e840003e21fa6383d79dfde90f6c0b78ad8b')
PROTOCOL=dict(path='tools/p09/worker_readiness_v1.py',bytes=6890,
    sha256='047c3f78f8a4472feeec4d56b65716f57e0429091321cb49afe5b685047d3a45')
HINT=dict(path=PREFIX+'successor-worker-bootstrap009.v4.json',bytes=12799,
    sha256='8504c8df540eb422ab058abcaadac38c1dd3e459f14b9131ae252fdae47845e6')
WIRE=dict(path=PREFIX+'successor-worker-capsule009.compact.v4.json',bytes=10447,
    sha256='ec3bbe77f6c83c1c353d6520022075ec3663e6b345881824301ff41140390cce')
STEP=dict(path=PREFIX+'step-config001.v1.json',bytes=685,
    sha256='2b549a20ad4f46b7d146b935b0ff103e92db0411ad195f6038457e994b973e7c')


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_FULL73_ENTRY_'+label)


def family(original,function,updates):
    before=getattr(original,function).__globals__;env=dict(before,**updates);proofs=[]
    for name,old in tuple(vars(original).items()):
        if type(old) is FunctionType and old.__globals__ is before:
            fn=FunctionType(old.__code__,env,name=old.__name__,argdefs=old.__defaults__,closure=old.__closure__)
            fn.__kwdefaults__=old.__kwdefaults__
            require(fn.__code__ is old.__code__ and fn.__defaults__ is old.__defaults__ and fn.__closure__ is old.__closure__,
                'WHOLE_ORIGINAL_FUNCTION_CODE_DEFAULTS_CLOSURE')
            env[name]=fn;proofs.append(dict(function=name,whole_original_code_defaults_closure_retained=True))
    return NS(**{**vars(original),**env}),env,proofs


def worker_api(root,envelope,loader):
    originals,_=loader.load(root,[OLD_ENTRY],{})
    original=originals.native009_worker_entry_v1
    api,env,proofs=family(original,'main',dict(__file__=str(root/SELF),SELF=SELF,HINT=HINT,WIRE=WIRE,STEP=STEP))
    def prepare(actual_root):
        require(actual_root==root,'SAME_EXPLICIT_REPOSITORY')
        import conservative_maintenance as c
        c.Windows();require(c.ROOT==root,'SAME_CONFIGURED_ROOT')
        import accept_case112_current_epoch as a
        import current_stored_runtime_scope as scope
        import owned_source_read_pressure as bytes_policy
        bootstrap,_=envelope.namespace_bundle.load(root,[CONSTRUCTION,PROTOCOL],{})
        construction=bootstrap.native009_full72_construction_v1
        selected={'prepared_run_closure_v1','ast_clone_namespace_v1','ast_copy_namespace_connection_v1',
            'receipt_xz_envelope_v1','bounded_successor_capsule_wire_v2',
            'post_product_recovery_window_v1','post_product_recovery_connection_v1'}
        pins=[p for p in construction.PINS if p['path'].rsplit('/',1)[-1][:-3] in selected]+[TRANSPORT]
        require(len(pins)==8,'CLOSED_PRODUCTION_SOURCE_GRAPH8')
        libs,_=envelope.namespace_bundle.load(root,pins,{})
        libs.prepared_run_closure_v1.configure_host_policy(c)
        current,_=libs.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,libs.ast_clone_namespace_v1)
        current,imports=construction.private_runtime_imports(current)
        import json
        hint=json.loads(env['read'](root,HINT));wire=env['read'](root,WIRE);env['read'](root,STEP)
        transport=libs.native009_full73_transport_v1
        connected=transport.connect(root,current,scope,bytes_policy,libs.receipt_xz_envelope_v1,
            libs.bounded_successor_capsule_wire_v2,lambda:None,a.exact)
        graph,_=connected.reconstruct(hint,wire,lambda:None)
        linked=connected.build(root,current,connected,graph,envelope.prior,libs.post_product_recovery_connection_v1,
            libs.post_product_recovery_window_v1,lambda:None)
        require(linked.state.calls==linked.state.attempts==0 and len(graph.binding.descriptors())==73,'WHOLE73_NOT_YET_EXECUTED')
        require(len(imports)==1 and linked.window.WINDOW.SECONDS==10,'PRIVATE_IMPORT_AND_ORIGINAL_WINDOW10')
        return linked,bootstrap.worker_readiness_v1
    env['prepare']=prepare;api.prepare=prepare
    api.original_api=original;api.family_proofs=proofs
    api.preparation_implementation_is_new_v4_with_original_worker_body=True
    return api


def launch_api(root,loader):
    originals,_=loader.load(root,[OLD_LAUNCH],{})
    original=originals.native009_worker_launch_v1
    api,env,proofs=family(original,'connect',dict(ENTRY=SELF))
    require(original.ENTRY=='tools/p09/native009_worker_entry_v1.py' and api.ENTRY==SELF,'ONE_EXPLICIT_ENTRY_METADATA_DEPENDENCY')
    api.original_api=original;api.family_proofs=proofs
    return api


def main():
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/p09'))
    import conservative_maintenance as c
    c.Windows()
    import flat_current_queue_envelope_runtime_v25 as envelope
    api=worker_api(root,envelope,envelope.namespace_bundle)
    return api.main()


if __name__=='__main__':raise SystemExit(main())
