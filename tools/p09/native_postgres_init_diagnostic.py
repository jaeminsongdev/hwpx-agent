"""One NEW reject-auth initdb only, no password, listener, SQL migration or product execution."""
import ctypes,hashlib,json,os,re,subprocess,sys
from pathlib import Path
import native_postgres_cluster as cluster
from bounded_process_progress import BoundedProcessCapture
ROOT=cluster.ROOT
CLUSTER='target/p09-native-postgres-init-diagnostic-281'
ERROR_TOKENS=('could not open file','could not open directory','could not execute command','could not change permissions',
    'could not create shared memory','could not start process','could not re-execute','could not load library',
    'invalid value for parameter','unrecognized configuration parameter','Permission denied','Access is denied',
    'No such file or directory','The system cannot find','running bootstrap script','creating configuration files','not removed')
def safe_init_error(stderr):
    # This mode never generates a credential. Retain only one sanitized error classification,
    # not full stdout/stderr, quoted paths or arbitrary values from an external process.
    tokens=[t for t in ERROR_TOKENS if t in stderr]
    lines=[line for line in stderr.splitlines()if re.search(r'\b(?:error|FATAL|PANIC):',line)]
    excerpt=''
    if lines:
        # Simple separate quote replacements do not depend on error-message formatting.
        excerpt=re.sub(r'"[^"\r\n]*"','<redacted>',lines[0]);excerpt=re.sub(r"'[^'\r\n]*'",'<redacted>',excerpt)
        excerpt=re.sub(r'[A-Za-z]:[^\s<>]*','<path>',excerpt)
        excerpt=''.join(c if 32<=ord(c)<127 else'?'for c in excerpt)[:180]
    return dict(tokens=tokens,first_error_sanitized=excerpt,windows_error_codes=re.findall(r'(?:error code|Windows error code)\s+([0-9]{1,10})',stderr))
def main():
    cluster.require(sys.argv[1:]==['--new-reject-initdb-only']and os.name=='nt'and Path.cwd().resolve()==ROOT.resolve(),'PG_INIT_DIAGNOSTIC_SCOPE')
    ctypes.WinDLL('kernel32',use_last_error=True).SetErrorMode(0x0001|0x0002|0x8000)
    root=ROOT/CLUSTER;parent=ROOT/'target';cluster.require(not root.exists()and parent.is_dir()and not parent.is_symlink()and not parent.is_junction()
        and root.resolve().is_relative_to(parent.resolve()),'PG_INIT_DIAGNOSTIC_FRESH_OWNED_ROOT')
    manifest=json.loads((ROOT/cluster.MANIFEST).read_text(encoding='utf-8'));cluster.require(cluster.runtime.sha_file(ROOT/cluster.MANIFEST)=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','PG_INIT_DIAGNOSTIC_RUNTIME_MANIFEST')
    for pin in manifest['runtime_pins']:cluster.require(cluster.runtime.sha_file(ROOT/cluster.runtime.ASSET/pin['path'])==pin['sha256'],'PG_INIT_DIAGNOSTIC_FRESH_RUNTIME')
    root.mkdir();binary=ROOT/cluster.runtime.ASSET/'pgsql/bin';data=root/'data'
    # Explicit fresh diagnostic root parameter; no existing data, auth or Job policy is relaxed.
    cluster.CLUSTER=CLUSTER;args=cluster.init_args(binary,data);process=capture=None
    try:
        process=subprocess.Popen(args,cwd=binary,env=cluster.runtime.clean_environment(binary),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        capture=BoundedProcessCapture(process,output_limit=32768,parse_markers=False);out,err=capture.communicate(timeout=60)
        print(json.dumps(dict(state='OBSERVED_NEW_INITDB_RESULT_NOT_DATABASE_QUALIFICATION',database_root=CLUSTER,initdb_exit_code=process.returncode,
            stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),
            diagnostics=safe_init_error(err),progress=[t for t in('selecting dynamic shared memory','selecting default max_connections','selecting default shared_buffers','creating configuration files','running bootstrap script','performing post-bootstrap initialization')if t in out],
            actual_postmaster_or_migration_or_password=False,raw_logs_retained=False)),flush=True)
    finally:
        if process is not None:
            if process.poll()is None:process.kill()
            process.wait(timeout=2)
            if capture is not None:capture.close()
if __name__=='__main__':main()
