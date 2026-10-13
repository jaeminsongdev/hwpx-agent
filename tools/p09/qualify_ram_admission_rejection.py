"""P357: 정확한065의 RAM admission 거절을 진단만 한다. runtime/GO가 아니다.

CPU 전용 원 validator/실패/placeholder/guard를 바꾸지 않는다. 새 실행·Native·
subprocess·thread·재시도·파일 쓰기는 없다. runtime 연결은 별도 profile 검증이 필요하다.
"""
import hashlib
import json
import math
from pathlib import Path
import packed_receipt_json as packed

ROOT=Path(__file__).resolve().parents[2]
DIR='implementation/p09/evidence/locked-r07/'
PINS=[
    dict(path=DIR+'p340-light-run063.v1.json',bytes=69306,sha256='3a1216d510063794c449a5fc622c46a4bfaadf99b87079ca9359a2de344094c6'),
    dict(path=DIR+'p340-light-review-run064.v1.json',bytes=65674,sha256='72be9720d93578ac456412ec2565e24f0999e3a17a41f3b05e9d9da90c734434'),
    dict(path=DIR+'p340-case-110-run065.v1.json',bytes=461324,sha256='60fd6251f28f09f7ad6dbeb24524d5cb5ca9511cacdb7f0dfbc8d35d00519283'),
    dict(path=DIR+'cases/p340-failure-110-run065.json',bytes=12256,sha256='a020fbb8a93f1220e84b3e8aa78d5559d242af755090564b0b413945f682d805')]
CODE2=[
    dict(path='tools/p09/resume_preserved106_queue_runtime.py',bytes=152778,sha256='9fcf1446bf38e14b67c05f10f25b693e6656a9864227d7d71a21ae9bc27b8473'),
    dict(path='tools/p09/tests/test_preserved106_queue_runtime.py',bytes=123113,sha256='c01811db277830995f6fb911cd7f181800f17170cfdf0a8037938d1583c54819')]
SCHEMA='hwpx-agent.p09-preserved106-fixed-runtime-queue/v21'

def require(ok,code):
    if not ok:raise ValueError('RAM_ADMISSION_DIAGNOSTIC_'+code)

def number(value):
    return type(value) in (int,float) and math.isfinite(value)

