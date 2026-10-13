"""P170 bounded diagnostic from accepted Cargo records, not a build verdict.

No process query, file polling, raw paths/names/versions or new child/thread.
Every original Cargo record and hash check runs before any observation.
"""
import argparse
import hashlib
import io
import json
import sys
import unittest
from unittest.mock import patch
import build_writer_xml_product as d

SELF='tools/p09/validated_compiler_progress.py'
TEST='tools/p09/tests/test_validated_compiler_progress.py'
MAX_ARTIFACT_EVENTS=20
MAX_FRAME_BYTES=256
PREFIX='P170_VALIDATED_COMPILER:'
GROUPS={'hwpx-package':'hwpx-package','domain-ir':'domain-ir','hwpx-agent-cli':'product-cli',
    'form_stored_provider':'product-libtest'}

def require(ok,code):d.require(ok,'PROGRESS_'+code)

def validate_event(row):
    require(type(row) is dict and set(row)=={'kind','sequence','group','fresh','omitted_artifacts'},'FIELDS')
    require(row['kind'] in ('artifact','closed') and type(row['sequence']) is int
        and 1<=row['sequence']<=MAX_ARTIFACT_EVENTS+1 and row['group'] in (*GROUPS.values(),'dependency',None)
        and (row['fresh'] is None or type(row['fresh']) is bool)
        and type(row['omitted_artifacts']) is int and 0<=row['omitted_artifacts']<=d.b.legacy.stream.MAX_MESSAGES,'TYPES')
    if row['kind']=='closed':require(row['group'] is None and row['fresh'] is None,'CLOSED')
    else:require(row['group'] is not None,'ARTIFACT')
    return row

def encode_event(row):
    validate_event(row);frame=(PREFIX+json.dumps(row,separators=(',',':'))+'\n').encode()
    require(len(frame)<=MAX_FRAME_BYTES,'FRAME_BUDGET');return frame

def emit_event(row):
    frame=encode_event(row);print(frame.decode().rstrip('\n'),file=sys.stderr,flush=True)

class CargoStream(d.b.CargoStream):
    def __init__(self,emit=emit_event):
        super().__init__();self.emit=emit;self.observed_artifacts=0;self.saved=0;self.omitted=0;self.progress_closed=False

    def accept(self,raw):
        super().accept(raw)  # All original whole-record/profile/duplicate/error validation remains first.
        if not raw.strip():return
        row=json.loads(raw.decode('utf-8'),object_pairs_hook=d.b.legacy.stream.unique_object)
        if row.get('reason')=='compiler-artifact':
            self.observed_artifacts+=1
            if self.saved<MAX_ARTIFACT_EVENTS:
                self.saved+=1;fresh=row.get('fresh')
                self.emit(dict(kind='artifact',sequence=self.saved,
                    group=GROUPS.get(row.get('target',{}).get('name'),'dependency'),
                    fresh=fresh if type(fresh) is bool else None,omitted_artifacts=self.omitted))
            else:self.omitted+=1

    def finish(self,stderr_bytes):
        payload=super().finish(stderr_bytes)  # No closing diagnostic before the full original stream accepts.
        require(not self.progress_closed,'DUPLICATE_PROGRESS_CLOSE');self.progress_closed=True
        self.emit(dict(kind='closed',sequence=self.saved+1,group=None,fresh=None,omitted_artifacts=self.omitted))
        return payload

def observe(text):
    require(type(text) is str and len(text.encode())<=32768,'OUTER_STREAM_BUDGET')
    records=[];partial=0
    for line in text.splitlines(keepends=True):
        if not line.startswith(PREFIX):continue
        if not line.endswith('\n'):
            require(len(line.encode())<MAX_FRAME_BYTES,'PARTIAL_FRAME_BUDGET');partial=len(line.encode());continue
        require(len(line.encode())<=MAX_FRAME_BYTES,'FRAME_BUDGET')
        try:row=json.loads(line[len(PREFIX):],object_pairs_hook=d.b.legacy.stream.unique_object)
        except json.JSONDecodeError:raise ValueError('PROGRESS_CLOSED_JSON_REJECTED') from None
        validate_event(row)
        require(len(records)<MAX_ARTIFACT_EVENTS+1 and row['sequence']==len(records)+1,'ORDER_AND_COUNT')
        require(not records or records[-1]['kind']!='closed','AFTER_CLOSE')
        records.append(row)
    closed=bool(records and records[-1]['kind']=='closed')
    require(not closed or not partial,'PARTIAL_AFTER_CLOSE')
    return dict(records=records,closing_observed=closed,partial_marker_bytes=partial,
        native_Process_query_started=False,raw_names_paths_versions_commands_saved=False,
        exact_compiler_or_linker_phase_verified=False,diagnostic_not_build_runtime_or_Gate=True,
        maximum_artifact_events=MAX_ARTIFACT_EVENTS,maximum_frame_bytes=MAX_FRAME_BYTES,
        unobserved_artifacts=None if not closed else records[-1]['omitted_artifacts'])

def contracts():
    sys.path.insert(0,str(d.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_validated_compiler_progress')
    with patch('subprocess.Popen',side_effect=AssertionError('P170_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P170_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P170_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==10 and not result.skipped,'CONTRACT10')
    return dict(contract_tests_run=10,contract_tests_passed=10)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--light',action='store_true',required=True);parser.parse_args()
    require(d.c.Path.cwd().resolve()==d.c.ROOT,'CWD')
    destination=d.s.scoped_path('implementation/p09/evidence/p09-170-validated-compiler-progress.light-run01.v1.json',fresh=True)
    resources=d.s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=d.s.LiveSQLReader(resources)
        for n in (SELF,TEST,d.b.SELF,'tools/p09/signed_durable_build_stream.py'):q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_VALIDATED_COMPILER_PROGRESS_CONTRACTS_ONLY_NOT_ACTUAL_BUILD_OR_GATE',
            actual_child_or_new_thread_started=False,actual_compiler_progress_observed=False,
            original_Cargo_validation_and_raw_SHA_unchanged=True,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.writer.b.prior.d.original.closed_error(e)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
