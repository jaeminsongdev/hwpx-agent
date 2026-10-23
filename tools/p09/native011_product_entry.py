"""Explicit one-shot entry and terminal publication; CLI is connection-only.

Product execution needs a separately supplied human-authorized callback. A
construction result, CLI flag, or publication receipt is never that authority.
Original lifecycle, resource checks, cleanup, checker and queue state stay.
"""
import base64
import hashlib
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace as NS

SELF='tools/p09/native011_product_entry.py'
TEST='tools/p09/tests/test_native011_product_entry.py'
LIFECYCLE='tools/p09/native011_product_lifecycle.py'
CONSTRUCTION='implementation/p09/evidence/p09-361-native011-current805-product-entry-connect002.v1.json'
RESULT='implementation/p09/evidence/p09-361-native011-case165-product-entry001.v1.json'
CANONICAL='implementation/p09/evidence/p09-361-case165-current-runtime-run011.v1.json'
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
PART_BYTES=180000
MAX_BYTES=16*1048576


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_PRODUCT_ENTRY_'+code)


def failure(error):
    value=error.args[0] if error.args else None
    return dict(error_type=type(error).__name__,error_code=value if type(value) is str
        and re.fullmatch('[A-Z0-9_]{1,160}',value) else 'ORIGINAL_ENTRY_ERROR')


def publish_result(value,root,publisher,a,factory,journal):
    """Original lossless codec and exclusive publisher under a new post-owner.

    No closed guard is reused. Partial exclusive outputs remain on any error;
    every attempted path is journaled and this function never retries.
    """
    guard=factory('whole_metadata_preflight')
    journal.update(attempted=True,parts=[],attempted_paths=[],cleanup=False)
    try:
        guard.acquire()
        packed=a.packed.pack(value,guard.check)
        guard.check(force=True)
        raw=(json.dumps(packed,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')
        require(0<len(raw)<=MAX_BYTES,'BOUNDED_LOSSLESS_TERMINAL_CARRIER')
        guard.check(force=True)
        journal.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
            original_packed_codec=True,original_result_not_summarized_or_rewritten=True)
        for offset in range(0,len(raw),PART_BYTES):
            guard.check()
            chunk=raw[offset:offset+PART_BYTES];index=offset//PART_BYTES
            name=RESULT.replace('.v1.json',f'.result-part{index:03}.v1.json')
            journal['attempted_paths'].append(name)
            pin=publisher.publish(root,name,dict(schema_version='hwpx-agent.p09-product-entry-result-part/v1',
                index=index,bytes=len(chunk),sha256=hashlib.sha256(chunk).hexdigest(),
                base64=base64.b64encode(chunk).decode('ascii'),
                original_Native_finished=True,queue_acceptance_authorized=False),a)
            require(type(pin) is dict and set(pin)=={'path','bytes','sha256'} and pin['path']==name
                and type(pin['bytes']) is int and 0<pin['bytes']<=262144
                and type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}',pin['sha256']),
                'EXACT_ORIGINAL_TERMINAL_PART_PIN')
            journal['parts'].append(pin)
        guard.check(force=True)
    finally:
        guard.close();journal['cleanup']=guard.cleanup
    require(journal['cleanup'] is True,'TERMINAL_PUBLICATION_OWNER_CLEANUP')


