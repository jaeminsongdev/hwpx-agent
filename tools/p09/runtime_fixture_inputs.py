"""P203: bind known r07 test-module fixture families without product execution.

manifest가 선언한 실제 문서와 고정 캡처를 별도 명시 입력으로 묶는다.
과거 note 실패는 실패로 유지한다. 모든 문서 byte를 fresh 읽고 다시 hash한다.
이 확인은 fixture 입력 자격만 증명하며 runner 범위 축소나 Gate 수용은 아니다.
"""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import joined_runtime_resume_progress as previous

c=previous.c;b=previous.b;r=previous.r;v=previous.v
SELF='tools/p09/runtime_fixture_inputs.py';TEST='tools/p09/tests/test_runtime_fixture_inputs.py'
SCHEMA='hwpx-agent.p09-r07-fixture-input-closure/v1'
PASS='PASS_KNOWN_R07_FIXTURE_INPUTS_FRESH_NOT_RUNTIME_OR_GATE'
MAX_FILE_BYTES=32*1024*1024
P77='implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json'
FORM_ROOT='fixtures/target-build/p09-42-product-form-values-01/output/'
FORM=FORM_ROOT+'fixture-manifest.json'
NOTE_ROOT='fixtures/target-build/p09-24-note-target-20261002-03/output/'
NOTE=NOTE_ROOT+'fixture-manifest.json'
NATIVE='implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json'
HEADER='crates/hwpx-package/src/hancom_2020_minimal_header.xml'
MANIFEST_PINS={
    P77:dict(path=P77,bytes=112797,sha256='36b30c931b760bddedb4950c46c8bf7ed84a046dc8998f7f4a51530cfe9f693d'),
    FORM:dict(path=FORM,bytes=7471,sha256='8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e'),
    NOTE:dict(path=NOTE,bytes=9946,sha256='ef2e30388827c40e02b99017350f434b33840ce5564c2d46b2bae9c10dac9150'),
    NATIVE:dict(path=NATIVE,bytes=34455,sha256='a03e6461d94010d7b1ccfbf9eecdb8e1d06389f3a690363e7b414d4cda9f2347')}
IO_SOURCES={
    'crates/product-cli/tests/form_stored_provider.rs',
    'crates/hwpx-package/tests/support/document_import_field_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_note_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_settings_inputs.rs',
    'crates/hwpx-package/tests/table_create_hwpx.rs',
    'crates/hwpx-package/examples/document_import_form_policies_support/mod.rs'}
FIXED_PACKAGES=(
    dict(path='implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx',
        bytes=15097,sha256='feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480'),
    dict(path='implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx',
        bytes=14556,sha256='02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7'))
SLOTS={f'P09-24-C{i:02}':f'p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01' for i in range(1,4)}


def require(ok,code):c.require(ok,'P203_'+code)


def pin(path,size,sha):
    result=dict(path=path,bytes=size,sha256=sha);v.pins([result])
    require(0<size<=MAX_FILE_BYTES,'INPUT_BYTE_BOUND');return result


def basename(name):
    require(isinstance(name,str) and bool(name) and name not in ('.','..')
        and not any(ch in name for ch in '/\\:'),'FIXTURE_BASENAME');return name


def merge(groups):
    result={}
    for rows in groups.values():
        for item in rows:
            checked=pin(item['path'],item['bytes'],item['sha256'])
            require(checked['path'] not in result or result[checked['path']]==checked,'CONFLICTING_DUPLICATE_PIN')
            result[checked['path']]=checked
    require(bool(result) and len(result)<=512,'FIXTURE_INVENTORY_BOUND');return result


def families(p77,form,note,native,header):
    p77_rows=[pin(row['path'],row['bytes'],row['sha256']) for row in p77['actual_inputs']]
    require(len(p77_rows)==len(v.pins(p77_rows))==36,'P77_EXACT36')
    matrix=[];seen=set()
    require(len(form['cases'])==5,'FORM_CASES5')
    for row in form['cases']:
        require(isinstance(row['case'],str) and row['case'] not in seen,'FORM_DISTINCT_CASES');seen.add(row['case'])
        for kind in ('source','output'):
            item=row[kind];matrix.append(pin(FORM_ROOT+basename(item['path']),item['bytes'],item['sha256']))
    require(len(v.pins(matrix))==10,'FORM_UNIQUE10')
    require(native['state']=='failed_semantic_non_green' and type(native['claims']['green_rows']) is int
        and native['claims']['green_rows']==0,'NATIVE_FAILED_EVIDENCE_PRESERVED')
    require(len(note['cases'])==len(native['cases'])==3,'NOTE_CASES3')
    locked=[];seen=set();native_rows={row['case_id']:row for row in native['cases']}
    require(set(native_rows)==set(SLOTS),'NATIVE_DISTINCT_KNOWN_CASES')
    for row in note['cases']:
        key=row['case_id'];require(key in SLOTS and key not in seen,'NOTE_DISTINCT_KNOWN_CASES');seen.add(key)
        actual=native_rows[key];require(actual['state']=='failed_semantic_non_green','NATIVE_CASE_FAILURE_PRESERVED')
        locked.append(pin(NOTE_ROOT+basename(row['file']),row['package_bytes'],row['package_sha256']))
        for lane in ('saved','reopened'):
            item=actual['snapshots'][lane]
            path='implementation/p09/evidence/private/'+SLOTS[key]+'/'+lane+'.hwpx'
            locked.append(pin(path,item['package_bytes'],item['package_sha256']))
    require(len(v.pins(locked))==9,'NOTE_UNIQUE9')
    groups=dict(P77=p77_rows,form_matrix=matrix,notes=locked,field_capture=[FIXED_PACKAGES[0]],
        object_capture=[FIXED_PACKAGES[1]],compiled_header=[header])
    inputs=merge(groups)
    require(all(item['path'].endswith('.hwpx') or item['path']==HEADER for item in inputs.values()),'KNOWN_INPUT_KINDS')
    return groups,inputs


