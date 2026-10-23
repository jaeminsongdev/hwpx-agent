"""Fixed readonly x86 compile/models worker under original owned preparation Job; never Native."""
import hashlib,json,re,subprocess,time
from pathlib import Path
import named_style_verification_runtime as r
SHELL=Path(r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe')
TEST='implementation/p09/tools/test-crossref-existing-owner.ps1'
NAMES={'name_family','name_bound','one_exact_owner','no_owner_no_fallback','duplicate_owners','incomplete_enumeration',
    'pid_mismatch','session_mismatch','birth_one_tick_mismatch','image_mismatch','version_mismatch','window_required',
    'window_changed_after_scan','exact_enum_limit','enum_overflow_not_first_match','get_object_missing','catalog_cleanup_failure',
    'invalid_expected_identity','unknown_names_never_get_objects','lease_close_once','stable_kernel_self_not_hancom'}


def parse_tests(stdout):
    return re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)


def run(guard,env,row):
    c,shared=r.c,r.shared;owned=capture=None;started=last=time.monotonic();step=dict(stage='compiled_x86_ROT_models20_and_actual_kernel_self1',cleanup=False)
    row['steps'].append(step)
    try:
        args=[str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/TEST),'-ModelsAndSelfOnly']
        owned=shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[str(SHELL)],cwd=c.ROOT,checkpoint=guard.check,env=env)
        capture=shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<90,'STOP_ROT_READONLY_TEST_COMMAND_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:
                capture.progress();account=owned.observe()
                if time.monotonic()-last>=15:
                    sample=guard.samples[-1];print(json.dumps(dict(stage=step['stage'],elapsed=round(time.monotonic()-started,1),system_CPU=sample['system_cpu_percent'],
                        available_RAM_percent=sample['available_ram_percent'],job_private_percent=account['peak_job_private_percent'],job_cpu_seconds=account['job_cpu_seconds'])),flush=True);last=time.monotonic()
        step.update(exit_code=owned.returncode,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            tests=parse_tests(stdout),
            safe_error_codes=re.findall(r'(?m)^Error: ((?:P09_XREF_ROT_[A-Z_]{1,120})|CS[0-9]{4})\r?$',stdout+stderr),
            summary_observed='21 passed; 0 failed; 0 ignored; models_and_self_only_not_ROT_or_Native'in stdout)
        c.require(step['exit_code']==0,'ROT_COMPILED_TEST_WORKER_FAILED')
        c.require(len(step['tests'])==21 and {name for name,status in step['tests']}=={'rot_existing::'+name for name in NAMES}
            and all(status=='ok'for name,status in step['tests'])and step['summary_observed']and not step['safe_error_codes'],'EXACT21_COMPILED_MODELS_AND_SELF_CASES_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)