def terminal(driver,once):
    """Original pure terminal inspections, never closed-guard IO or new credit."""
    pipeline=driver.lifecycle_controllers;route=pipeline.route;procedure=driver.lifecycle_procedure
    once.owner_check();driver.coordinator_boundary.seal()
    require(driver.closed and driver.cleanup and pipeline.state.closed and pipeline.cleanup()
        and once.phase=='RETURNED_NOT_ACCEPTED' and not once.failed
        and once.invocations==once.external_calls==once.intent_attempts==once.native_authorizations==once.entry_calls==1,
        'CLOSED_ORIGINAL_OWNER_AND_ONE_COMPLETE_ENTRY')
    require(procedure.state.invocations==procedure.state.entry_calls==procedure.state.finish_calls==1
        and procedure.state.original_procedure_returned is True and procedure.state.finish_failed is False
        and procedure.state.active_entry is None and procedure.state.returned_result is None
        and route.phase=='CHECKED_NOT_ACCEPTED' and route.guard is None and route.cleanup is True
        and route.oracle_attempts==route.guard_creations==1,'ORIGINAL_CLOSING_AND_ORACLE_FINISHED_NOT_CONSTRUCTION')
    batch,frame=route._terminal();route._checker()
    require(batch is driver.lifecycle_context.result.assembled.batch and frame.state=='COMMITTED'
        and frame.held.closed and frame.owned_cleanup_seen is True and not frame.registered
        and driver.parent_handoff.state.cleanup_confirmed is True,'ACTUAL_COMMITTED_FRAME_AND_RELEASED_SOURCE_HANDLES')
    audit=driver.product_audit.evidence()
    require(audit['original_deny_registrations']==audit['component_connections']==audit['factory_attempts']
        ==audit['allowed_Popen_events']==audit['original_process_policy_arm_attempts']==audit['original_policy_Popen_attempts']==1
        and audit['denied_Popen_events']==audit['original_denied_events']==0 and not audit['scope_active']
        and not audit['failed'] and audit['original_private_dependency_restored'] is True
        and audit['restore_error_types']==[],'ONE_ORIGINAL_PRODUCT_PROCESS_AND_RESTORED_PRIVATE_AUDIT')
    return frame


def driver_type(base,once,*,authorize=None,execute=False):
    require(type(execute) is bool and (authorize is None or callable(authorize))
        and once.external is authorize and (not execute or authorize is not None),
        'EXPLICIT_NEW_AUTHORITY_REQUIRED_FOR_EXECUTION_NOT_FLAGS')
    class Driver(base):
        def __init__(self):
            super().__init__();self.output=RESULT if execute else CONSTRUCTION
            self.entry_calls=0;self.entry_call_attempts=0;self.entry_finish_calls=0;self.entry_constructed=False
            self.entry_value=None;self.entry_error=None;self.entry_publication={};self.entry_verified=False;self.entry_original_verified=False
        def run(self,*args,**kwargs):
            self.entry_call_attempts+=1
            try:
                require(self.entry_calls==0,'ONE_ENTRY_NO_RETRY');self.entry_calls=1
                value=super().run(*args,**kwargs);self.entry_constructed=True
                require(self.entry_error is None,'NO_CAUGHT_ENTRY_FAILURE')
                require(once.external is authorize and once.phase=='NEW' and once.invocations==0,
                    'SAME_FRESH_INSTANCE_AFTER_ORIGINAL_CONSTRUCTION')
                if not execute:return dict(value,state='PASS_NATIVE011_ENTRY_CONNECTION_NOT_EXECUTION')
                self.entry_value=self.product_dispatch.run()
                require(self.entry_error is None,'NO_CAUGHT_ENTRY_FAILURE')
                return dict(value,state='RETURNED_NATIVE011_LIFECYCLE_PENDING_TERMINAL_PUBLICATION')
            except BaseException as error:
                if self.entry_error is None:self.entry_error=failure(error)
                raise
        def finish(self,root,row,publisher,a):
            require(self.entry_finish_calls==0,'ONE_TERMINAL_PUBLICATION_NO_RETRY');self.entry_finish_calls=1
            try:
                super().finish(root,row,publisher,a)
                require(self.closed and self.cleanup,'ORIGINAL_DRIVER_CLEANUP_BEFORE_PUBLICATION')
                if not execute:
                    require(self.entry_constructed and self.entry_error is None and once.invocations==0
                        and once.external_calls==once.intent_attempts==once.native_authorizations==0,
                        'CONNECTION_ONLY_NOT_PARTIAL_OR_FAILED_PRODUCT')
                    require(not row.get('terminal_evidence_publication_error')
                        and not row.get('state','').startswith(('FAILED_','CLEANUP_FAILED_')),
                        'NO_BASE_TERMINAL_FAILURE_PROMOTED_TO_CONNECTION_PASS')
                    row['state']='PASS_NATIVE011_ENTRY_CONNECTION_NOT_EXECUTION'
                else:
                    require(self.entry_error is None and type(self.entry_value) is dict,
                        'ORIGINAL_ENTRY_RETURN_REQUIRED_NOT_FAILURE_REPAIR')
                    terminal(self,once)
                    require(not row.get('terminal_evidence_publication_error'), 'NO_BASE_TERMINAL_PUBLICATION_FAILURE')
                    pin=self.entry_value['canonical_receipt_pin']
                    require(type(pin) is dict and set(pin)=={'path','bytes','sha256'} and pin['path']==CANONICAL
                        and type(pin['bytes']) is int and pin['bytes']>0
                        and type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}',pin['sha256']),
                        'ORIGINAL_VERIFIED_CANONICAL_PIN_NOT_DIAGNOSTIC')
                    row['canonical_receipt_pin']=dict(pin)
                    self.entry_original_verified=True
                    publish_result(self.entry_value,root,publisher,a,self.factory,self.entry_publication)
                    self.entry_verified=True
                    row['state']='PASS_NATIVE011_COMPLETE_PRODUCT_AND_ORIGINAL_ORACLE_NOT_QUEUE_OR_GATE'
            except BaseException as error:
                current=failure(error)
                if self.entry_error is None:self.entry_error=current
                row.update(state='FAILED_NATIVE011_PRODUCT_ENTRY_NOT_ACCEPTED',**self.entry_error)
                if current!=self.entry_error:row['entry_terminal_secondary_error']=current
            finally:
                context=self.lifecycle_context
                frames=[] if context is None else context.result.assembled.batch.parent_connection.state.frames
                attempts=0 if context is None else context.result.assembled.batch.parent_connection.state.attempts
                possible_execution=bool(frames) or attempts>0
                row.update(product_entry=dict(execution_requested=execute,entry_calls=self.entry_calls,entry_call_attempts=self.entry_call_attempts,
                    terminal_calls=self.entry_finish_calls,construction_completed=self.entry_constructed,
                    complete_original_lifecycle_and_publication_verified=self.entry_verified,
                    original_lifecycle_and_oracle_verified=self.entry_original_verified,
                    error=self.entry_error,result_reference_released=True,queue_acceptance_authorized=False),
                    product_entry_result_artifact=dict(self.entry_publication),parent_attempts=attempts,
                    Frame_instances=len(frames),actual_Native_Frame_created=bool(frames),
                    actual_product_executed=True if self.entry_original_verified else None if possible_execution else False,
                    actual_whole_corpus_bytes_qualified=self.entry_original_verified,actual_metadata_body_qualified=self.entry_original_verified,
                    actual_Native_or_source_Frame_qualified=self.entry_original_verified,actual_product_GO_received=self.entry_original_verified,
                    worker_attempts=1 if self.entry_original_verified else None if possible_execution else 0,
                    worker_calls=1 if self.entry_original_verified else None if possible_execution else 0,
                    cleanup_confirmed=bool(self.cleanup) and self.entry_publication.get('cleanup') is not False,
                    accepted_count_delta=0,official_accepted_count=158,official_queue_advanced=False,P09_gate='OPEN',P10_started=False)
                self.entry_value=None
    return Driver


