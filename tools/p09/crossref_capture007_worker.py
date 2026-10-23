"""Fixed007 worker composition; unchanged original one-core/non-killing lifecycle, no CLI."""
import json,sys
import crossref_fixed_worker as original
import crossref_capture007_namespace as namespace

TARGET='implementation/p09/tools/run-crossref-capture007-worker.ps1'
PROGRAM='implementation/p09/tools/crossref-capture007-worker-program.ps1'
PROFILE='implementation/p09/tools/crossref-capture007-namespace.ps1'
SOURCES=original.SOURCES+(TARGET,PROGRAM,PROFILE,'implementation/p09/tools/crossref-capture007-source-guard.ps1','implementation/p09/tools/crossref-capture007-application-binding.ps1',namespace.PROBE)
PROBE_PIN=(5151232,'614077e81603807133782c35679993e78fab96d9953e4a20cec935b61194ee1c')

def command(reader):
    p=original.prior
    p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'CAPTURE007_FIXED_SOURCE_ROOT')
    for path in SOURCES:reader.pin(path)
    p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'CAPTURE007_ORIGINAL_FIXED_BOOTSTRAP')
    pin=reader.snapshots[namespace.PROBE]
    p.require((pin['bytes'],pin['sha256'])==PROBE_PIN,'CAPTURE007_EXACT_COMPILED_READONLY_PROBE')
    args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(p.original.c.ROOT/TARGET),'-FixedEightAfterSession']
    return [sys.executable,'-B',str(p.original.c.ROOT/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

class Fixed007Worker(original.FixedWorker):
    def _fixed_command(self,reader):return command(reader)
