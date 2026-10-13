"""Independent r328 metadata close; no product/Native or passed-test replay."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_worker_connection_v1 as worker
SELF="tools/p09/audit_case158_parent_connection_r328.py"
ADDED="<!-- BEGIN P09_R328_STATUS -->\n> 2026-10-13 P09 r328 — 원래 부모 engine 코드·worker·준비 입력 검사를 보존한 explicit physical Frame/row 연결 구현 및 CODE9 PASS. 공식151/249·잔여98·next158·delta0; 목표ACTIVE/P09·A12·A13 OPEN/P10 새 구현0.\n> 원bootstrap pins는 그대로, 두 실제읽기/lock/cost는 명시 physical projection으로 연결하고 최종 row에 semantic/physical 및 decoder5를 구분. 초기9테스트는 private engine globals에 source 이름이 없어 실패(r650); 실패source2개 보존 후 helper를 closure로 전달해 교정. r651 새CODE9 및 실제158 whole-template 함수/worker/private-env identity 연결검사 PASS; 실제 engine/Native/제품 호출0.\n> r652 현재원전체 inherited union+새연결코드/증거/qualified archive10/실패preimages 포함104fresh/104final 확인. semantic2609/276457089bytes, physical2609/259016188bytes, 정확11 alias만 조정. 원complete cost+decoder5=597.6761541초/600, CPUmax36.03%/가용RAMmin55.8637%/cleanupTrue. 새 immutable158 controller/DATA/qualification은 아직 포함되지 않아 fullpreflight/GO/제품 자격을 주장하지 않음.\n> 다음:whole current158 controller에 부모 adapter·원full oracle·worker capsule transport를 연결하고 새코드/DATA/검증증거 비용을 모두 포함한 fullpreflight→본문1회→독립승인. 후보margin2.3238초를 추정으로 사용하지 않고 초과 시 원본/전체입력/guard/rate/600 유지한 중복 IO 최적화를 먼저 수행. PCfreeze 원인·해결 미확정; 원151/root157/user문서/성공실패 보존·접근허용/HWP/UAC/OS·Defender·WSL/Git/삭제이동0.\n> 세부:implementation/p09/P09-361_CASE158_PARENT_CONNECTION_R328.md; 근거:r650-r652; 새source4개 p361-r328-qualified.\n<!-- END P09_R328_STATUS -->\n\n"
ARCHIVES=["tools/p09/runtime_envelope_parent_connection_v1.py","tools/p09/tests/test_runtime_envelope_parent_connection_v1.py","tools/p09/qualify_case158_parent_connection_r328.py","tools/p09/review_case158_parent_worker_full_cost_r328.py"]
DOCS=[dict(path="CURRENT_STATE.md",bytes=877371,sha256="4a7df076c40e1127b99a3706b0bfa716c0f4709a1aea0fe8bf8d03f628ab0462"),
    dict(path="implementation/p09/P09-361_SCAN_CANDIDATE_RETENTION.md",bytes=347771,sha256="634859cb25bc3223981bd4afe9aba45e4d846f78f3342ca3c3257d22ad6167d2")]

def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)()
    result=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        current158_product_or_Native_or_queue_acceptance_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        authority=a.read_exact(q,worker.AUTHORITY);a.read_exact(q,worker.ROOT)
        a.fields(authority,dict(accepted_count_after=151,next_runtime_index=158,
            resource_cleanup_confirmed=True,P09_gate="OPEN"),"UNCHANGED_ACTUAL151")
        a.exact(authority["runtime_candidate_pin"],worker.ROOT,"UNCHANGED_ACTUAL157")
        code=q.json("implementation/p09/evidence/p09-361-case158-parent-connection-code9-r651.v1.json")
        a.fields(code,dict(state="PASS_PARENT_CODE9_REAL158_WHOLE_ENGINE_NAMESPACE_CONNECTED_NOT_PRODUCT",
            contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            actual_current158_parent_or_worker_or_Native_executed=False),"CODE9_ONLY")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_QUALIFIED_CODE")
        a.exact(code["parent_connection_evidence"]["attempts"],0,"NO_ENGINE_BODY_EXECUTION")
        cost=q.json("implementation/p09/evidence/p09-361-case158-parent-worker-full-source-cost-r652.v1.json")
        a.fields(cost,dict(state="PASS_CURRENT_PARENT_WORKER_FULL_SOURCE_COST_REVIEW_NOT_CURRENT158_PREFLIGHT_OR_PRODUCT",
            cleanup_confirmed=True,full_current158_controller_DATA_or_preflight_qualified=False,
            current_input_scope_reduction_or_guard_rate_relaxation=False),"REVIEW_NOT_PREFLIGHT_OR_GO")
        a.exact(cost["complete_current_connection_candidate_seconds"],597.6761541094098,"ACTUAL_CANDIDATE_COST")
        a.exact(q.pin(cost["source_pin"]["path"]),cost["source_pin"],"CURRENT_COST_REVIEW_SOURCE")
        failure=q.json("implementation/p09/evidence/p09-361-case158-parent-code9-attempt001-failed-r650.v1.json")
        a.fields(failure,dict(state="FAILED_NOT_ACCEPTED",contracts=dict(run=9,errors=9,failures=0,skipped=0),
            cleanup_confirmed=True),"FAILED_PARENT_PREIMAGE_RETAINED")
        for name in ("tools/p09/runtime_envelope_parent_connection_v1.py",
            "tools/p09/tests/test_runtime_envelope_parent_connection_v1.py"):
            q.pin("implementation/p09/evidence/p361-r328-failed-parent001/"+name)
        for name in ARCHIVES:
            pin=q.pin(name);path="implementation/p09/evidence/p361-r328-qualified/"+name
            a.exact(q.pin(path),dict(pin,path=path),"QUALIFIED_ARCHIVE_EXACT")
        documents=[]
        for old in DOCS:
            pin,raw=q._read(old["path"],parse=True);q._bind(pin["path"],pin)
            data=bytes(raw);added=ADDED.encode("utf-8")
            a.require(data.endswith(added),"EXACT_APPENDED_R328")
            original=data[:-len(added)]
            a.exact(dict(bytes=len(original),sha256=hashlib.sha256(original).hexdigest()),
                {k:old[k] for k in ("bytes","sha256")},"ALL_PREVIOUS_DOCUMENT_BYTES_PRESERVED")
            documents.append(pin)
        q.pin("implementation/p09/P09-361_CASE158_PARENT_CONNECTION_R328.md")
        q.finish();g.check(force=True)
        result.update(state="PASS_R328_AUTHORITY151_PARENT_CONNECTION_AND_COST_METADATA_CLOSED_NOT_CURRENT158_OR_GATE",
            goal_status="ACTIVE",accepted_count_after=151,current_queue_remaining=98,next_case=158,
            current_generation_individual_cases=46,parent_CODE9_and_namespace_only=True,
            full_current158_controller_DATA_or_product_qualified=False,
            previous_documents_and_authority151_root157_preserved=True,
            failed_parent_source_and_result_preserved=True,qualified_source_archives=len(ARCHIVES),
            current_candidate_seconds=cost["complete_current_connection_candidate_seconds"],
            all_future_controller_DATA_and_qualification_costs_still_required=True,
            document_pins=documents,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            code=str(error);result["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_R328_METADATA_FAILURE"
    finally:g.close();result["cleanup_confirmed"]=g.cleanup
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
