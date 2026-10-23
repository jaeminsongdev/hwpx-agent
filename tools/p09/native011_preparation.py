"""Fresh fixed162 Native011 metadata construction and disk admission only.

No old qualification suite, historical raw corpus, worker/GO or product runs.
Existing outputs are never overwritten or silently reused. A partially written
package is retained for explicit recovery, not automatically retried.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
import traceback
from types import FunctionType, SimpleNamespace as NS

SELF = 'tools/p09/native011_preparation.py'
GRAPH = dict(path='implementation/p09/evidence/p09-361-case165-successor-run010-graph002.v1.json',
    bytes=11673,sha256='104a632a894608e33f51e3ea98c9e0080dd226465b3efc92dc410e3e6a899363')
ZLIB_PROOF = dict(path='implementation/p09/evidence/p09-361-case165-batch-zlib-binding-run010-qual001.v1.json',
    bytes=20096,sha256='f90bccb7e10741c5df659193c0b158f98053df0835973dd4c62fe397e64726d2')
ZLIB_CODE = ('tools/p09/batch_zlib_binding.py','tools/p09/batch_zlib_mapping.py',
    'tools/p09/zlib165_mapping_declaration_v1.py')


def require(ok, code):
    if not ok:
        raise ValueError('NATIVE011_PREPARATION_' + code)


def bounded_read(q, a, pin, limit):
    require(type(limit) is int and 0 < pin['bytes'] <= limit, 'DECLARED_READ_BOUND')
    before = q.maximum_parse_bytes
    try:
        q.maximum_parse_bytes = min(before,limit+1)
        actual, raw = q._read(pin['path'],parse=True)
        q._bind(actual['path'],actual)
    finally:
        q.maximum_parse_bytes = before
    a.exact(actual,pin,'NATIVE011_FRESH_BOUNDED_SOURCE_OR_METADATA')
    return bytes(raw)


def constructor_context(root,q,a,scope,bytes_policy,source_loader):
    """Reuse only declared constructor dependencies; no observed scope union."""
    report = a.read_exact(q,GRAPH)
    a.fields(report,dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',
        index=165,fresh_inputs=64,final_fresh_hashes=64,cleanup_confirmed=True,
        GO_authorized=False,product_or_Native_executed=False),'NATIVE011_REFERENCE_GRAPH_DECLARATION')
    known = scope.pins(report['source_pins'])
    require(len(known)==64,'REFERENCE64_NOT_RECURSIVE_HISTORY')
    a.exact(q.pin(source_loader.SELF),known[source_loader.SELF],'NATIVE011_ORIGINAL_LOADER')
    policy_pin = known['tools/p09/batch_verification.py']
    tree = ast.parse(bounded_read(q,a,policy_pin,262144))
    nodes = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='require'
        or isinstance(n,ast.ClassDef) and n.name=='PacedNamespaceLoader']
    require(len(nodes)==2,'WHOLE_ORIGINAL_PACED_LOADER_DEFINITIONS')
    env = dict(os=os,threading=threading,NS=NS,scope=scope)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),policy_pin['path'],'exec'),env)
    paced = env['PacedNamespaceLoader'](source_loader,q,known)
    libs,_ = paced.api.load(root,[known['tools/p09/'+n+'.py'] for n in
        ('ast_clone_namespace_v1','ast_copy_namespace_connection_v1')],{})
    optimized,_ = libs.ast_copy_namespace_connection_v1.connect(source_loader,libs.ast_clone_namespace_v1)
    paced = env['PacedNamespaceLoader'](optimized,q,known)
    libs,_ = paced.api.load(root,[known['tools/p09/native009_full72_construction_v1.py']],{})
    construction = libs.native009_full72_construction_v1
    known = scope.extend(known,scope.pins(construction.PINS))
    proof = a.read_exact(q,ZLIB_PROOF)
    a.fields(proof,dict(state='QUALIFIED_NEW_BINDING_AND_DISK_TRANSPORT_NOT_LIVE_NATIVE_OR_ACCEPTANCE',
        GO_authorized=False,accepted_count_delta=0,installed_in_product=False),'NATIVE011_ZLIB_DATA_PROOF_ONLY')
    current = proof['current_result']
    a.fields(current,dict(state='PASS_NEW_ZLIB_BINDING_AND_FRESH_DISK_TRANSPORT_NOT_NATIVE',descriptor_count=162,
        new_manifest_and_full_table_independently_reconstructed=True,cleanup_confirmed=True,
        fresh_inputs=79,final_fresh_hashes=79),'NATIVE011_EXISTING_FULL162_DATA_QUALIFICATION')
    require(len(current['binding_proof']['historical_roles_preserved'])==8,'UNCHANGED_EIGHT_FAILURE_ROLES')
    qualified = scope.pins(current['source_pins'])
    additions = {}
    for name in ZLIB_CODE:
        a.exact(q.pin(name),qualified[name],'NATIVE011_QUALIFIED_ZLIB_SOURCE3_UNCHANGED')
        additions[name] = dict(qualified[name])
    known = scope.extend(known,additions)
    require(len(known)<=96 and sum(p['bytes'] for p in known.values() if p['path'].endswith('.py'))<=2097152,
        'CLOSED_SOURCE_COUNT_AND_TWO_MIB_DECLARATION_BUDGET')
    paced = env['PacedNamespaceLoader'](optimized,q,known)
    loader,_ = construction.private_runtime_imports(paced.api)
    names = ('fixed162_worker_transport_v1','receipt_xz_envelope_v1','bounded_successor_capsule_wire_v2',
        'native009_parent_scope_v1','zlib165_mapping_declaration_v1','batch_zlib_mapping','current_queue_successor_binding')
    libs,_ = loader.load(root,[known['tools/p09/'+n+'.py'] for n in names],{})
    api = libs.fixed162_worker_transport_v1.connect(root,loader,scope,bytes_policy,libs.receipt_xz_envelope_v1,
        libs.bounded_successor_capsule_wire_v2,q.checkpoint,a.exact)
    return NS(loader=loader,known=known,api=api,libraries=libs,paced=paced,
        declared_source_files=len(known),declared_source_bytes=sum(p['bytes'] for p in known.values()
            if p['path'].endswith('.py')),qualified_zlib_source_pins=[additions[n] for n in ZLIB_CODE])


def main():
    import argparse
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser()
    parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args()
    require(1<=args.attempt<=8,'BOUNDED_NEW_PREPARATION_ATTEMPT')
    denied=[]
    def deny(event,arguments):
        if event in ('subprocess.Popen','os.system','os.startfile'):
            denied.append(event);raise ValueError('NATIVE011_PREPARATION_PROCESS_DENIED')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,owned_source_read_pressure as bytes_policy
    import runtime_envelope_namespace_bundle_v1 as source_loader
    import native011_worker_transport as transport,native011_zlib_binding as zlib,native011_package as package
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    row=dict(state='FAILED_NATIVE011_ACTUAL_METADATA_PACKAGE_NOT_NATIVE',stage='PREPARATION',
        product_executed=False,GO_authorized=False,accepted_count_delta=0,official_accepted_count=158,
        physical162_envelopes_freshly_verified=False,new_product_authority='PENDING_USER_REPLY')
    output=f'implementation/p09/evidence/p09-361-native011-actual-package-attempt{args.attempt:03}.v1.json'
    q=None;started=time.monotonic()
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        require(not (c.ROOT/output).exists(),'NEW_RESULT_PATH')
        for name in (zlib.MANIFEST,zlib.WIRE,zlib.BOOTSTRAP):
            path=c.ROOT/name
            require(not path.exists() and not path.is_symlink() and not path.is_junction(),'ALL_NEW_PACKAGE_PATHS_UNUSED')
        for name in (SELF,transport.SELF,zlib.SELF,package.SELF):q.pin(name)
        worker=transport.connect(bounded_read(q,a,transport.SOURCE,65536))
        binding=zlib.connect(bounded_read(q,a,zlib.SOURCE,65536))
        row['stage']='FRESH_CONSTRUCTOR_CONTEXT'
        context=constructor_context(c.ROOT,q,a,scope,bytes_policy,source_loader)
        row['source_declaration']=dict(files=context.declared_source_files,bytes=context.declared_source_bytes,
            current_Native_source_scope=False)
        print(json.dumps(dict(stage=row['stage'],source_declaration=row['source_declaration'])),flush=True)
        declaration=context.libraries.zlib165_mapping_declaration_v1
        read=lambda p,limit:bounded_read(q,a,p,limit)
        previous=json.loads(read(declaration.REFERENCE_BOOTSTRAP,16384).decode('ascii'))
        reference,reference_proof=context.api.reconstruct(previous,read(declaration.REFERENCE_WIRE,16384),guard.check)
        row['stage']='NEW_FULL162_PACKAGE_CONSTRUCTION'
        constructor=NS(**vars(context.api),read_reference=read)
        prepared=package.prepare(c.ROOT,context.loader,context.known,constructor,
            context.libraries.bounded_successor_capsule_wire_v2,bytes_policy,reference,previous,declaration,
            context.libraries.batch_zlib_mapping,context.libraries.current_queue_successor_binding,
            binding,worker,guard.check)
        row.update(package_construction=prepared.proof,proposed_payload_pins=prepared.pins)
        row['stage']='EXCLUSIVE_PACKAGE_PUBLICATION'
        published=[]
        for name,raw,limit in prepared.payloads:
            require(not (c.ROOT/name).exists(),'PACKAGE_STILL_UNUSED_BEFORE_EXCLUSIVE_PUBLICATION')
            published.append(context.libraries.native009_parent_scope_v1.publish_bytes(
                c.ROOT,name,raw,q,guard,bytes_policy,a,limit))
            row['published_pins']=list(published)
        row['stage']='INDEPENDENT_FRESH_DISK_ENTRY'
        def reconstruct(prior,packet,check):
            old,proof=context.api.reconstruct(prior,packet,check)
            new=binding.connect(c.ROOT,context.loader,scope,old,declaration,
                context.libraries.batch_zlib_mapping,context.libraries.current_queue_successor_binding,check)
            return new,proof
        def graph(reference,step,check):
            item=binding.worker_graph(c.ROOT,context.loader,context.known,context.api,
                context.libraries.bounded_successor_capsule_wire_v2,bytes_policy,reference,step,declaration,worker,check)
            return item.graph,item.runtime
        rebuild=binding.entry_reconstructor(worker,context.api.metadata)
        actual=rebuild(transport.TASK,published[2],read,reconstruct,graph,guard.check)
        a.exact(actual.graph.binding.descriptors(),prepared.entry.graph.binding.descriptors(),
            'NATIVE011_FRESH_DISK_WHOLE162_NOT_REBASED')
        a.exact(dict(actual.graph.binding.manifest_pin),published[0],'NATIVE011_FRESH_DISK_MANIFEST')
        require(actual.proof['metadata_byte_admissions']==4 and not denied,'FOUR_FRESH_DISK_INPUTS_AND_NO_PROCESS')
        row['stage']='FINAL_FRESH_SOURCE_READS';q.finish();guard.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots),'COMPLETE_CLOSING_SOURCE_AND_METADATA_HASHES')
        row.update(state='PASS_NATIVE011_REAL162_METADATA_CONSTRUCTED_AND_FRESH_DISK_ENTRY_NOT_NATIVE',
            descriptor_count=162,entry_proof=actual.proof,reference_proof=reference_proof,
            original009_reconstructions=context.api.state.reconstructions,
            original009_actual162_decodes=context.api.state.actual162_decodes,
            prior_suites_reexecuted=False,worker_or_dispatch_or_live_Frame_qualified=False,
            installed_in_product=False)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError,NameError,ImportError) as error:
        row['error_type']=type(error).__name__
        row['error_code']=error.args[0] if error.args and type(error.args[0]) is str and re.fullmatch(
            '[A-Za-z0-9_]{1,160}',error.args[0]) else 'CLOSED_ACTUAL_PREPARATION_FAILED'
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-5:]]
    finally:
        guard.close()
        row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=guard.samples,
            subprocess_creation_attempts=len(denied))
        if guard.cleanup is not True:row['state']='FAILED_NATIVE011_PREPARATION_CLEANUP'
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],stage=row['stage'],error_code=row.get('error_code'),
            error_frames=row.get('error_frames'),cleanup=row['cleanup_confirmed'],fresh=row['fresh_inputs'],
            final=row['final_fresh_hashes'],elapsed=row['elapsed_seconds'],published_pins=row.get('published_pins',[]),
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            available_RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':
    raise SystemExit(main())
