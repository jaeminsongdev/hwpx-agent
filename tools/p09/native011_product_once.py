"""One externally authorized Native011 entry, never an acceptance mechanism.

The persistent claim is an execution-coordination OUTPUT, not source/Native
byte credit or an approval. Default authority is absent. A real caller must
use the attested original publisher and the complete original entry lifecycle;
this library alone does not build that lifecycle or execute a CLI product.
"""
import hashlib
import os
from pathlib import Path
import re
import sys
import threading
from types import CodeType, FunctionType

SELF='tools/p09/native011_product_once.py'
TEST='tools/p09/tests/test_native011_product_once.py'
CLAIM='implementation/p09/evidence/p09-361-case165-native011-product-once-intent.v1.json'
PUBLISHER=dict(path='tools/p09/successor_preparation_workspace_v1.py',bytes=9656,
    sha256='003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98')
AUTHORITY=dict(path='tools/p09/native011_product_authority_connection.py',bytes=10143,
    sha256='5f6baf945bfd91123249b1cb0629c97c06619ef77045c3cf1d869691cbe195a7')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-product-once-entry-construct001.v1.json'
RUNTIME='implementation/p09/evidence/p09-361-case165-current-runtime-run011.v1.json'


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_PRODUCT_ONCE_'+code)


def intent():
    return dict(state='EXCLUSIVE_NATIVE011_ENTRY_INTENT_NOT_GO_OR_COMPLETION',index=165,physical_run=11,
        Native_or_product_or_GO_already_executed=False,queue_acceptance_authorized=False,
        file_is_not_external_execution_authority=True,automatic_retry_permitted=False)


def claim_writer(raw,publisher,root,api):
    """Capture the whole original xb/flush/fsync publisher, no IO on binding."""
    require(type(raw) is bytes and len(raw)==PUBLISHER['bytes']
        and hashlib.sha256(raw).hexdigest()==PUBLISHER['sha256'],'EXACT_ORIGINAL_PUBLISHER_SOURCE')
    function=publisher.publish
    require(type(function) is FunctionType
        and function.__code__.co_filename.replace('\\','/').endswith(PUBLISHER['path']),'ORIGINAL_PUBLISHER_FUNCTION_ORIGIN')
    expected=[value for value in compile(raw,function.__code__.co_filename,'exec').co_consts
        if type(value) is CodeType and value.co_name=='publish']
    require(len(expected)==1 and expected[0]==function.__code__,'ENTIRE_ORIGINAL_EXCLUSIVE_FSYNC_PUBLISHER')
    code=function.__code__
    def write(value):
        original=intent()
        require(type(value) is dict and set(value)==set(original)
            and all(type(value[name]) is type(item) and value[name]==item for name,item in original.items()),
            'EXACT_ONCE_INTENT_NOT_APPROVAL_OR_COMPLETION')
        require(function.__code__ is code,'ORIGINAL_PUBLISHER_CODE_UNCHANGED_BEFORE_CLAIM')
        return function(root,CLAIM,value,api)
    return write


