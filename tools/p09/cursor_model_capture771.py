"""Record bounded model process outcome before JSON parsing; no raw output export."""
import hashlib,json,subprocess,time
import named_style_verification_runtime as r

def command(guard,args,env,row,label):
    owned=capture=None;start=time.monotonic();step=dict(stage=label,cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[args[0]],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-start<90,'CURSOR771_MODEL_COMMAND_TIMEOUT')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        try:value=json.loads(out)
        except json.JSONDecodeError as error:
            step['output_decode_error']=dict(kind='JSONDecodeError',line=error.lineno,column=error.colno)
            raise ValueError('CURSOR771_MODEL_STDOUT_INVALID_JSON')from None
        step['result']=value
        r.c.require(owned.returncode==0 and not err,'CURSOR771_MODEL_COMMAND_FAILED')
        return value
    finally:
        if owned is not None:
            # Fixed code-model processes only; this never owns a Native session.
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
