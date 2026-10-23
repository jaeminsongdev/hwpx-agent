"""Explicit zlib package profile for the existing worker preparation path.

The source3/file3 qualification is reused, not the former runtime's whole
source inventory. Current worker and this profile are separately fresh inputs.
No GO, product execution, publisher, or automatic acceptance is provided.
"""
from types import SimpleNamespace as NS

SELF='tools/p09/batch_zlib_runtime.py'
TEST='tools/p09/tests/test_batch_zlib_runtime.py'
QUALIFICATION=dict(path='implementation/p09/evidence/p09-361-case165-batch-zlib-binding-run010-qual001.v1.json',
    bytes=20096,sha256='f90bccb7e10741c5df659193c0b158f98053df0835973dd4c62fe397e64726d2')
CODE=('tools/p09/batch_zlib_binding.py','tools/p09/batch_zlib_mapping.py','tools/p09/zlib165_mapping_declaration_v1.py')
PACKAGE=(
    dict(path='implementation/p09/evidence/p09-361-case165-successor-run010-zlib-manifest001.v1.json',
        bytes=99480,sha256='bd6eec32a2b9be4e75fd9831e89b18d83ba1d9202ca8e4e156f04492e7249d2e'),
    dict(path='implementation/p09/evidence/p09-361-case165-successor-worker-capsule010.compact.zlib.v1.json',
        bytes=15058,sha256='e080c18a4862785a6e903eb77dd7aeae7bd544ceb54ae831f835fe7f3f3bbb49'),
    dict(path='implementation/p09/evidence/p09-361-case165-successor-worker-bootstrap010.zlib.v1.json',
        bytes=4898,sha256='4a161c79587a300f0c2b053f4a275e5cae4c49cf53ab9e54432861b039812d93'))


def require(ok,code):
    if not ok:raise ValueError('ZLIB_RUNTIME_'+code)


def admit(root,q,a,scope,report,known,worker_path):
    """Keep producer64 intact, then admit only the explicit new code inputs."""
    require(worker_path=='tools/p09/batch_worker_launch.py','ONE_OWNED_WORKER_ENTRY')
    proof=a.read_exact(q,QUALIFICATION)
    a.fields(proof,dict(state='QUALIFIED_NEW_BINDING_AND_DISK_TRANSPORT_NOT_LIVE_NATIVE_OR_ACCEPTANCE',
        GO_authorized=False,accepted_count_delta=0,installed_in_product=False),'PACKAGE_DATA_QUALIFICATION_ONLY')
    current=proof['current_result']
    a.fields(current,dict(state='PASS_NEW_ZLIB_BINDING_AND_FRESH_DISK_TRANSPORT_NOT_NATIVE',
        descriptor_count=162,new_manifest_and_full_table_independently_reconstructed=True,
        cleanup_confirmed=True,fresh_inputs=79,final_fresh_hashes=79),'FULL162_QUALIFIED_PACKAGE')
    a.exact(current['publication_pins'],list(PACKAGE),'EXACT_DISTINCT_ZLIB_PACKAGE_NOT_OLD010')
    require(len(current['binding_proof']['historical_roles_preserved'])==8,'ALL_EIGHT_HISTORICAL_ROLES')
    source=scope.pins(current['source_pins'])
    additions={}
    for name in CODE:
        require(name in source,'NAMED_QUALIFIED_SOURCE3')
        a.exact(q.pin(name),source[name],'UNCHANGED_QUALIFIED_PACKAGE_SOURCE')
        additions[name]=dict(source[name])
    for name in (SELF,worker_path):additions[name]=dict(q.pin(name))
    known=scope.extend(known,additions)
    report=dict(report,manifest_pin=dict(PACKAGE[0]),wire_pin=dict(PACKAGE[1]),bootstrap_pin=dict(PACKAGE[2]),
        zlib_package_qualification_pin=dict(QUALIFICATION),
        reused_qualification_scope='Exact source3 and file3, not former worker/Native source closure')
    return report,known


