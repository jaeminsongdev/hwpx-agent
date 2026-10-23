"""User-authorized OS maintenance for ONE original003 process. Not Native retry, qualification or original-run cleanup."""
import ctypes,hashlib,json,os,sys,time
from ctypes import wintypes as w
from pathlib import Path
ROOT=Path('D:/개발/hwpx-agent')
ORIGINAL='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run003.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-external003-user-authorized-cleanup550.v1.json'
EXPECTED_PID=24780
EXPECTED_BIRTH=134370773797187988
IMAGE=Path('C:/Program Files (x86)/HNC/Office 2020/HOffice110/bin/hwp.exe')
def require(value,code):
    if not value:raise ValueError('P550_'+code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    require(os.name=='nt'and Path.cwd().resolve()==ROOT.resolve()and sys.argv[1:]==['--close-original003-owned-background-only'],'EXACT_MAINTENANCE_SCOPE')
    output=ROOT/OUTPUT;require(not output.exists()and not output.is_symlink(),'IMMUTABLE_MAINTENANCE_RESULT')
    record=dict(state='FAILED_EXTERNAL003_USER_AUTHORIZED_MAINTENANCE',process_id=EXPECTED_PID,expected_birth_100ns=EXPECTED_BIRTH,
        original_run=ORIGINAL,user_authorized_Hancom_cleanup_until_user_reports_use=True,
        new_Native_session_or_document_actions=False,original_run_cleanup_false_or_failure_rewritten=False,
        original_001_002_003_or_Native_replayed=False,normal_GUI_close_available=False,
        termination_attempted=False,exact_held_process_exit_confirmed=False)
    process=None;k=ctypes.WinDLL('kernel32',use_last_error=True);started=time.monotonic()
    k.OpenProcess.argtypes,k.OpenProcess.restype=[w.DWORD,w.BOOL,w.DWORD],w.HANDLE
    k.CloseHandle.argtypes,k.CloseHandle.restype=[w.HANDLE],w.BOOL
    k.WaitForSingleObject.argtypes,k.WaitForSingleObject.restype=[w.HANDLE,w.DWORD],w.DWORD
    k.QueryFullProcessImageNameW.argtypes,k.QueryFullProcessImageNameW.restype=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)],w.BOOL
    k.GetProcessTimes.argtypes,k.GetProcessTimes.restype=[w.HANDLE,*([ctypes.POINTER(w.FILETIME)]*4)],w.BOOL
    k.ProcessIdToSessionId.argtypes,k.ProcessIdToSessionId.restype=[w.DWORD,ctypes.POINTER(w.DWORD)],w.BOOL
    k.GetCurrentProcessId.restype=w.DWORD
    k.TerminateProcess.argtypes,k.TerminateProcess.restype=[w.HANDLE,w.UINT],w.BOOL
    k.GetExitCodeProcess.argtypes,k.GetExitCodeProcess.restype=[w.HANDLE,ctypes.POINTER(w.DWORD)],w.BOOL
    try:
        source=ROOT/ORIGINAL;require(source.stat().st_size==125769 and sha(source)=='901374892ce5c40986b3de473a139bf4d3579b68738419bd284f95e63a8c047a','EXACT_ORIGINAL_FAILED_RECEIPT')
        p=json.loads(json.loads(source.read_text(encoding='utf8'))['payload_json']);native=p['qualification_worker']['handler_summary']['native_backend_profile']
        require(p['state']=='FAILED_EXTERNAL_QUALIFIED_ENTRY'and p['cleanup']is False and p['fixed_eight_executed']is False
            and native['owner_bound']is False and native['process_id']==EXPECTED_PID and native['process_birth_100ns']==EXPECTED_BIRTH,'ORIGINAL_FAILED_BEFORE_DOCUMENTS_EXACT_OWNED_IDENTITY')
        require(IMAGE.is_file()and not IMAGE.is_symlink()and IMAGE.stat().st_size==2321432
            and sha(IMAGE)=='7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce','CURRENT_EXPECTED_INSTALLED_IMAGE')
        process=k.OpenProcess(0x00100000|0x1000|0x0001,False,EXPECTED_PID)
        require(bool(process),'OPEN_EXACT_QUERY_SYNC_TERMINATE_HANDLE_NO_BROAD_PROCESS_SELECTION')
        times=[w.FILETIME()for _ in range(4)];require(k.GetProcessTimes(process,*[ctypes.byref(t)for t in times]),'READ_HELD_PROCESS_TIMES')
        birth=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime;require(birth==EXPECTED_BIRTH,'HELD_PROCESS_BIRTH_NOT_REUSED_PID')
        image=ctypes.create_unicode_buffer(32768);size=w.DWORD(len(image));require(k.QueryFullProcessImageNameW(process,0,image,ctypes.byref(size)),'READ_HELD_IMAGE')
        require(Path(image.value).resolve()==IMAGE.resolve(),'HELD_PROCESS_EXACT_IMAGE_PATH')
        session=w.DWORD();ours=w.DWORD();require(k.ProcessIdToSessionId(EXPECTED_PID,ctypes.byref(session))and k.ProcessIdToSessionId(k.GetCurrentProcessId(),ctypes.byref(ours)),'READ_CURRENT_AND_TARGET_SESSION')
        require(session.value==native['session_id']==ours.value,'SAME_ORIGINAL_AND_CURRENT_SESSION')
        status=k.WaitForSingleObject(process,0);require(status in(0,258),'HELD_PROCESS_LIVENESS_QUERY')
        record.update(process_birth_verified=True,installed_image_verified=True,same_session_verified=True,original_claim_owned_process_only=True)
        if status==258:
            record['termination_attempted']=True
            require(k.TerminateProcess(process,0xC0DE0003),'TERMINATE_USER_AUTHORIZED_EXACT_HELD_PROCESS')
            require(k.WaitForSingleObject(process,5000)==0,'SAME_HELD_PROCESS_EXIT_WITHIN_BOUND')
        exit_code=w.DWORD();require(k.GetExitCodeProcess(process,ctypes.byref(exit_code))and exit_code.value!=259,'EXACT_PROCESS_TERMINAL')
        record.update(exact_held_process_exit_confirmed=True,exit_code=exit_code.value)
        require(sha(source)=='901374892ce5c40986b3de473a139bf4d3579b68738419bd284f95e63a8c047a','ORIGINAL_FAILURE_AND_CLEANUP_FALSE_BYTES_UNCHANGED')
        record['state']='PASS_USER_AUTHORIZED_EXACT_ORPHAN_PROCESS_EXIT_NOT_ORIGINAL_RUN_CLEANUP_OR_NATIVE_QUALIFICATION'
    except(ValueError,OSError,KeyError,TypeError)as error:
        code=error.args[0]if error.args else None;record.update(error_type=type(error).__name__,error_code=code if type(code)is str and code.startswith('P550_')else'P550_FAILURE_NO_RAW_VALUES')
    finally:
        record['query_terminate_handle_closed']=process is None or bool(k.CloseHandle(process));record['elapsed_seconds']=round(time.monotonic()-started,3)
        payload=(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n').encode();require(len(payload)<=16384,'BOUNDED_MAINTENANCE_RECEIPT')
        with output.open('xb')as f:f.write(payload);f.flush();os.fsync(f.fileno())
        print(json.dumps(record,ensure_ascii=False),flush=True)
    return 0 if record['state'].startswith('PASS_')and record['query_terminate_handle_closed']else 2
if __name__=='__main__':raise SystemExit(main())
