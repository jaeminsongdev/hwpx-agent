"""Fixed008 worker composition; unchanged original one-core/non-killing lifecycle, no CLI."""
import json,sys
import crossref_fixed_worker as original
import crossref_capture008_namespace as namespace

TARGET='implementation/p09/tools/run-crossref-capture008-worker.ps1'
PROGRAM='implementation/p09/tools/crossref-capture008-worker-program.ps1'
PROFILE='implementation/p09/tools/crossref-capture008-namespace.ps1'
SOURCES=original.SOURCES+(TARGET,PROGRAM,PROFILE,'implementation/p09/tools/crossref-capture008-source-guard.ps1','implementation/p09/tools/crossref-capture008-application-binding.ps1',namespace.PROBE)
PROBE_PIN=(5151744,'f63c2a3559cc853f8076258cd2ece0b28a2178234f1bf4980209a9705be70592')

def command(reader):
    p=original.prior
    p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'CAPTURE008_FIXED_SOURCE_ROOT')
    for path in SOURCES:reader.pin(path)
    p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'CAPTURE008_ORIGINAL_FIXED_BOOTSTRAP')
    pin=reader.snapshots[namespace.PROBE]
    p.require((pin['bytes'],pin['sha256'])==PROBE_PIN,'CAPTURE008_EXACT_COMPILED_READONLY_PROBE')
    args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(p.original.c.ROOT/TARGET),'-FixedEightAfterSession']
    return [sys.executable,'-B',str(p.original.c.ROOT/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

class Fixed008Worker(original.FixedWorker):
    def _fixed_command(self,reader):return command(reader)
