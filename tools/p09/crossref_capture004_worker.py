"""Fixed004 worker composition, using unchanged one-percent/non-killing worker lifecycle."""
import json,sys
import crossref_fixed_worker as original
import crossref_capture004_namespace as namespace

TARGET='implementation/p09/tools/run-crossref-capture004-worker.ps1'
PROGRAM='implementation/p09/tools/crossref-capture004-worker-program.ps1'
PROFILE='implementation/p09/tools/crossref-capture004-namespace.ps1'
SOURCES=original.SOURCES+(TARGET,PROGRAM,PROFILE,namespace.PROBE)
PROBE_PIN=(5149696,'e64128bec14686aaecde8bafaf34458b59a4c694fe2b0a54f411d013b0a01551')

def command(reader):
    p=original.prior
    p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'CAPTURE003_FIXED_SOURCE_ROOT')
    for path in SOURCES:reader.pin(path)
    p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'CAPTURE003_ORIGINAL_FIXED_BOOTSTRAP')
    pin=reader.snapshots[namespace.PROBE]
    p.require((pin['bytes'],pin['sha256'])==PROBE_PIN,'CAPTURE003_EXACT_COMPILED_READONLY_PROBE')
    args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(p.original.c.ROOT/TARGET),'-FixedEightAfterSession']
    return [sys.executable,'-B',str(p.original.c.ROOT/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

class Fixed004Worker(original.FixedWorker):
    def _fixed_command(self,reader):return command(reader)
