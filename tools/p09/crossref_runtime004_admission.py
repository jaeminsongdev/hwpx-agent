"""004-only admission of the qualified two-image Python host, never Native permission.

The immutable host qualification is held once by the enclosing entry reader.
Case boundaries read only current execution images/profile sources; they do not
walk the historic receipt chain or turn a saved host result into a session pass.
"""
import named_style_verification_runtime as r
import crossref_python_current555 as profile

QUALIFICATION='implementation/p09/evidence/p09-361-current-python-runtime558.v1.json'
QUALIFICATION_SHA='9267de5e6b11a105cba545268aa15310b7c5fdc26f2cce8a5af53161802da903'
QUALIFICATION_STATE='PASS_CURRENT_PYTHON_TWO_SIGNED_IMAGES_KERNEL_PREASSIGNED_SELFCHECK_AND004_READY_DENIAL_NOT_NATIVE_OR_GATE'
PROFILE_PIN=dict(path='tools/p09/crossref_python_current555.py',bytes=2536,sha256='17f91e89b21e54687401c7e692c163ae8eea9932433a6703db1e1c99f5490685')

def require(ok,code):
    if not ok:raise ValueError('XREF_RUNTIME004_'+code)

def require_qualification(reader):
    # Called exactly once at bundle entry; reader.finish() rehashes it at exit.
    value=r.compact.unpack(reader.json(QUALIFICATION))
    require(reader.snapshots[QUALIFICATION]['sha256']==QUALIFICATION_SHA,'EXACT_QUALIFICATION_RECEIPT')
    require(value['state']==QUALIFICATION_STATE and value['cleanup']is True
        and type(value['fresh_inputs'])is int and value['fresh_inputs']==value['final_fresh_hashes']==260
        and value['runtime_disk_image_final_fresh_hashes']==2 and value['same_live_kernel_before_after']is True
        and value['native_constructor_trap_calls']==0 and value['actual_Hancom_ROT_COM_or_native_started']is False
        and value['fixed_eight_executed']is False and value['native_startup_qualified']is False
        and value['public_entry_profile_applied']is False,'CLOSED_HOST_ONLY_QUALIFICATION')
    require(value['qualified_runtime_profile']==PROFILE_PIN and reader.pin(PROFILE_PIN['path'])==PROFILE_PIN,'SAME_QUALIFIED_PROFILE_SOURCE')
    pins=value['runtime_current_image_pins']
    require(type(pins)is list and len(pins)==2,'EXACT_QUALIFIED_IMAGE_COUNT')
    observed=profile.validate({pin['path']:pin for pin in pins},value['loaded_image_observation'])
    require(observed==value['current_runtime'],'QUALIFIED_IMAGE_PROFILE')
    step,=value['steps']
    require(step['cleanup']is True and step['exit_code']==2 and step['requests']==1 and step['io_threads_joined']is True
        and step['handler_summary']['ready_denied_before_case_io']is True
        and step['owned_job']['owned_tree_empty']is True and step['owned_job']['forced_termination_invoked']is False,
        'CLOSED_READY_DENIAL_NOT_NATIVE_SESSION')
    return dict(qualification=QUALIFICATION,sha256=QUALIFICATION_SHA,profile=profile.PROFILE,
        qualification_checked_at_bundle_boundary=True,native_session_or_execution_authorized=False)

def verify_current_reader(reader):
    # The enclosing boundary freshly pins AND finally rereads both disk images.
    pins={name:reader.pin(name)for name in profile.specifications()}
    return profile.validate(pins,profile.observe_loaded_images())
