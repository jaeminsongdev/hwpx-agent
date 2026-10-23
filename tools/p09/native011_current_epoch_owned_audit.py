"""Exact original owned monitor with current805 target/report identity only."""
import ast
import copy
import hashlib
import json
import re
import sys
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_owned_audit.py'
TEST='tools/p09/tests/test_native011_current_epoch_owned_audit.py'
SOURCE=dict(path='tools/p09/native011_owned_metadata_audit.py',bytes=9498,
    sha256='b624bcefafb00c8decdcd9a4bd80b06bb2a63fa3b7d46af4f524a45cc9e5b493')
TARGET='tools/p09/native011_current_epoch_audit.py'
LABELS={
    'implementation/p09/evidence/p09-361-native011-owned-metadata-audit-attempt':
        'implementation/p09/evidence/p09-361-native011-current805-owned-metadata-audit',
    'PASS_NATIVE011_ACTUAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE':
        'PASS_CURRENT805_ACTUAL_METADATA_WHOLE_BOUNDARIES_NOT_NATIVE'}


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_OWNED_AUDIT_'+code)


def preserve_terminal_failure(owned,capture,row,stdout,stderr,monitor):
    require(type(owned.returncode) is int and owned.returncode!=0,'TERMINAL_FAILED_CHILD_ONLY')
    markers,observations=capture.progress();owned.observe()
    summary=json.loads(stdout.splitlines()[-1])
    row['owned'].update(exit_code=owned.returncode,markers=markers,marker_observations=observations,
        child_summary=summary,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
        terminal_failure_no_phase_rotation=True,uncredited_terminal_markers=markers[monitor.seen:])
    require(type(markers) is list and markers==list(monitor.MARKERS[:len(markers)]),
        'EXACT_TERMINAL_PREFIX_WITHOUT_MONITOR_ROTATION_OR_CREDIT')
    code=summary.get('error_code')
    raise ValueError(code if type(code) is str and re.fullmatch('[A-Za-z0-9_]{1,160}',code)
        else 'ACTUAL_READONLY_CHILD_FAILED_NO_RETRY')


def observe_markers(monitor,markers,owned,capture,row,preserve):
    try:return monitor.accept(markers,owned)
    except ValueError as error:
        if (error.args==('NATIVE011_OWNED_METADATA_AUDIT_NO_MONITOR_ROTATION_FROM_TERMINAL_PROCESS',)
            and type(owned.returncode) is int and owned.returncode!=0):
            stdout,stderr=capture.communicate(timeout=.5)
            return preserve(owned,capture,row,stdout,stderr,monitor)
        raise