def direct_file(root,item):
    pin(item['path'],item['bytes'],item['sha256']);path=root/item['path']
    require(path.resolve().is_relative_to(root.resolve()),'INPUT_OUTSIDE_ROOT')
    current=path
    while current!=root:
        require(not current.is_symlink() and not current.is_junction(),'INPUT_LINK_OR_REPARSE')
        require(current.parent!=current,'INPUT_ANCESTOR_BOUNDARY');current=current.parent
    require(path.is_file(),'INPUT_NOT_DIRECT_FILE')
    require(path.stat().st_size==item['bytes'],'INPUT_METADATA_SIZE');return path


def verify_bytes(q,inputs):
    for item in inputs.values():
        direct_file(c.ROOT,item);require(q.pin(item['path'])==item,'ACTUAL_FIXTURE_BYTE_HASH')


def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_runtime_fixture_inputs')
    with patch('subprocess.Popen',side_effect=AssertionError('P203_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P203_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P203_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==16 and not checked.skipped,'CONTRACT16');return 16


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT and 1<=args.run<=99,'CWD_RUN')
    target=b.s.scoped_path(f'implementation/p09/evidence/runtime-r07/p09-203-fixture-input-closure-run{args.run:02}.v1.json',fresh=True)
    context=r.observation.Context();owner=r.observation.Resources(context);q=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**r.flags(),
        runtime_scope_changed=False,EXE_bytes_rehashed=False,actual_Hangul_SQL_or_product_body_executed=False)
    try:
        owner.admit();q=r.Reader(owner,context);q.pin(SELF);q.pin(TEST);out['fixture_input_contract_tests_passed']=contracts()
        expected,names,exe=b.baseline(q);parent=q.json(b.run.PARENT['path'])
        modules=parent['source_module_instances'];require(len(modules)==59,'COMPILED_TEST_MODULES59')
        texts={}
        for name in sorted({row['path'] for row in modules}):
            require(q.pin(name)==expected[name],'FROZEN_TEST_MODULE_SOURCE');texts[name]=q.text(name)
        found={name for name,text in texts.items() if re.search(r'\b(?:std::)?fs::|include_(?:bytes|str)!',text)}
        require(found==IO_SOURCES,'EXACT_KNOWN_FIXTURE_IO_MODULES')
        for name,item in MANIFEST_PINS.items():
            direct_file(c.ROOT,item);require(q.pin(name)==item,'FROZEN_FIXTURE_MANIFEST')
            require(any(item['sha256'] in text for text in texts.values()),'MANIFEST_SHA_IN_FROZEN_RUST')
        for item in FIXED_PACKAGES:
            require(any(item['sha256'] in text for text in texts.values()),'FIXED_CAPTURE_SHA_IN_FROZEN_RUST')
        metadata={name:q.json(name) for name in MANIFEST_PINS}
        groups,inputs=families(metadata[P77],metadata[FORM],metadata[NOTE],metadata[NATIVE],expected[HEADER])
        verify_bytes(q,inputs);q.finish()
        out.update(state=PASS,binding=v.identity(names,expected,exe),
            manifest_pins=list(MANIFEST_PINS.values()),fixture_input_pins=list(inputs.values()),
            family_reference_counts={name:len(rows) for name,rows in groups.items()},
            family_reference_bytes={name:sum(row['bytes'] for row in rows) for name,rows in groups.items()},
            unique_fixture_inputs=len(inputs),unique_fixture_input_bytes=sum(item['bytes'] for item in inputs.values()),
            qualified_known_fixture_IO_sources=sorted(found),compiled_test_module_instances=59,
            old_manifest_overlap=sum(name in expected for name in inputs),
            dynamic_fixture_inputs_newly_explicit=sum(name not in expected for name in inputs),
            fixture_scope='KNOWN_PREEXISTING_TEST_MODULE_FIXTURES_NOT_ALL_PRODUCT_IO',
            every_known_fixture_byte_fresh_before_and_at_finish=True,
            native_note_original_failed_semantic_state_preserved=True,
            new_product_test_or_all_runtime_dependency_closure_proved=False,
            safe_runtime_exclusions=[],runtime_input_exclusions_authorized=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=r.observation.summary(owner)
        with target.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','fixture_input_contract_tests_passed','unique_fixture_inputs',
            'unique_fixture_input_bytes','error_code','resource_stop_reason')}),flush=True)
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
