"""r330 metadata closure; preserve CPU stops and no new product acceptance."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_worker_connection_v1 as w
SELF="tools/p09/audit_case158_admission_r330.py"
ADD="<!-- BEGIN P09_R330_STATUS -->\n> 2026-10-13 P09 r330 — receipt-safe V2 전체preflight025 CPUwarning STOP 후검증코드중복준비IO 검토·same-reader admission 최적화구현. 공식151/249·잔여98·next158·delta0; 목표ACTIVE/P09·A12·A13 OPEN/P10 새구현0.\n> preflight025 FAILED:72.7414s/528fresh/574reads/96439638bytes/final0/CPUmax90.45%/가용RAMmin46.5937%/cleanupTrue. 경고직전ownCPU0%/private46.6836MiB; 마지막System43.18→90.45%. 이후2초accessible PID표본은경고와동시가아니므로CPU90·Defender 원인을귀속하지않음. 제품/Native시작0.\n> 같은reader에서preflight_data→binding이 own_inputs를중복호출하는경로를제거하는명시admission wrapper 구현/CODE7 r664 PASS. sameowner·sameReader·pre-finish만재사용/매호출원checkpoint 및pinledger동일성확인/다른reader·finalphase재사용금지/반환dict변형격리. parsed source/byte/hash cache·원finalfresh·Native두읽기대체0. 기존V19 body보존명시dependency연결 CODE7/r665 PASS·새DATA025.\n> 수정 fullpreflight026은final409/920에서CPU75.69%경고FAILED/165.3233s/1333reads/197489419bytes/cleanupTrue. 마지막5표본ownCPU0%/private46.7617MiB. 준비중복제거는코드자격까지이며전체PASS/실제CPU·PCfreeze개선·원인미증명. failed025/026 및r666 검토원장보존·같은실행blind재시도0.\n> 현재성공한제품/새승인0·root158run001부재·실패attempt와구분되는새실행identity/진단기록qualification 미완료. 다음은중단구간IO·동시외부CPU발생증거의bounded연결을점검하고원scope/guard/rate/600·720·1200/15/decode5유지한새whole qualification 후독립적제품시도. 원151/157/user문서/성공실패/source4exactarchive보존·한글/접근허용/UAC/OS·Defender·WSL/Git/삭제이동0.\n> 세부:implementation/p09/P09-361_CASE158_ADMISSION_R330.md; 근거:pref025-026/r664-r666; source p361-r330-qualified.\n<!-- END P09_R330_STATUS -->\n\n"
SOURCES=["tools/p09/flat_current_queue_envelope_runtime_v19.py","tools/p09/tests/test_flat_current_queue_envelope_runtime_v19.py","tools/p09/same_reader_source_admission_once_v1.py","tools/p09/tests/test_same_reader_source_admission_once_v1.py"]
DOCS=[dict(path="CURRENT_STATE.md",bytes=881375,sha256="ec038774768495056ab1a7afdb7d1325fe410a474a801b65263f66c6add8f225"),
dict(path="implementation/p09/P09-361_SCAN_CANDIDATE_RETENTION.md",bytes=351775,sha256="2bcdf28f62845a341dca8ef5d6881bf0ca64dc5e5ada1a6b3081f35edbdaf0c9")]
E="implementation/p09/evidence/"
def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        ar=a.read_exact(q,w.AUTHORITY);a.read_exact(q,w.ROOT)
        a.fields(ar,dict(accepted_count_after=151,next_runtime_index=158,resource_cleanup_confirmed=True),"UNCHANGED151")
        a.exact(ar["runtime_candidate_pin"],w.ROOT,"UNCHANGED157")
        for n,final in ((25,0),(26,409)):
            row=q.json(E+f"p09-361-case158-envelope-controller-preflight0{n}.v1.json")
            a.fields(row,dict(state="FAILED_NOT_ACCEPTED",error_code="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME",
                product_worker_or_Native_frame_executed=False,cleanup_confirmed=True,final_fresh_hashes=final),"FAILED_PREFLIGHT_NOT_PRODUCT")
            a.exact(row["resource_samples"][-1]["parent_cpu_machine_percent"],0.0,"ACTUAL_LAST_PARENT_CPU")
        review=q.json(E+"p09-361-case158-metadata-cpu-stop025-026-review-r666.v1.json")
        a.fields(review,dict(state="REVIEWED_METADATA_CPU_WARNINGS_NOT_PRODUCT_OR_CAUSE",
            accepted_count_delta=0,case158_product_started_this_turn=False,
            actual_global_CPU_or_freeze_improvement_proven=False),"REVIEW_NOT_CAUSE_OR_IMPROVEMENT")
        for filename,state in (("p09-361-case158-same-reader-admission-code7-r664.v1.json","PASS_SAME_READER_ADMISSION_CODE7_NOT_CURRENT_RUNTIME"),
            ("p09-361-case158-envelope-controller-code7-r665.v1.json","PASS_CURRENT158_ENVELOPE_CONTROLLER_CODE7_NOT_PRODUCT_OR_GO")):
            code=q.json(E+filename)
            a.fields(code,dict(state=state,contracts=dict(run=7,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"NEW_CODE7")
            for p in code["new_code_pins"]+code.get("source_pins",[]):a.exact(q.pin(p["path"]),p,"CURRENT_QUALIFIED_CODE")
        data=q.json(E+"p09-361-case158-envelope-controller-data025.v1.json")
        a.fields(data,dict(index=158,before=151,run=1),"LATEST_DATA")
        for p in [data["qualification_pin"]]+data["controller_code_pins"]:a.exact(q.pin(p["path"]),p,"LATEST_DATA_PIN")
        for path in SOURCES:
            p=q.pin(path);target=E+"p361-r330-qualified/"+path
            a.exact(q.pin(target),dict(p,path=target),"SOURCE_ARCHIVE_EXACT")
        docs=[]
        for old in DOCS:
            p,raw=q._read(old["path"],parse=True);q._bind(p["path"],p);b=bytes(raw);suffix=ADD.encode("utf-8")
            a.require(b.endswith(suffix),"EXACT_CURRENT_APPEND")
            a.exact(dict(bytes=len(b)-len(suffix),sha256=hashlib.sha256(b[:-len(suffix)]).hexdigest()),
                {k:old[k] for k in ("bytes","sha256")},"WHOLE_PREVIOUS_DOCUMENT_BYTES")
            docs.append(p)
        q.pin("implementation/p09/P09-361_CASE158_ADMISSION_R330.md");q.finish();g.check(force=True)
        out.update(state="PASS_R330_AUTHORITY151_SAME_READER_ADMISSION_CODE_AND_CPU_STOP_REVIEW_NOT_CURRENT158_OR_GATE",
            goal_status="ACTIVE",accepted_count_after=151,current_queue_remaining=98,next_case=158,
            current_generation_individual_cases=46,case158_product_or_Native_started_this_turn=False,
            whole_current_preflight_and_source_final_fresh_incomplete=True,
            same_reader_admission_and_controller_CODE7_passed=True,
            CPU_or_PC_freeze_cause_or_improvement_proven=False,
            previous_documents_and_authority151_root157_preserved=True,
            source_archives=len(SOURCES),document_pins=docs,fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        out["error_type"]=type(e).__name__
        if isinstance(e,ValueError):
            import re
            msg=str(e);out["error_code"]=msg if re.fullmatch("[A-Za-z0-9_]{1,256}",msg) else "REDACTED_R330_ERROR"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
