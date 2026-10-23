"""Fixed009 worker composition; unchanged original one-core/non-killing lifecycle, no CLI."""
import json,sys
import crossref_fixed_worker as original
import crossref_capture009_namespace as namespace

TARGET='implementation/p09/tools/run-crossref-capture009-worker.ps1'
PROGRAM='implementation/p09/tools/crossref-capture009-worker-program.ps1'
PROFILE='implementation/p09/tools/crossref-capture009-namespace.ps1'
SOURCES=original.SOURCES+(TARGET,PROGRAM,PROFILE,'implementation/p09/tools/crossref-capture009-source-guard.ps1','implementation/p09/tools/crossref-capture008-application-binding.ps1','implementation/p09/tools/crossref-capture009-artifact-guard.ps1',namespace.PROBE)
PROBE_PIN=(5152256,'66f39ca7cbddfe075d18738e97d34f49aef77e97265e3256baf7c6883f878f55')

def command(reader):
    p=original.prior
    p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'CAPTURE009_FIXED_SOURCE_ROOT')
    for path in SOURCES:reader.pin(path)
    p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'CAPTURE009_ORIGINAL_FIXED_BOOTSTRAP')
    pin=reader.snapshots[namespace.PROBE]
    p.require((pin['bytes'],pin['sha256'])==PROBE_PIN,'CAPTURE009_EXACT_COMPILED_READONLY_PROBE')
    args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(p.original.c.ROOT/TARGET),'-FixedEightAfterSession']
    return [sys.executable,'-B',str(p.original.c.ROOT/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

class Fixed009Worker(original.FixedWorker):
    def _fixed_command(self,reader):return command(reader)
