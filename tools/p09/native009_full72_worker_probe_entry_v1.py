"""Diagnostic-only real full72 worker; every Popen is denied before OS create.

Not a Native dispatcher or a product permission. Old diagnostic library pins
are reused as metadata, not its69 result. No default helper is hidden/removed.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

SELF='tools/p09/native009_full72_worker_probe_entry_v1.py'
OLD_ENTRY=dict(path='tools/p09/native009_worker_probe_entry_v1.py',bytes=7325,
    sha256='8777d1df6b3e4d5baefb181907e3a7ea676d3f71114193324a83feaf29ea1db6')
TRANSPORT=dict(path='tools/p09/native009_full72_transport_v1.py',bytes=15741,
    sha256='441a0c98198d0442552004d918d4f6516e1c67e38a9de3585cd8e5a84612080e')
PREFIX='implementation/p09/evidence/p09-361-case165-'
HINT=dict(path=PREFIX+'successor-worker-bootstrap009.v3.json',bytes=11606,
    sha256='c09c3d7ad4129fc83b1181de4a595e12e8cd93108a3a4af24b12336806712c5c')
WIRE=dict(path=PREFIX+'successor-worker-capsule009.compact.v3.json',bytes=10295,
    sha256='e75ab40944945f0a7ae995041dbc6c9a56dae405066156869e2b8910d4e49556')
STEP=dict(path=PREFIX+'step-config001.v1.json',bytes=685,
    sha256='2b549a20ad4f46b7d146b935b0ff103e92db0411ad195f6038457e994b973e7c')


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_FULL72_PROBE_ENTRY_'+label)


def main():
    args=sys.argv[1:]
    require(len(args)==4 and args[::2]==['--ready-handle','--task'] and args[3]=='case165-current-r009-tests','EXACT_DIAGNOSTIC_TASK9')
    require(re.fullmatch('[1-9][0-9]{0,19}',args[1]) is not None and int(args[1])<2**64,'EXACT_INHERITED_EVENT')
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/p09'))
    import conservative_maintenance as c
    c.Windows()
    import subprocess,copy
    original_copy=copy.deepcopy;observed=dict(expected=None,command_verified=None,other_JSON_opens=0,
        unexpected_project_metadata=[],outside_or_unclassified_JSON_opens=0,current_step_metadata_reads=0)
    allowed_json={str(root/pin['path']).replace('\\','/') for pin in (HINT,WIRE,STEP)}
    def audit(event,values):
        if event=='subprocess.Popen':
            expected=observed['expected'];actual=values[1]
            observed['command_verified']=expected is not None and actual in (expected,subprocess.list2cmdline(expected))
            raise ValueError('DIAG_SUBPROCESS_DENIED' if observed['command_verified'] else 'DIAG_UNEXPECTED_COMMAND_DENIED')
        if event=='open' and values and isinstance(values[0],str) and values[0].lower().endswith('.json'):
            if values[0].replace('\\','/')==str(root/STEP['path']).replace('\\','/'):observed['current_step_metadata_reads']+=1
            if values[0].replace('\\','/') not in allowed_json:
                observed['other_JSON_opens']+=1
                path=Path(values[0]).absolute()
                relative=path.relative_to(root).as_posix() if path.is_relative_to(root) else ''
                if re.fullmatch(r'implementation/p09/evidence/[A-Za-z0-9_.-]{1,160}\.json',relative):
                    if relative not in observed['unexpected_project_metadata'] and len(observed['unexpected_project_metadata'])<4:
                        observed['unexpected_project_metadata'].append(relative)
                else:observed['outside_or_unclassified_JSON_opens']+=1
    # Installed before all graph, private helper or original worker setup.
    sys.addaudithook(audit)
    import flat_current_queue_envelope_runtime_v25 as envelope
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_product_window_runtime_v18 as original_window
    old,_=envelope.namespace_bundle.load(root,[OLD_ENTRY],{})
    modules,_=envelope.namespace_bundle.load(root,old.native009_worker_probe_entry_v1.PINS+[TRANSPORT],{})
    modules.prepared_run_closure_v1.configure_host_policy(c)
    protocol=modules.worker_readiness_v1
    loader,_=modules.ast_copy_namespace_connection_v1.connect(envelope.namespace_bundle,modules.ast_clone_namespace_v1)
    def read(pin):
        path=root/pin['path']
        for ancestor in (path.parent,*path.parent.parents):
            require(ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction(),'DIRECT_METADATA_ANCESTORS')
            if ancestor==root:break
        require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_METADATA_FILE')
        with path.open('rb') as stream:raw=stream.read(16385)
        require(len(raw)==pin['bytes']<=16384 and hashlib.sha256(raw).hexdigest()==pin['sha256'],'EXACT_BOUNDED_METADATA')
        return raw
    hint=json.loads(read(HINT));wire=read(WIRE);read(STEP)
    observed['expected']=[str(root/scope.EXE_PIN['path']),hint['step']['case'],'--exact','--test-threads=1','--format=pretty','--color=never']
    api=modules.native009_full72_transport_v1.connect(root,loader,scope,bytes_policy,modules.receipt_xz_envelope_v1,
        modules.bounded_successor_capsule_wire_v2,lambda:None,a.exact)
    graph,_=api.reconstruct(hint,wire,lambda:None)
    linked=api.build(root,loader,api,graph,original_window,modules.post_product_recovery_connection_v1,
        modules.post_product_recovery_window_v1,lambda:None)
    event=protocol.WindowsEvent(int(args[1]));stdin=sys.stdin
    try:
        sys.stdin=protocol.ReadyReader(stdin,event)
        try:linked.execute('case165-current-r009-tests')
        except ValueError as error:
            require(error.args in (('WORKER_NOT_AUTHORIZED',),('DIAG_SUBPROCESS_DENIED',)),'EXACT_ORIGINAL_WORKER_STOP')
            read(STEP)
            require(observed['current_step_metadata_reads']==3,'ONE_ORIGINAL_STEP_READ_PLUS_TWO_FRESH_PIN_CHECKS')
            if observed['other_JSON_opens'] or copy.deepcopy is not original_copy:
                print(json.dumps(dict(terminal='DIAG_BOOTSTRAP_IO_FAILURE',other_JSON_opens=observed['other_JSON_opens'],
                    default_copy_unchanged=copy.deepcopy is original_copy,
                    unexpected_project_metadata=observed['unexpected_project_metadata'],
                    outside_or_unclassified_JSON_opens=observed['outside_or_unclassified_JSON_opens'])),file=sys.stderr)
                return 1
            require(observed['other_JSON_opens']==0 and copy.deepcopy is original_copy,'NO_OTHER_JSON_IO_OR_COPY_MUTATION')
            private=('native009_worker_probe_entry_v1','native009_full72_transport_v1','native007_failure_binding_v1',
                'legacy_validation_binding_v1','worker_readiness_v1','ast_clone_namespace_v1','ast_copy_namespace_connection_v1',
                'native009_worker_transport_v1','native009_engine_connection_v1','receipt_xz_envelope_v1',
                'bounded_successor_capsule_wire_v2','post_product_recovery_window_v1','post_product_recovery_connection_v1')
            require(not any(name in sys.modules for name in private),'SOURCE_PINNED_PRIVATE_HELPERS_NOT_DEFAULT_IMPORTED')
            helpers={Path(filename).absolute() for module in tuple(sys.modules.values()) if (filename:=getattr(module,'__file__',None))
                and Path(filename).absolute().is_relative_to(root/'tools/p09')}
            print(json.dumps(dict(terminal=error.args[0],task=graph.worker.TASK,descriptor_count=len(graph.binding.descriptors()),
                actual_worker_attempts=linked.state.attempts,actual_worker_calls=linked.state.calls,
                original_worker_code=Path(linked.original_worker.__code__.co_filename).name,raw_policy_restored=linked.policy.restored,
                product_command_verified=observed['command_verified'],historical_runtime_reads=0,other_JSON_opens=0,
                current_step_pin_checked_before_after=True,current_step_metadata_reads=observed['current_step_metadata_reads'],
                private_helpers_not_default_imported=True,child_default_project_helper_count=len(helpers),actual_product_created=False)),file=sys.stderr)
            return 1
    finally:sys.stdin=stdin;event.close()
    raise ValueError('NATIVE009_FULL72_PROBE_UNEXPECTED_NORMAL_RETURN')


if __name__=='__main__':raise SystemExit(main())