class Once:
    def __init__(self,checkpoint,*,authorize=None):
        require(callable(checkpoint) and (authorize is None or callable(authorize)),
            'EXPLICIT_GUARD_AND_OPTIONAL_EXTERNAL_AUTHORITY_NOT_FLAGS')
        self.checkpoint=checkpoint;self.external=authorize;self.owner=(os.getpid(),threading.get_ident())
        self._authority_origin=(authorize,)
        self.phase='NEW';self.invocations=0;self.external_calls=0;self.intent_attempts=0
        self.claim_pin=None;self.native_authorizations=0;self.entry_calls=0;self.failed=False
        self.error_type=None;self.error_code=None
    def owner_check(self):
        require((os.getpid(),threading.get_ident())==self.owner,'SAME_OWNER_PROCESS_THREAD')
        require(type(self._authority_origin) is tuple and len(self._authority_origin)==1
            and self.external is self._authority_origin[0],'AUTHORITY_DEPENDENCY_FIXED_AT_CREATION')
    def fail(self,error):
        if not self.failed:
            self.error_type=type(error).__name__;value=error.args[0] if error.args else None
            self.error_code=(value if type(value) is str and value.startswith(('NATIVE011_PRODUCT_ONCE_','STOP_'))
                and re.fullmatch('[A-Z0-9_]{1,160}',value) else 'ORIGINAL_ENTRY_ERROR')
        self.phase='FAILED';self.failed=True
    def _checked(self,phase):
        self.checkpoint()
        require(not self.failed and self.phase==phase,'NO_CAUGHT_FAILURE_OR_PHASE_CHANGE_AT_CHECKPOINT')
    def authorize_native(self):
        """Dependency for the unchanged original parent execute(). Not a GO."""
        self.owner_check()
        try:
            require(self.phase=='ENTRY' and not self.failed and self.claim_pin is not None
                and self.native_authorizations==0 and self.entry_calls==1,'ONE_CLAIMED_ORIGINAL_NATIVE_ENTRY_ONLY')
            self.native_authorizations=1
            self._checked('ENTRY')
            require(self.native_authorizations==1,'SAME_ORIGINAL_NATIVE_AUTHORIZATION_AFTER_GUARD')
            return True
        except BaseException as error:self.fail(error);raise
    def execute(self,entry,write_intent):
        """No retry and no synthesized completion, Frame commit or case result."""
        self.owner_check();require(self.invocations==0 and self.phase=='NEW' and not self.failed,'ONE_INVOCATION_NO_RETRY')
        self.invocations=1
        try:
            require(callable(entry) and callable(write_intent),'EXPLICIT_COMPLETE_ENTRY_AND_CLAIM_WRITER')
            self._checked('NEW')
            require(self.external is not None,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED')
            self.external_calls=1
            require(self.external() is True,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED')
            self._checked('NEW');self.phase='CLAIMING';self.intent_attempts=1
            pin=write_intent(intent())
            require(not self.failed and self.phase=='CLAIMING','NO_CAUGHT_FAILURE_DURING_CLAIM')
            require(type(pin) is dict and set(pin)=={'path','bytes','sha256'} and pin['path']==CLAIM
                and type(pin['bytes']) is int and 0<pin['bytes']<=262144
                and type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}',pin['sha256']),
                'EXACT_PERSISTED_ORIGINAL_INTENT_PIN')
            self.claim_pin=dict(pin);self._checked('CLAIMING');self.phase='ENTRY';self.entry_calls=1
            result=entry()
            require(not self.failed and self.phase=='ENTRY' and self.native_authorizations==1,
                'ORIGINAL_NATIVE_AUTHORITY_CONSUMED_ONCE_NOT_CAUGHT_FAILURE')
            self._checked('ENTRY');self.phase='RETURNED_NOT_ACCEPTED'
            return result
        except BaseException as error:self.fail(error);raise
    def evidence(self):
        self.owner_check()
        return dict(phase=self.phase,entry_invocations=self.invocations,external_authority_calls=self.external_calls,
            intent_write_attempts=self.intent_attempts,intent_pin=None if self.claim_pin is None else dict(self.claim_pin),
            original_native_authorization_calls=self.native_authorizations,complete_entry_calls=self.entry_calls,
            failed=self.failed,error_type=self.error_type,error_code=self.error_code,
            claim_not_Native_byte_credit_or_external_authority=True,automatic_retry_permitted=False,
            original_Frame_commit_or_product_result_created_by_coordinator=False,
            product_acceptance_qualified=False,accepted_count_delta=0,GO_written_by_coordinator=False)


def driver_type(base,once,*,authorize=None):
    """A fresh explicit dependency never enables an older default instance."""
    require((authorize is None or callable(authorize)) and type(once) is Once and once.external is authorize,
        'DEFAULT_CONSTRUCTION_HAS_NO_EXTERNAL_APPROVAL')
    class Driver(base):
        def __init__(self):super().__init__();self.output=OUTPUT;self.once_declared=False
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control);before=control.admit
            def declared(*args,**kwargs):
                require(not self.once_declared,'ONE_EXPLICIT_ONCE_DECLARATION')
                value=before(*args,**kwargs);self.once_declared=True
                require(len(value.control_names)==72 and not {SELF,TEST}&set(value.control_names),
                    'EXACT74_NAMED_ONCE_INPUTS_NOT_OBSERVED_SCOPE_UNION')
                from types import SimpleNamespace as NS
                return NS(**{**vars(value),'control_names':value.control_names+(SELF,TEST)})
            control.admit=declared
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            value=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            actual=data.planned.batch.parent_connection.parent.run_owned
            require(type(actual) is FunctionType,'ORIGINAL_INSTALLED_PARENT_EXECUTE')
            cells=dict(zip(actual.__code__.co_freevars,(cell.cell_contents for cell in actual.__closure__ or ())))
            dependency=cells.get('authorize')
            proof=once.evidence();original=self.parent_handoff.evidence()
            require(self.once_declared and self.construct_only and self.native is None
                and getattr(dependency,'__self__',None) is once
                and getattr(dependency,'__func__',None) is Once.authorize_native
                and original['authorization_dependency_present'] is True
                and original['execution_attempts']==original['component_connections']==0
                and proof['phase']=='NEW' and proof['entry_invocations']==proof['intent_write_attempts']==0
                and proof['original_native_authorization_calls']==proof['complete_entry_calls']==0,
                'SAME_REAL_PARENT_BOUND_TO_UNUSED_ONCE_GATE_NOT_APPROVED')
            reader=a.AcceptanceReader(root,q.checkpoint)
            for name in (SELF,TEST):a.exact(reader.pin(name),dict(data.planned.current[name]),'CURRENT_ONCE_CONNECTION_SOURCE')
            reader.finish();reader.checkpoint()
            require(reader.final_fresh_hashes==len(reader.snapshots)==2,'TWO_ONCE_SOURCE_INPUTS_FRESH_AND_CLOSING_ONCE')
            require(not(root/CLAIM).exists() and not(root/RUNTIME).exists(),'NO_REAL_INTENT_OR_NATIVE011_FROM_CONSTRUCTION')
            return dict(value,state='PASS_PRODUCT_ONCE_ENTRY_CONSTRUCTION_NO_AUTHORITY_NOT_EXECUTION',
                product_once_entry=dict(coordinator=proof,original_parent_authority_dependency_connected=True,
                    external_execution_authority_supplied=authorize is not None,original_complete_entry_lifecycle_connected=False,
                    connection_fresh_inputs=2,connection_final_fresh_hashes=2,
                    connection_source_pins=list(reader.snapshots.values()),original_closed_reader_reused_or_reset=False,
                    Native_or_product_or_GO_or_intent_executed=False,accepted_count_delta=0,GO_authorized=False))
    return Driver