def project(raw):
    require(type(raw) is bytes and len(raw)==SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest()==SOURCE['sha256'],'EXACT_ENTIRE_ORIGINAL_OWNED_MONITOR_SOURCE')
    tree=ast.parse(raw);original=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
    revised=copy.deepcopy(original);changes=[]
    class Labels(ast.NodeTransformer):
        def visit_Constant(self,node):
            if type(node.value) is str and node.value in LABELS:
                after=ast.copy_location(ast.Constant(LABELS[node.value]),node)
                after._before=copy.deepcopy(node);changes.append(node.value);return after
            return node
    revised=Labels().visit(revised)
    require(sorted(changes)==sorted(LABELS),'EXACT_TWO_REPORT_IDENTITY_LABELS')
    loops=[node for node in ast.walk(revised) if isinstance(node,ast.For) and isinstance(node.iter,ast.Tuple)
        and len(node.iter.elts)>2 and isinstance(node.iter.elts[0],ast.Name) and node.iter.elts[0].id=='SELF'
        and isinstance(node.iter.elts[1],ast.Name) and node.iter.elts[1].id=='TARGET']
    require(len(loops)==1,'ONE_EXPLICIT_ORIGINAL_MONITOR_INPUT_LIST')
    added=ast.Constant(SOURCE['path']);added._added_source=True;loops[0].iter.elts.append(added)
    # A failed child may finish immediately after its next marker. Preserve
    # its terminal error BEFORE the unchanged monitor rejects late rotation.
    # No phase credit, new guard, retry or successful result is granted.
    statements=[node for node in ast.walk(revised) if isinstance(node,ast.While)]
    require(len(statements)==1,'ONE_ORIGINAL_CHILD_OBSERVATION_LOOP')
    loop=statements[0];positions=[i for i,node in enumerate(loop.body) if isinstance(node,ast.Assign)
        and len(node.targets)==1 and isinstance(node.targets[0],ast.Tuple)
        and any(isinstance(part,ast.Name) and part.id=='observations' for part in node.targets[0].elts)
        and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute)
        and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='capture'
        and node.value.func.attr=='progress']
    require(len(positions)==1,'ONE_TERMINAL_CAPTURE_AFTER_COMMUNICATE')
    branch=ast.parse('if owned.returncode != 0: _preserve_terminal_failure(owned,capture,row,stdout,stderr,monitor)').body[0]
    branch._added_source=True;loop.body.insert(positions[0],branch)
    accepted=[]
    class Observe(ast.NodeTransformer):
        def visit_Call(self,node):
            if (isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name)
                and node.func.value.id=='monitor' and node.func.attr=='accept'):
                after=ast.parse('_observe_markers(monitor,markers,owned,capture,row)',mode='eval').body
                after._before=copy.deepcopy(node);accepted.append(1);return after
            return self.generic_visit(node)
    revised=Observe().visit(revised)
    require(len(accepted)==2,'BOTH_ORIGINAL_MONITOR_OBSERVATION_SITES')
    class Undo(ast.NodeTransformer):
        def visit(self,node):
            if hasattr(node,'_before'):return copy.deepcopy(node._before)
            if hasattr(node,'_added_source'):return None
            return super().visit(node)
    require(ast.dump(Undo().visit(copy.deepcopy(revised)),include_attributes=False)
        ==ast.dump(original,include_attributes=False),'ENTIRE_ORIGINAL_MONITOR_MAIN_AST_INVERSE')
    return revised,dict(entire_original_monitor_main_AST_inverse=True,
        exact_report_identity_labels=2,explicit_original_source_role_added=SOURCE['path'],
        four_phase_protocol_and_original_guards_and_Job_and_cleanup_retained=True,
        failed_child_summary_preserved_without_terminal_phase_credit=True,
        original_default_modules_mutated=False,Native_or_product_authorized=False)


def main():
    from pathlib import Path
    require(sys.argv[1:] in (['--attempt','1','--generation','3'],['--attempt','2','--generation','3'],
        ['--attempt','3','--generation','3']),
        'ONLY_CLOSED_CURRENT805_READONLY_AUDITS')
    root=Path(__file__).resolve().parents[2];raw=(root/SOURCE['path']).read_bytes()
    node,proof=project(raw)
    env=dict(__name__='p09_current805_owned_audit_private',__file__=SOURCE['path'])
    exec(compile(raw,SOURCE['path'],'exec'),env)
    # Keep Monitor, failure preservation, resource samples and actual OwnedJob
    # construction/capture/cleanup unchanged. Only named identities differ.
    # The class body itself remains byte-for-byte original. Supply its fixed
    # marker declaration to the separate failure-only observation helper.
    def terminal(owned,capture,row,stdout,stderr,actual):
        proxy=NS(seen=actual.seen,MARKERS=env['MARKERS'])
        return preserve_terminal_failure(owned,capture,row,stdout,stderr,proxy)
    def observing(actual,markers,owned,capture,row):
        return observe_markers(actual,markers,owned,capture,row,terminal)
    env.update(SELF=SELF,TARGET=TARGET,_preserve_terminal_failure=terminal,_observe_markers=observing)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),SOURCE['path'],'exec'),env)
    return env['main']()


if __name__=='__main__':raise SystemExit(main())
