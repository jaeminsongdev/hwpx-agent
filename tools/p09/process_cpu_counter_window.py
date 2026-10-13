"""P310: bounded raw PerfProc CPU window. Diagnostic only; not runtime/STOP override.
기존 guard/Windows sampler와 분리된 전후 두 조회의 계산기. 누적 카운터를 CPU%로 오인하지 않는다.
PID/원 raw elapsed token/instance 동일성을 확인한다. 명령줄·이미지 경로는 받지 않는다.
"""
import json
import math
import re
MAX_ROWS=4096
MAX_BYTES=4*1024*1024
SELF='tools/p09/process_cpu_counter_window.py'
TEST='tools/p09/tests/test_process_cpu_counter_window.py'
COLLECTOR='tools/p09/read_process_cpu_counter_snapshot.ps1'
SCHEMA='hwpx-agent.p09-perfproc-raw-snapshot/v1'
WINDOW='hwpx-agent.p09-perfproc-cpu-window/v1'
KEYS={'pid','name','creating_pid','raw_elapsed_token','cpu_100ns','sys_100ns',
    'frequency_sys100ns','private_bytes','working_set_bytes'}
WATCH={'MsMpEng','git','python','cargo','rustc','vmmemWSL','codex','ChatGPT','WmiPrvSE','pwsh'}
DOC='https://learn.microsoft.com/en-us/previous-versions/aa394323(v=vs.85)'

def require(ok,code):
    if not ok:raise ValueError('PERFPROC_'+code)

def raw_integer(value):
    require(isinstance(value,str) and bool(re.fullmatch(r'0|[1-9][0-9]{0,19}',value)),'RAW_DECIMAL_STRING')
    n=int(value);require(n<=2**64-1,'RAW_UINT64_BOUND');return n

def snapshot(d):
    require(isinstance(d,dict) and set(d)=={'schema_version','counter_class','query_started_utc',
        'query_finished_utc','operation_timeout_seconds','rows'} and d['schema_version']==SCHEMA
        and d['counter_class']=='Win32_PerfRawData_PerfProc_Process'
        and d['operation_timeout_seconds']==5 and type(d['operation_timeout_seconds']) is int,'SNAPSHOT_SCHEMA')
    require(all(isinstance(d[k],str) and re.fullmatch(r'[0-9TZ:.+\-]{20,40}',d[k])
        for k in ('query_started_utc','query_finished_utc')),'BOUNDED_QUERY_TIMESTAMPS')
    require(isinstance(d['rows'],list) and 2<=len(d['rows'])<=MAX_ROWS
        and len(json.dumps(d,ensure_ascii=True).encode())<=MAX_BYTES,'ROW_OR_BYTE_BUDGET')
    result={}
    for row in d['rows']:
        require(isinstance(row,dict) and set(row)==KEYS,'CLOSED_ROW_FIELDS')
        require(type(row['pid']) is int and 0<=row['pid']<=2**32-1
            and type(row['creating_pid']) is int and 0<=row['creating_pid']<=2**32-1,'PID_UINT32')
        name=row['name']
        require(isinstance(name,str) and 0<len(name)<=128 and not any(ch in name for ch in '\\/:\r\n\t')
            and not any(ord(ch)<32 for ch in name),'INSTANCE_NOT_PATH_OR_COMMAND_LINE')
        key=('pseudo',name) if row['pid']==0 else ('process',row['pid'])
        require(key not in result and (row['pid']!=0 or name in ('Idle','_Total')),'UNIQUE_PID_OR_PSEUDO')
        n={k:raw_integer(row[k]) for k in KEYS-{'pid','name','creating_pid'}}
        require(n['frequency_sys100ns']==10000000 and n['sys_100ns']>0,'EXACT_100NS_FREQUENCY')
        result[key]=dict(row,numeric=n)
    require(('pseudo','Idle') in result and ('pseudo','_Total') in result,'IDLE_AND_TOTAL_REQUIRED')
    return result

def window(before,after,processors):
    require(type(processors) is int and 1<=processors<=64,'ONE_PROCESSOR_GROUP_BOUND')
    a=snapshot(before);b=snapshot(after);rows=[];drift=0
    for key in a.keys()&b.keys():
        x,y=a[key],b[key]
        if key[0]!='pseudo' and (x['raw_elapsed_token']!=y['raw_elapsed_token']
            or x['name']!=y['name'] or x['creating_pid']!=y['creating_pid']):
            drift+=1;continue
        delta=y['numeric']['cpu_100ns']-x['numeric']['cpu_100ns']
        ticks=y['numeric']['sys_100ns']-x['numeric']['sys_100ns']
        require(delta>=0 and ticks>0,'COUNTER_RESET_OR_NONADVANCING_WINDOW')
        value=100*delta/(ticks*processors)
        require(math.isfinite(value) and 0<=value<=100.5,'MACHINE_CPU_NOT_CLAMPED')
        # Provider timing/quantization can cause a small overshoot; preserve, never clamp it to100.
        rows.append(dict(pid=y['pid'],name=y['name'],creating_pid=y['creating_pid'],
            machine_CPU_percent=round(value,6),sample_seconds=ticks/10000000,
            private_bytes=y['numeric']['private_bytes'],working_set_bytes=y['numeric']['working_set_bytes']))
    idle=next(x for x in rows if x['name']=='Idle' and x['pid']==0)
    total=next(x for x in rows if x['name']=='_Total' and x['pid']==0)
    live=[x for x in rows if x['pid']!=0]
    live.sort(key=lambda x:(-x['machine_CPU_percent'],x['pid']))
    watched=[x for x in live if re.sub(r'#[0-9]+$','',x['name']) in WATCH]
    require(len(watched)<=256,'WATCHED_OUTPUT_BOUND')
    return dict(schema_version=WINDOW,scope='DIAGNOSTIC_WINDOW_NOT_GUARD_OR_CAUSE',processor_count=processors,
        before_rows=len(a),after_rows=len(b),compared_process_count=len(live),identity_drift_skipped=drift,
        disappeared_count=len(a.keys()-b.keys()),new_count=len(b.keys()-a.keys()),top8=live[:8],watched=watched,
        idle_machine_CPU_percent=idle['machine_CPU_percent'],total_including_idle_machine_CPU_percent=total['machine_CPU_percent'],
        host_busy_from_idle_percent=round(100-idle['machine_CPU_percent'],6),
        raw_elapsed_token_interpreted_as_wall_time=False,raw_uint64_as_decimal_strings_preserved=True,
        source_scope_or_guard_changed=False,CPU_cause_or_PC_freeze_resolution_established=False,official_counter_reference=DOC)
