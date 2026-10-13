"""Independent metadata closure, not full158 product/Native qualification."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_worker_connection_v1 as connection
SELF="tools/p09/audit_case158_worker_connection_r327.py"
PREFIX="<!-- BEGIN P09_R327_CURRENT_STATUS -->\n> 2026-10-13 P09 r326-r327 — full-oracle 구성요소와 parent/worker 원본 재읽기 정책 연결 진전. 공식151/249·잔여98·next158·delta0. P09/A12/A13 OPEN; full249/signed16/reconciliation 미완료; P10 새 구현 없음; 목표ACTIVE.\n> r326 CODE10/CODE9 PASS 및 실제 projected12 입력 두 경계 CLOSED 검사 완료. CLOSED를 COMMITTED/제품으로 승격하지 않음. r327 새 worker CODE12 PASS; 실제11 매핑 canonical6382bytes·파일6383bytes(LF 포함)를 별도 대조하고 step158을 실제151 권위와 compiled249 목록에서 고정.\n> r647 실제 owned Python worker의 원래 GO/Job 검사 및 원본 읽기 진단1회 차단·API 복원 PASS. 제품 subprocess 호출은 진단 sink로 가로챘으므로 Rust/Cargo/제품/전체Native frame 실행0; 새 공식승인0. Job CPU cap6.25%/affinity1/BelowNormal/peak42.91MiB/종료active0·CPUmax22.38%/가용RAMmin58.4694%/cleanupTrue.\n> 다음:새 부모 전체 engine·semantic/physical oracle·worker capsule transport 연결을 qualification하고 immutable158 controller/DATA 및 그 모든 입력을 비용에 포함한 fullpreflight→제품1회→독립승인. 593.6697초는 이전 후보 비용이며 새 코드/증거/설정의 비용 포함을 주장하지 않음. PC프리즈 원인·해결 미확정; 기존151 권위/원본/성공실패/user문서 보존·접근허용/HWP/UAC/OS설정/Git/삭제이동0.\n> 세부:implementation/p09/P09-361_CASE158_WORKER_CONNECTION_R327.md; 근거:r640-r647; qualified source10개 p361-r327-qualified.\n<!-- END P09_R327_CURRENT_STATUS -->\n\n"
DOCS=[dict(path="CURRENT_STATE.md",bytes=875752,sha256="6f21eaed3db75468afe51b0d1aad58db2758ca8240f03e65efa26a7da53e1f56"),
    dict(path="implementation/p09/P09-361_SCAN_CANDIDATE_RETENTION.md",bytes=346152,sha256="4bdd03ad15000daddfa3f81ed5d79008bc94c925fe7f4def1fd433f36d56efcc")]
SOURCES=["tools/p09/runtime_envelope_raw_access_policy_v1.py","tools/p09/tests/test_runtime_envelope_raw_access_policy_v1.py","tools/p09/runtime_envelope_full_oracle_connection_v1.py","tools/p09/tests/test_runtime_envelope_full_oracle_connection_v1.py","tools/p09/probe_case158_policy_frame_r326.py","tools/p09/runtime_envelope_worker_connection_v1.py","tools/p09/tests/test_runtime_envelope_worker_connection_v1.py","tools/p09/qualify_case158_worker_connection_r327.py","tools/p09/prepare_case158_worker_data_r327.py","tools/p09/probe_case158_owned_worker_policy_r327.py"]
EVIDENCE="implementation/p09/evidence/"

def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)()
    result=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        full_current158_product_or_Native_or_queue_acceptance_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        ar=a.read_exact(q,connection.AUTHORITY)
        a.fields(ar,dict(accepted_count_after=151,next_runtime_index=158,
            resource_cleanup_confirmed=True,P09_gate="OPEN"),"UNCHANGED_OFFICIAL151")
        a.exact(ar["runtime_candidate_pin"],connection.ROOT,"ACTUAL157_ROOT")
        a.read_exact(q,connection.ROOT)
        for suffix,expected,count in (
            ("p09-361-case158-raw-live-access-policy-code10-r640.v1.json","PASS_",10),
            ("p09-361-case158-full-oracle-connection-code9-r642.v1.json","PASS_",9),
            ("p09-361-case158-worker-policy-code12-actual11-capsule-r645.v1.json","PASS_",12)):
            row=q.json(EVIDENCE+suffix)
            a.require(row["state"].startswith(expected) and row["cleanup_confirmed"] is True,"CODE_COMPONENT_ONLY")
            a.exact(row["contracts"],dict(run=count,errors=0,failures=0,skipped=0),"EXACT_COMPONENT_COUNTS")
            for pin in row["new_code_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_COMPONENT_BYTES")
        failed=q.json(EVIDENCE+"p09-361-case158-full-oracle-code9-attempt001-failed-r641.v1.json")
        a.require(failed["state"].startswith("FAILED") and failed["contracts"]["errors"]==9,"PRESERVED_FAILED_FIXTURE")
        failure=q.json(EVIDENCE+"p09-361-case158-worker-namespace-inspection-failed-r644.v1.json")
        a.exact(failure["error_code"],"FLAT_QUEUE_CONFIG_REQUIRED","PRESERVED_NAMESPACE_FAILURE")
        focus=q.json(EVIDENCE+"p09-361-case158-actual-policy-projected-frame12-r643.v1.json")
        a.require(focus["cleanup_confirmed"] is True and focus["focused_frame"]["frame_state"]=="CLOSED"
            and focus["worker_process_policy_or_whole_product_connection_qualified"] is False,"CLOSED_NOT_PRODUCT")
        prep=q.json(EVIDENCE+"p09-361-case158-step-capsule-preparation-r646.v1.json")
        a.require(prep["cleanup_confirmed"] is True and prep["product_or_worker_or_Native_executed"] is False,"PREP_NOT_PRODUCT")
        actual=q.json(EVIDENCE+"p09-361-case158-owned-worker-policy-diagnostic-r647.v1.json")
        a.fields(actual,dict(state="PASS_ACTUAL158_OWNED_WORKER_GO_JOB_RAW_POLICY_PRODUCT_CALL_INTERCEPTED_NOT_PRODUCT",
            cleanup_confirmed=True,actual_product_or_Native_frame_executed=False,full_current158_worker_dispatch_qualified=False),"DIAGNOSTIC_NOT_PRODUCT")
        a.fields(actual["owned_Job_final"],dict(active_processes=0,owned_processes=[]),"OWNED_DIAGNOSTIC_EMPTY")
        child=actual["child_diagnostic"];policy=child["worker_policy"]["raw_access_policy"]
        a.fields(child,dict(product_child_executed=False,intercepted_product_subprocess_calls=1,
            deliberate_raw_access_attempts=1),"DELIBERATE_SINK_AND_DENIAL")
        a.fields(policy,dict(mapped_raw_receipt_count=11,denied_live_raw_access_attempts=1,
            all_original_open_function_identities_restored=True),"ACTUAL_WORKER_POLICY_RESTORED")
        for pin in actual["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ACTUAL_DIAGNOSTIC_SOURCES")
        raw_pin,raw=q._read(actual["raw_capsule_file_pin"]["path"],parse=True)
        q._bind(raw_pin["path"],raw_pin);a.exact(raw_pin,actual["raw_capsule_file_pin"],"RAW_CAPSULE_FILE6383")
        data=bytes(raw);canonical=prep["candidate_capsule_ascii"].encode("ascii")
        a.exact(data,canonical+b"\n","EXPLICIT_CANONICAL_TO_DISK_LF")
        binding,_=connection.decode(data,{k:raw_pin[k] for k in ("bytes","sha256")},g.check)
        a.exact(len(binding.originals),11,"ALL11_ACTUAL_POLICY_BINDINGS")
        a.exact(q.json(prep["candidate_config_path"]),prep["candidate_config"],"IMMUTABLE158_STEP")
        for name in SOURCES:
            p=q.pin(name);archive="implementation/p09/evidence/p361-r327-qualified/"+name
            a.exact(q.pin(archive),dict(p,path=archive),"EXACT_ARCHIVE")
        docs=[]
        for old in DOCS:
            pin,buffer=q._read(old["path"],parse=True);q._bind(pin["path"],pin)
            current=bytes(buffer);prefix=PREFIX.encode("utf-8")
            a.require(current.endswith(prefix),"EXACT_R327_DOCUMENT_APPEND")
            rest=current[:-len(prefix)]
            a.exact(dict(bytes=len(rest),sha256=hashlib.sha256(rest).hexdigest()),
                {k:old[k] for k in ("bytes","sha256")},"ENTIRE_PRE_R327_DOCUMENT_BYTES_PRESERVED")
            docs.append(pin)
        q.pin("implementation/p09/P09-361_CASE158_WORKER_CONNECTION_R327.md")
        q.finish();g.check(force=True)
        result.update(state="PASS_R327_CURRENT151_WORKER_CONNECTION_METADATA_CLOSURE_NOT_CURRENT158_OR_GATE",
            goal_status="ACTIVE",accepted_count_after=151,current_queue_remaining=98,next_case=158,
            current_generation_individual_cases=46,document_pins=docs,qualified_source_archives=len(SOURCES),
            prior_document_whole_bytes_preserved=True,original_authority151_and_root157_unchanged=True,
            failed_diagnostics_preserved=True,worker_product_call_intercepted_not_product=True,
            parent_whole_engine_oracle_and_capsule_dispatch_connection_qualified=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            code=str(error);result["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_FINAL_METADATA_FAILURE"
    finally:g.close();result["cleanup_confirmed"]=g.cleanup
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
