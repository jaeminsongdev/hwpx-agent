"""Close r329 metadata only; keep actual attempt unaccepted."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_worker_connection_v1 as w
SELF="tools/p09/audit_case158_controller_r329.py"
APPEND="<!-- BEGIN P09_R329_STATUS -->\n> 2026-10-13 P09 r329 — current158 V19 부모/fulloracle/worker-capsule 통합 실행기 및 immutable DATA 구현. 공식151/249·잔여98·next158·delta0; 목표ACTIVE/P09·A12·A13 OPEN/P10 새 구현0.\n> preflight020은 이전157 판정의 pressure/window AST marker 충돌로 실패; 실제151 승인에 쓰인 CODE5/r612 격리marker 연결재사용. preflight021~023은 원64 helper 상한 실패. 모듈숨김/상한완화 없이14 신규소스 및원lean/V18/bundle 정의를 exact namespace로연결하고모든원소스pin보존. r658 실제binding 후import변화0/fresh913·final913 진단.\n> preflight024 실제PASS:compiledRust787/import63/원metadata10계약/fresh913·final913/physical2593/모델595.7088457초/600·decoder5포함/CPUmax42.86%/가용RAMmin56.5260%/cleanupTrue. 이후158제품시도1회는 Native pressure terminal latch로exit1·runtime root 부재; 마지막원관측metadata_hash2593. 제품본문/완전capture/FrameCOMMITTED/explicit handle counter 증거없음·승인0·관련Python잔여0. r660 FAILED 보존; 당시CPU원인/제품실행여부/explicit Native cleanup 증명불가 유지.\n> 원본밖최종receipt open도 liveNative callback을불렀던V1 정책의 latch 후기록차단을회귀재현. 원본guard-before-deny 및원physical reader/decoder/Frame 보호는유지하고원본아닌output/cleanup에추가Native checkpoint를걸지않는명시V2 parent dependency 구현. CODE4/r661 및새controller CODE7/r662 PASS. 이는실제CPU원인증명/제품PASS아님.\n> 현재qualified V19/data024는receipt-safe V2이며새preflight025/제품/독립승인 NOT_RUN. old preflight024는이전V1 버전만증명; 같은본문blind재시도없음. 다음은V2 전체사전검증 및failed attempt와구분되는실행/진단기록경로 qualification 후제품1회·독립승인. PCfreeze 해결미확정/기존권위·원본·문서·성공실패/새source8 exact archive보존·한글/접근허용/UAC/OS·Defender·WSL/Git/삭제이동0.\n> 세부:implementation/p09/P09-361_CASE158_CONTROLLER_R329.md; failed020~023/pass024/r654~r662; source p361-r329-qualified.\n<!-- END P09_R329_STATUS -->\n\n"
SOURCES=["tools/p09/flat_current_queue_envelope_runtime_v19.py","tools/p09/tests/test_flat_current_queue_envelope_runtime_v19.py","tools/p09/runtime_envelope_namespace_bundle_v1.py","tools/p09/runtime_envelope_raw_access_policy_v2.py","tools/p09/runtime_envelope_parent_connection_v2.py","tools/p09/tests/test_runtime_envelope_raw_access_policy_v2.py","tools/p09/qualify_case158_controller_v19_r329.py","tools/p09/diagnose_case158_helper_count_r329.py"]
DOCS=[dict(path="CURRENT_STATE.md",bytes=879195,sha256="e18a86b5dc965082a0be3db6f674c0413d14f36df126e01268ee5f95755c97d6"),
dict(path="implementation/p09/P09-361_SCAN_CANDIDATE_RETENTION.md",bytes=349595,sha256="6c750e1fc90074352e7c4aca12f69875b88ddb78dd822b5e888c7df3cfd67217")]
E="implementation/p09/evidence/"
def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        ar=a.read_exact(q,w.AUTHORITY);a.read_exact(q,w.ROOT)
        a.fields(ar,dict(accepted_count_after=151,next_runtime_index=158,resource_cleanup_confirmed=True),"UNCHANGED151")
        a.exact(ar["runtime_candidate_pin"],w.ROOT,"UNCHANGED157")
        for n in (20,21,22,23):
            failed=q.json(E+f"p09-361-case158-envelope-controller-preflight0{n}.v1.json")
            a.fields(failed,dict(state="FAILED_NOT_ACCEPTED",product_worker_or_Native_frame_executed=False,
                cleanup_confirmed=True),"PRESERVED_FAILED_PREFLIGHT")
        passed=q.json(E+"p09-361-case158-envelope-controller-preflight024.v1.json")
        a.fields(passed,dict(state="PASS_REVIEWED_METADATA_CONNECTION_PREFLIGHT_NOT_NATIVE_OR_PRODUCT_OR_ACCEPTANCE",
            imports=63,current_Rust=787,fresh_inputs=913,final_fresh_hashes=913,cleanup_confirmed=True),"OLD_V1_PREFLIGHT_ONLY")
        a.exact(passed["complete_runtime_budget"]["predicted_runtime_combined_seconds"],595.7088456562586,"OLD_OBSERVED_COST")
        fail=q.json(E+"p09-361-case158-v19-actual-run001-failed-root-absent-r660.v1.json")
        a.fields(fail,dict(state="FAILED_NOT_ACCEPTED_RUNTIME_ROOT_ABSENT",accepted_count_delta=0,
            runtime_root_exists=False,explicit_handle_cleanup_receipt_available=False,
            actual_product_body_or_complete_capture_proven=False),"NO_FABRICATED_BODY_OR_CLEANUP")
        a.require(not (a.c.ROOT/(E+"p09-361-case158-current-runtime-run001.v1.json")).exists(),"ROOT_STILL_ABSENT")
        for filename,count in (("p09-361-case158-receipt-safe-policy-code4-r661.v1.json",4),
            ("p09-361-case158-envelope-controller-code7-r662.v1.json",7)):
            code=q.json(E+filename)
            a.require(code["state"].startswith("PASS_") and code["cleanup_confirmed"] is True,"CURRENT_CODE_ONLY")
            a.exact(code["contracts"],dict(run=count,errors=0,failures=0,skipped=0),"CURRENT_CODE_COUNTS")
            for p in code["new_code_pins"]+code.get("source_pins",[]):a.exact(q.pin(p["path"]),p,"CURRENT_QUALIFIED_BYTES")
        data=q.json(E+"p09-361-case158-envelope-controller-data024.v1.json")
        a.fields(data,dict(index=158,before=151,run=1),"CURRENT_DATA")
        a.exact(q.pin(data["qualification_pin"]["path"]),data["qualification_pin"],"CURRENT_DATA_QUAL")
        for p in data["controller_code_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_DATA_SOURCES")
        for name in SOURCES:
            p=q.pin(name);archive=E+"p361-r329-qualified/"+name
            a.exact(q.pin(archive),dict(p,path=archive),"ARCHIVE_EXACT")
        docs=[]
        for old in DOCS:
            p,raw=q._read(old["path"],parse=True);q._bind(p["path"],p);b=bytes(raw);suffix=APPEND.encode("utf-8")
            a.require(b.endswith(suffix),"EXACT_DOCUMENT_APPEND")
            a.exact(dict(bytes=len(b)-len(suffix),sha256=hashlib.sha256(b[:-len(suffix)]).hexdigest()),
                {k:old[k] for k in ("bytes","sha256")},"ALL_PREVIOUS_DOCUMENT_BYTES")
            docs.append(p)
        q.pin("implementation/p09/P09-361_CASE158_CONTROLLER_R329.md");q.finish();g.check(force=True)
        out.update(state="PASS_R329_CURRENT151_V19_PREFLIGHT_FAILURE_REVIEW_RECEIPT_SAFE_V2_CODE_NOT_CURRENT158_OR_GATE",
            goal_status="ACTIVE",accepted_count_after=151,current_queue_remaining=98,next_case=158,
            current_generation_individual_cases=46,old_V1_full_preflight_passed=True,
            actual_attempt_failed_and_root_absent=True,actual_body_and_explicit_native_cleanup_unproven=True,
            current_receipt_safe_V2_CODE4_and_controller_CODE7_passed=True,
            current_V2_full_preflight_or_product_or_queue_acceptance_qualified=False,
            previous_documents_and_authority151_root157_preserved=True,
            qualified_source_archives=len(SOURCES),document_pins=docs,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        out["error_type"]=type(e).__name__
        if isinstance(e,ValueError):
            import re
            msg=str(e);out["error_code"]=msg if re.fullmatch("[A-Za-z0-9_]{1,256}",msg) else "REDACTED_R329_AUDIT_ERROR"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
