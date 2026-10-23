"""380: fresh native prerequisites only; no Hwp/COM/child launch, no rerun of240's modeled contracts."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_startup_prerequisites as observed
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-current-crossref-prerequisites380.v1.json';DRIVER='tools/p09/inspect_current_crossref_prerequisites.py'
BASE='implementation/p09/evidence/p09-361-crossref-startup-prerequisites240.v1.json'
CURRENT='implementation/p09/evidence/p09-361-personal-info-detection-product-sync379.v1.json'
NATIVE={'tools/p09/crossref_startup_prerequisites.py','tools/p09/crossref_native_startup.py','tools/p09/crossref_native_host_limits.py',
    'tools/p09/crossref_owned_host_process.py','tools/p09/crossref_preassigned_readonly.py','tools/p09/crossref_native_host_channel.py',
    'implementation/p09/tools/inspect-crossref-runtime-connection.ps1','implementation/p09/tools/crossref-fixed-batch.ps1',
    'implementation/p09/tools/crossref-native-case-ports.ps1','implementation/p09/tools/sdk-baseline-owned-session.ps1'}

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CURRENT_XREF_PREREQUISITES_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_CURRENT_XREF_PREREQUISITES',own_cpu_selection=selection,
        actual_Cargo_Hangul_COM_or_child_process=False,fixed_eight_executed=False,native_startup_qualified=False,permission_dialog_requested=False,
        OS_settings_changed=False,prior_native_or_modeled_contracts_replayed=False,Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);prior=q.json(BASE);current=q.json(CURRENT)
        c.require(prior['cleanup']and prior['modeled_contracts_passed']==8 and not prior['native_startup_qualified'],'ORIGINAL240_CLOSED_READONLY_PREREQUISITES_NOT_NATIVE_QUALIFICATION')
        c.require(q.snapshots[CURRENT]['sha256']=='2ddadac05cde72decbe2845cc1e984061b4820f170c93e857e3e672d43598047'and current['cleanup'],'EXACT379_LATEST_CURRENT_DOC_FRONTIER')
        pins={p['path']:p for p in prior['source_pins']}
        for path in sorted(NATIVE):q.pin(path);c.require(q.snapshots[path]==pins[path],'ALL_ORIGINAL_NATIVE_PARENT_GUARDS_AND_CLOSED_FIXED_EIGHT_ENTRY_UNCHANGED')
        q.pin(DRIVER);q.pin('tools/p09/named_style_verification_runtime.py')
        executable=observed.startup.Path(observed.startup.limits.EXECUTABLE);image=a.AcceptanceReader(executable.parent,guard.check)
        row['actual_observation']=observed.inspect(guard.windows,guard.check,lambda:image.pin(executable.name))
        parent=observed.startup.host.read_parent_cpu(guard.windows)
        row['immediate_parent_job_observation']=parent
        row['OS_permitted_external_breakaway_eligibility_only']=parent['job_present']is False or(parent['query_succeeded']is True and parent['flags']&0x800!=0)
        c.require(not row['actual_observation']['process_created']and not row['actual_observation']['COM_activated']and not row['actual_observation']['permission_dialog_requested'],
            'NO_NATIVE_PROCESS_SLOT_COM_DOCUMENT_OR_PERMISSION_WINDOW_CREATED')
        image.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_XREF_READONLY_PREREQUISITES_OBSERVED_NOT_NATIVE_SESSION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            external_executable_pins=list(image.snapshots.values()),external_final_fresh_hashes=image.final_fresh_hashes,
            next_work='qualified_native_safe_controller_provenance_no_parent_policy_relaxation_or_closed_entry_bypass')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'CURRENT_XREF_READONLY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','actual_observation','immediate_parent_job_observation','OS_permitted_external_breakaway_eligibility_only',
            'fresh_inputs','final_fresh_hashes','external_final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
