"""P202: fresh source-reference audit; never authorizes a reduced runtime scope.

evidence/archive 폴더만 보고 실행 입력을 제외하지 않는다. Rust의 직접 경로와
파일명 참조는 보수적으로 보호하며, 참조가 없다는 사실을 미사용 증명으로 삼지 않는다.
실제 worker의 직접 입력도 보존한다. 동적 fixture 의존성은 별도 확인 대상이다.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch

import joined_runtime_resume_progress as previous

c=previous.c;b=previous.b;r=previous.r;v=previous.v
SELF='tools/p09/audit_runtime_input_roles.py'
TEST='tools/p09/tests/test_runtime_input_roles.py'
PREFIXES=('implementation/p09/evidence/','implementation/p09/source-archive/')


def require(ok,code):c.require(ok,'P202_'+code)


def classify(expected,exe,sources,worker_inputs):
    require(v.pins(list(expected.values()))==expected and expected.get(exe['path'])==exe,'EXACT_MANIFEST_PINS')
    require(isinstance(sources,dict) and bool(sources) and set(sources)<=set(expected)
        and all(isinstance(text,str) for text in sources.values()),'BOUND_SOURCE_TEXT')
    require(isinstance(worker_inputs,set) and bool(worker_inputs) and worker_inputs<=set(expected),'WORKER_INPUT_SCOPE')
    candidates={n for n in expected if n.startswith(PREFIXES)}
    references={n:[] for n in candidates}
    for source,text in sources.items():
        for name in candidates:
            # 파일명만 있는 동적 경로도 놓치지 않도록 과잉 보호한다. 미사용 판정은 하지 않는다.
            if name in text or c.Path(name).name in text:
                references[name].append(source)
    roles=[]
    for name,pin in expected.items():
        if name==exe['path']:role='CURRENT_EXECUTABLE_REQUIRED'
        elif name.endswith('.exe'):role='HISTORICAL_EXECUTABLE_WHOLE_RECONCILIATION_REQUIRED'
        elif name in worker_inputs:role='DIRECT_WORKER_INPUT_REQUIRED'
        elif name in candidates and references[name]:role='RUST_REFERENCED_EVIDENCE_RETAINED'
        elif name in candidates:role='HISTORICAL_CANDIDATE_USAGE_UNPROVEN_RETAINED'
        else:role='ORIGINAL_NON_EXECUTABLE_INPUT_RETAINED'
        roles.append(dict(pin=pin,role=role,referencing_Rust_sources=references.get(name,[])))
    counts={};sizes={}
    for row in roles:
        role=row['role'];counts[role]=counts.get(role,0)+1;sizes[role]=sizes.get(role,0)+row['pin']['bytes']
    require(sum(counts.values())==len(expected) and sum(sizes.values())==sum(p['bytes'] for p in expected.values()),
        'COMPLETE_UNCHANGED_MANIFEST')
    return dict(manifest_roles=roles,role_counts=counts,role_bytes=sizes,
        scanned_source_count=len(sources),original_manifest_pin_count=len(expected),
        original_manifest_bytes=sum(p['bytes'] for p in expected.values()),
        safe_runtime_exclusions=[],runtime_input_exclusions_authorized=False,
        reduced_scope_runtime_qualified=False,dynamic_fixture_dependency_closure_complete=False,
        lack_of_literal_reference_used_as_nonusage_proof=False,
        whole_historical_reconciliation_required=True,product_complete=False,P09_gate='OPEN')


def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_runtime_input_roles')
    with patch('subprocess.Popen',side_effect=AssertionError('P202_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P202_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P202_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==12 and not checked.skipped,'CONTRACT12')
    return 12


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=b.s.scoped_path(f'implementation/p09/evidence/runtime-r07/p09-202-input-role-audit-run{args.run:02}.v1.json',fresh=True)
    context=r.observation.Context();owner=r.observation.Resources(context);q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**r.flags(),
        foreign_PID_query_executed=False,EXE_bytes_rehashed=False,runtime_scope_changed=False)
    try:
        owner.admit();q=r.Reader(owner,context);q.pin(SELF);q.pin(TEST)
        out['input_role_contract_tests_passed']=contracts()
        expected,names,exe=b.baseline(q)
        rust=sorted(n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml')))
        require(len(rust)==785,'ALL_COMPILED_RUST_INPUTS785')
        # 고정된 소스 입력만 fresh 읽는다. 큰 과거 JSON/EXE 반복 읽기로 돌아가지 않는다.
        sources={}
        for name in rust:
            require(q.pin(name)==expected[name],'FRESH_FROZEN_RUST_SOURCE')
            sources[name]=q.text(name)
        # worker() が直接読む compiled inventory は必ず候補から保護する。
        roles=classify(expected,exe,sources,{b.run.PARENT['path']})
        del sources
        q.finish();out.update(state='PASS_SOURCE_REFERENCE_AUDIT_NOT_REDUCED_RUNTIME_OR_GATE',
            binding=v.identity(names,expected,exe),input_roles=roles,
            all785_source_text_fresh_read_and_final_hash_confirmed=True,
            original_manifest_not_rewritten=True,static_reference_audit_not_complete_call_graph=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=r.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','input_role_contract_tests_passed','error_code','resource_stop_reason')}),flush=True)
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
