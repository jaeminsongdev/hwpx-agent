"""Fixed010 worker composition; unchanged original one-core/non-killing lifecycle, no CLI."""
import json,sys
import crossref_fixed_worker as original
import crossref_capture010_namespace as namespace

TARGET='implementation/p09/tools/run-crossref-capture010-worker.ps1'
PROGRAM='implementation/p09/tools/crossref-capture010-worker-program.ps1'
PROFILE='implementation/p09/tools/crossref-capture010-namespace.ps1'
SOURCES=original.SOURCES+(TARGET,PROGRAM,PROFILE,'implementation/p09/tools/crossref-capture009-source-guard.ps1','implementation/p09/tools/crossref-capture008-application-binding.ps1','implementation/p09/tools/crossref-capture009-artifact-guard.ps1',namespace.PROBE)
PROBE_PIN=(5152256,'379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c')

def command(reader):
    p=original.prior
    p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'CAPTURE010_FIXED_SOURCE_ROOT')
    for path in SOURCES:reader.pin(path)
    p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'CAPTURE010_ORIGINAL_FIXED_BOOTSTRAP')
    pin=reader.snapshots[namespace.PROBE]
    p.require((pin['bytes'],pin['sha256'])==PROBE_PIN,'CAPTURE010_EXACT_COMPILED_READONLY_PROBE')
    args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(p.original.c.ROOT/TARGET),'-FixedEightAfterSession']
    return [sys.executable,'-B',str(p.original.c.ROOT/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

class Fixed010Worker(original.FixedWorker):
    def _fixed_command(self,reader):return command(reader)