def validate(light,fresh,root,side):
    for doc in (light,fresh,root):
        require(doc['schema_version']==SCHEMA and doc['selected_test_index']==110
            and doc['prior_runtime_plan']['runtime_source_qualified_individual_cases']==103
            and doc['current95_code_pins'][-2:]==CODE2
            and doc['resource_watcher_cleanup_confirmed'] is True,'EXACT_CURRENT103_CODE_AND_CLEANUP')
        require(doc['actual_product_child_executed'] is False
            and all(doc[k]=='OPEN' for k in ('P09_gate','A12_gate','A13_gate'))
            and doc['product_complete'] is False,'NO_PRODUCT_OR_GATE')
    require(light['state']=='PASS_PRESERVED106_NEXT_QUEUE_NOT_ACTUAL_OR_GATE'
        and light['runtime_contract_executions']==862
        and fresh['state']=='PASS_PRESERVED106_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT'
        and fresh['runtime_contract_executions']==0 and fresh['reused_light_contract_executions']==862
        and fresh['reviewed_light_pin']==PINS[0],'EXACT862_AND_DISTINCT_FRESH')
    require(root['qualified_light_pin']==PINS[0] and root['independent_fresh_pin']==PINS[1]
        and root['qualified_contract_checkpoint_statistics']==light['contract_checkpoint_statistics']
        and root['terminal_parent_failure_sidecar_pin']==PINS[3],'LITERAL_QUALIFICATION_AND_SIDECAR')
    require(root['state']=='FAILED_NOT_ACCEPTED' and root['error_code']=='TERMINAL_FAILURE_EXACT_STOP_NOT_PASS'
        and root['resource_stop_reason'] is None and root['failure_diagnostic']['stage']=='owned_parent'
        and root['runtime_contract_executions']==root['accepted_exact_product_body_count']==0
        and root['source_attempted'] is True and root['source_qualified'] is False
        and 'runtime_plan' not in root and root.get('case_receipt_pin') is None,'REJECTION_PRESERVED_NOT_ACCEPTED')
    require(side['state']=='REJECTED_ORIGINAL_PARENT_DIAGNOSTIC_NOT_ACCEPTED'
        and side['original_validation_error']==root['error_code']
        and side['diagnostic_only'] is True and side['runtime_accepted'] is False
        and side['owner_done'] is True and side['owner_cleanup_confirmed'] is True
        and side['owner_stop_reason'] is None and side['product_body_executed_by_diagnostic'] is False
        and side['live_guard_sampler_or_frame_restarted'] is False
        and side['original_parent_state_reason_preserved'] is True,'ORIGINAL_TERMINAL_DIAGNOSTIC_ONLY')
    frame=root['terminal_source_frame'];h=frame['handles']
    require(side['original_frame_snapshot']==frame and frame['frame_state']=='CLOSED'
        and frame['registered_live_frame'] is False and frame['input_count']==1658
        and frame['input_bytes']==121216238 and frame['actual_byte_boundaries']==[]
        and root['actual_input_path_guard_selected'] is True
        and root['actual_boundary_adapter_restored'] is True
        and root['actual_source_path_guard_diagnostics']==[],'CLOSED_BEFORE_ANY_BYTE_BOUNDARY')
    require(type(h['input_lock_handles_opened']) is int and h['input_lock_handles_opened']==1966
        and h['input_lock_handles_closed']==1966 and h['input_lock_cleanup_confirmed'] is True
        and h['borrowed_byte_streams'] is None,'EXACT_ACQUISITION_NO_BORROWER')
    require(all(type(h[k]) is int and h[k]==0 for k in ('input_lock_handles_remaining',
        'active_reader_bindings','active_byte_streams','handle_close_failed_attempts')),'NO_LIVE_HANDLE_OR_STREAM')
    p=side['original_parent_document']
    require(p['state']=='DEFERRED_NOT_STARTED' and p['stop_reason']==p['resource_stop_reason']=='DEFERRED_STABLE_RESOURCE_WINDOW'
        and p['operation_phase']=='admission' and p['task']=='p204-r07-case-110-tests'
        and p['binding']==root['binding'] and p['selected_test_names']==[root['selected_test_name']]
        and p.get('job_final') is None and p['owned_source_reader_passes']==[]
        and p['owned_tree_empty'] is True and p['cleanup_confirmed'] is True
        and p.get('exit_code') is None and p.get('tests_passed') is None,'ORIGINAL_PARENT_ADMISSION_DEFER')
    require(all(p[k] is False for k in ('worker_created','job_assigned','writer_authorized',
        'actual_job_membership_checked','owned_limits_verified','heavy_work_started','actual_product_child_executed')),
        'NO_JOB_OR_WORKER_OR_PRODUCT')
    rows=p['samples'];require(type(rows) is list and len(rows)==6,'EXACT_SIX_ORIGINAL_WINDOWS')
    for row in rows:
        cpu,ram,commit=(row[k] for k in ('system_cpu_percent','available_ram_percent','commit_used_percent'))
        require(all(number(v) for v in (cpu,ram,commit)) and 0<=cpu<98
            and 8<=ram<10 and 0<=commit<95,'RAM_START_WINDOW_NOT_CPU_OR_HARD_STOP')
    return dict(state='PASS_STRICT_RAM_ADMISSION_DIAGNOSTIC_NOT_RUNTIME_OR_GO',
        original_failed_preserved=True,original_parent_reason='DEFERRED_STABLE_RESOURCE_WINDOW',
        found_cause='RAM_START_WINDOW_REJECTED_BY_CPU_ONLY_TERMINAL_CAPTURE',
        RAM_available_min_percent=min(r['available_ram_percent'] for r in rows),
        RAM_available_max_percent=max(r['available_ram_percent'] for r in rows),
        Native_handles_opened_and_closed=1966,actual_product_child_executed=False,
        cleanup_confirmed=True,current_GO=False,runtime_recovery_connected=False,
        guard_or_original_validator_changed=False)

def load(pin):
    # 변조/급증한 파일도 전체 read_bytes로 먼저 할당하지 않는다.
    require(pin in PINS and type(pin['bytes']) is int and 0<pin['bytes']<=1048576,'KNOWN_BOUNDED_ARTIFACT')
    path=ROOT.joinpath(pin['path'])
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_ARTIFACT_ONLY')
    with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
    require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'EXACT_ARTIFACT_BYTES')
    doc=json.loads(raw)
    return packed.unpack(doc,lambda:None) if set(doc)==packed.KEYS else doc

def main():
    result=validate(*(load(pin) for pin in PINS))
    placeholder=ROOT.joinpath(DIR+'cases/p340-case-110-run065.json')
    require(placeholder.is_file() and not placeholder.is_symlink() and not placeholder.is_junction()
        and placeholder.stat().st_size==0,'ORIGINAL_ZERO_PLACEHOLDER_RETAINED')
    print(json.dumps(result))
    return 0

if __name__=='__main__':raise SystemExit(main())