def direct(root,pin):
    path=root/pin['path']
    for member in (path,*path.parents):
        require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP_SOURCE')
        if member==root:break
    with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
    require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'EXACT_BOOTSTRAP_SOURCE')
    return raw


def construct_entry(*,outer=None,output=OUTPUT,checkpoint_route=None,authorize=None):
    from types import SimpleNamespace as NS
    require(outer is None or callable(outer),'EXPLICIT_OUTER_LIFECYCLE_CONSTRUCTION')
    require(authorize is None or callable(authorize),'EXPLICIT_OPTIONAL_AUTHORITY_DEPENDENCY_NOT_FLAG')
    require(checkpoint_route is None or callable(checkpoint_route) and outer is not None,
        'EXPLICIT_COORDINATOR_ROUTE_REQUIRES_OUTER_LIFECYCLE')
    require(type(output) is str and re.fullmatch(
        r'implementation/p09/evidence/p09-361-native011-[A-Za-z0-9-]{1,120}\.v1\.json',output)
        and (outer is not None or output==OUTPUT),'BOUNDED_CONSTRUCTION_OUTPUT_NOT_RUNTIME')
    root=Path(__file__).resolve().parents[2]
    require(not(root/CLAIM).exists() and not(root/RUNTIME).exists() and not(root/output).exists(),
        'EXCLUSIVE_CONSTRUCTION_BEFORE_REAL_INTENT_OR_NATIVE')
    box=[]
    def checkpoint():
        require(len(box)==1,'SAME_ORIGINAL_STAGE_CONTROLLER')
        if checkpoint_route is None:return box[0].check()
        return checkpoint_route(box[0],once)
    once=Once(checkpoint,authorize=authorize)
    env=dict(__name__='p09_product_once_bootstrap',__file__=LOADER['path'])
    exec(compile(direct(root,LOADER),LOADER['path'],'exec'),env)
    libs,_=NS(**env).load(root,[AUTHORITY],{});authority=libs.native011_product_authority_connection
    def wrap(base):
        selected=driver_type(base,once,authorize=authorize)
        class Bound(selected):
            def __init__(self):
                super().__init__();require(not box,'ONE_ORIGINAL_STAGE_CONTROLLER');box.append(self)
        revised=Bound if outer is None else outer(Bound,once)
        require(type(revised) is type and issubclass(revised,Bound),'OUTER_LIFECYCLE_RETAINS_ORIGINAL_ONCE_DRIVER')
        return revised
    return authority.construct(authorize=once.authorize_native,output=output,wrap=wrap)


def main():
    require(not sys.argv[1:],'CONSTRUCTION_ONLY_NO_GO_OR_NATIVE_ARGUMENTS');sys.dont_write_bytecode=True
    return construct_entry()


if __name__=='__main__':raise SystemExit(main())
