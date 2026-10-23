"""One complete original lifecycle call, not a CLI or execution permission.

Bind to the same open controllers; a default None plan remains denied.
Only a fresh explicit authority can run. The original lifecycle owns IO, Job,
Frame, time limits, teardown and independent verification. This adapter neither
invents a result nor adds queue acceptance. Real integration is a separate gate.
"""
from types import CodeType, FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_product_dispatch.py'
TEST='tools/p09/tests/test_native011_product_dispatch.py'


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_PRODUCT_DISPATCH_'+code)


def bind(driver,once,once_api,write_intent,progress,*,authorize):
    require((authorize is None or callable(authorize)) and type(once) is once_api.Once and once.external is authorize,
        'FRESH_EXPLICIT_AUTHORITY_NOT_DEFAULT_REBIND_OR_FLAG')
    once.owner_check()
    require(callable(progress) and type(write_intent) is FunctionType,
        'EXPLICIT_PROGRESS_AND_ORIGINAL_CLAIM_WRITER')
    writer_codes=[item for item in once_api.claim_writer.__code__.co_consts
        if type(item) is CodeType and item.co_name=='write']
    require(len(writer_codes)==1 and write_intent.__code__==writer_codes[0]
        and write_intent.__globals__ is once_api.Once.execute.__globals__,
        'WHOLE_ORIGINAL_CLAIM_WRITER_NOT_INJECTED_RESULT')
    pipeline=driver.lifecycle_controllers;procedure=driver.lifecycle_procedure
    context=driver.lifecycle_context;inputs=driver.oracle_inputs;audit=driver.product_audit
    binding=procedure.state.input_binding;boundary=driver.coordinator_boundary
    require(binding is not None and binding.context is context and binding.api is inputs.api
        and binding.Reader is inputs.Reader and binding.policy is inputs.policy is audit.policy,
        'SAME_ORIGINAL_CONTEXT_INPUTS_READER_AND_PROCESS_POLICY')
    state=NS(attempts=0,returned=False,failed=False,error_type=None,result_retained=False)
    saved_writer=(write_intent.__code__,write_intent.__globals__,write_intent.__defaults__,write_intent.__closure__)
    saved_invoke=(procedure.invoke,procedure.invoke.__code__)
    def seal():
        require(driver.lifecycle_controllers is pipeline and driver.lifecycle_procedure is procedure
            and driver.lifecycle_context is context and driver.oracle_inputs is inputs
            and driver.product_audit is audit and driver.coordinator_boundary is boundary
            and procedure.state.input_binding is binding and binding.context is context
            and binding.api is inputs.api and binding.Reader is inputs.Reader
            and binding.policy is inputs.policy is audit.policy and once.external is authorize
            and procedure.invoke is saved_invoke[0] and procedure.invoke.__code__ is saved_invoke[1]
            and (write_intent.__code__,write_intent.__globals__,write_intent.__defaults__,write_intent.__closure__)==saved_writer,
            'BOUND_DEPENDENCIES_UNCHANGED')
        require(driver.construct_only is True and driver.native is None and not driver.closed
            and driver.stage=='construction' and not pipeline.state.closed and not audit.failed
            and all(getattr(pipeline.state,name) is True for name in
                ('reader_bound','parent_bound','coordinator_bound','process_audit_bound','oracle_inputs_bound')),
            'SAME_OPEN_ORIGINAL_CONTROLLER_PIPELINE_NOT_CLOSED_CONSTRUCTION')
        once.owner_check();procedure.seal();boundary.seal();inputs.seal()
    seal()
    require(once.phase=='NEW' and not once.failed and once.invocations==once.external_calls==once.intent_attempts
        ==once.native_authorizations==once.entry_calls==0 and procedure.state.invocations==procedure.state.entry_calls==0,
        'ONE_UNUSED_WHOLE_ENTRY_BEFORE_CLAIM_OR_NATIVE')
    def run():
        require(state.attempts==0 and not state.failed,'ONE_COMPLETE_DISPATCH_NO_RETRY')
        state.attempts=1
        try:
            seal()
            require(authorize is not None,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED_BEFORE_ENTRY')
            result=procedure.invoke(once,once_api.Once,write_intent,context,pipeline.route,pipeline.relay,pipeline.epochs,
                inputs.Reader,inputs.policy,inputs.api,progress)
            require(once.phase=='RETURNED_NOT_ACCEPTED' and not once.failed
                and once.invocations==once.external_calls==once.intent_attempts==once.native_authorizations==once.entry_calls==1
                and procedure.state.invocations==procedure.state.entry_calls==procedure.state.finish_calls==1
                and procedure.state.original_procedure_returned is True and procedure.state.finish_failed is False
                and procedure.state.active_entry is None and procedure.state.returned_result is None,
                'ORIGINAL_COMPLETE_LIFECYCLE_RETURN_AND_TEARDOWN_NOT_ADAPTER_SUCCESS')
            state.returned=True
            return result
        except BaseException as error:
            state.failed=True;state.error_type=type(error).__name__;raise
    def evidence():
        return dict(bound=True,dispatch_attempts=state.attempts,original_complete_lifecycle_returned=state.returned,
            external_authority_dependency_supplied=authorize is not None,
            failed=state.failed,error_type=state.error_type,result_retained=state.result_retained,
            default_denied_instance_changed=False,original_whole_entry_callable_connected=True,
            original_resource_or_deadline_or_process_policy_replaced=False,
            adapter_created_GO_or_Frame_commit_or_product_result=False,
            product_or_Native_qualified=False,accepted_count_delta=0,queue_acceptance_authorized=False)
    return NS(run=run,evidence=evidence,state=state)


def connect(driver,once,root,reader,a,current,publisher):
    """Fresh source declarations and the real inactive original writer, no IO claim."""
    for name in (SELF,TEST):a.exact(reader.pin(name),dict(current[name]),'DIRECT_CURRENT_DISPATCH_SOURCE')
    env=type(once).execute.__globals__;api=NS(Once=type(once),claim_writer=env['claim_writer'])
    pin=env['PUBLISHER'];observed,raw=reader._read(pin['path'],parse=True);reader._bind(observed['path'],observed)
    a.exact(observed,pin,'WHOLE_ORIGINAL_DISPATCH_PUBLISHER')
    a.exact(observed,dict(current[pin['path']]),'DIRECT_CURRENT_DISPATCH_PUBLISHER')
    writer=api.claim_writer(bytes(raw),publisher,root,a)
    labels=('RUNNING_FRESH_WHOLE_OPENING','RUNNING_ORIGINAL_NATIVE011_PRODUCT_ONCE',
        'RUNNING_FRESH_WHOLE_CLOSING','RUNNING_ORIGINAL_FULL_ORACLE')
    def progress(label):
        require(type(label) is str and label in labels,'BOUNDED_ORIGINAL_PROGRESS_LABEL')
        print(label,flush=True)
    return bind(driver,once,api,writer,progress,authorize=once.external)
