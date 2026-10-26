"""Code-only guarded result capture; retain exit/safe error before decoding JSON."""
import hashlib,json,re,subprocess,time
import named_style_verification_runtime as r
def command(guard,args,env,row,label):
    owned=capture=None;begin=time.monotonic();step=dict(stage=label,cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[args[0]],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-begin<90,'XREF_RESULT730_CODE_TIMEOUT')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        if err:
            safe=err.strip();step['safe_error_code']=safe if re.fullmatch(r'P729_[A-Z0-9_]{1,80}',safe)else'XREF_RESULT730_PRODUCT_ERROR_NO_RAW_VALUES'
        if owned.returncode!=0 or err:return None
        result=json.loads(out);step['result']=result;return result
    finally:
        if owned is not None:
            # This Job contains only a fixed readonly Rust reader, never Native.
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