def reconstruct(root,q,a,scope,loader,known,api,bounded,bytes_policy,worker,report,read):
    """Run original entry admission with a distinct fresh full162 Binding."""
    libraries,_=loader.load(root,[known[n] for n in CODE+('tools/p09/current_queue_successor_binding.py',)],{})
    binding,mapping,declaration,bindings=(getattr(libraries,n) for n in
        ('batch_zlib_binding','batch_zlib_mapping','zlib165_mapping_declaration_v1','current_queue_successor_binding'))
    a.exact(declaration.QUALIFICATION,
        dict(path='implementation/p09/evidence/p09-361-case165-batch-zlib-files-run010-qual001.v1.json',
             bytes=105093,sha256='cfb2795d9dab562ba5a589b5e8b25a3be20db83ac9b9c4e821c852d2fbfa7d83'),
        'ORIGINAL_FRESH_FILE_QUALIFICATION_NOT_REPLACED')
    references=[]
    def reference_factory(prior,packet,check):
        old,proof=api.reconstruct(prior,packet,check)
        a.exact(dict(old.binding.manifest_pin),dict(declaration.REFERENCE_MANIFEST),'ORIGINAL009_ROOT')
        new=binding.connect(root,loader,scope,old,declaration,mapping,bindings,check)
        a.exact(new.manifest_pin,PACKAGE[0],'NEW_MANIFEST_FROM_WHOLE_ORIGINAL_CONSTRUCTOR')
        references.append(new)
        return new,proof
    def transport_factory(reference,step,check):
        selected=binding.worker_graph(root,loader,known,api,bounded,bytes_policy,reference,step,declaration,worker,check)
        return selected.graph,selected.runtime
    rebuild=binding.entry_reconstructor(worker,api.metadata)
    entry=rebuild('case165-current-r010-tests',report['bootstrap_pin'],read,reference_factory,transport_factory,q.checkpoint)
    require(len(references)==1 and entry.graph.binding is not references[0].binding,'FRESH_WIRE_CONSTRUCTOR_NOT_REFERENCE_REUSE')
    a.exact(entry.graph.binding.descriptors(),references[0].binding.descriptors(),'ACTUAL_NEW_FULL162')
    a.exact(dict(entry.graph.binding.manifest_pin),PACKAGE[0],'ACTUAL_NEW_MANIFEST')
    return NS(**{**vars(entry),'proof':dict(entry.proof,
        zlib_profile=True,qualified_source3_checked=True,full_reference_constructor_and_new_binding=True,
        reused_corpus648_suite=False,original_failures_not_promoted=True,
        current_worker_or_Native_or_GO_qualified=False)})


def terminal_evidence(linked,row):
    """Add only measured preparation identity; preserve original EOF fields."""
    require(type(row) is dict and row.get('terminal')=='WORKER_NOT_AUTHORIZED'
        and row.get('task')=='case165-current-r010-tests' and row.get('descriptor_count')==162,
        'ORIGINAL_EOF_TERMINAL_BEFORE_PROFILE_EVIDENCE')
    proof=linked.preparation_evidence
    require(proof.get('zlib_profile') is True and type(proof.get('fresh_inputs')) is int
        and proof['fresh_inputs']>0 and proof['final_fresh_hashes']==proof['fresh_inputs'],
        'ACTUAL_COMPLETED_PREPARATION_NOT_EXPECTATIONS')
    require(proof.get('package_pins')==list(PACKAGE) and proof['entry_proof'].get('zlib_profile') is True,
        'ACTUAL_NEW_PACKAGE_AND_ENTRY')
    source={p['path']:dict(p) for p in proof['source_pins']}
    selected=CODE+(SELF,'tools/p09/batch_worker_launch.py')
    require(all(n in source for n in selected),'ALL_FIVE_PROFILE_SOURCES_MEASURED')
    return dict(row,zlib_preparation=dict(package_pins=proof['package_pins'],
        fresh_inputs=proof['fresh_inputs'],final_fresh_hashes=proof['final_fresh_hashes'],
        actual_entry_metadata_reads=proof['entry_proof']['metadata_byte_admissions'],
        source_pins=[source[n] for n in selected],Native_or_GO_qualified=False))