def entry(lifecycle,*,authorize=None,execute=False):
    require(type(execute) is bool and (authorize is None or callable(authorize))
        and (not execute or authorize is not None),'EXPLICIT_AUTHORITY_NOT_CLI_OR_CONSTRUCTION_PERMISSION')
    def wrap(base,once):return driver_type(base,once,authorize=authorize,execute=execute)
    return lifecycle.construct(authorize=authorize,wrap=wrap,output=RESULT if execute else CONSTRUCTION)


def main():
    require(sys.argv[1:]==['--connect-only'],'CLI_CONNECTION_ONLY_NO_PRODUCT_GO_OR_RETRY')
    sys.dont_write_bytecode=True;root=Path(__file__).resolve().parents[2]
    def fresh(name,limit):
        path=root/name
        for member in (path,*path.parents):
            require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP_SOURCE')
            if member==root:break
        with path.open('rb') as stream:raw=stream.read(limit+1)
        require(0<len(raw)<=limit,'BOUNDED_PRIVATE_BOOTSTRAP');return raw
    raw=fresh(LOADER['path'],LOADER['bytes'])
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_ORIGINAL_LOADER')
    env=dict(__name__='p09_product_entry_bootstrap',__file__=LOADER['path']);exec(compile(raw,LOADER['path'],'exec'),env)
    raw=fresh(LIFECYCLE,65536);pin=dict(path=LIFECYCLE,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    libraries,_=NS(**env).load(root,[pin],{})
    before=sys.argv;sys.argv=[before[0]]
    try:return entry(libraries.native011_product_lifecycle)
    finally:sys.argv=before


if __name__=='__main__':raise SystemExit(main())
