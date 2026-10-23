"""Fixed006 worker composition; unchanged original one-core/non-killing lifecycle, no CLI."""
import json,sys
import crossref_fixed_worker as original
import crossref_capture006_namespace as namespace

TARGET='implementation/p09/tools/run-crossref-capture006-worker.ps1'
PROGRAM='implementation/p09/tools/crossref-capture006-worker-program.ps1'
PROFILE='implementation/p09/tools/crossref-capture006-namespace.ps1'
SOURCES=original.SOURCES+(TARGET,PROGRAM,PROFILE,'implementation/p09/tools/crossref-capture006-source-guard.ps1',namespace.PROBE)
PROBE_PIN=(5150720,'c0328953ea359536b5f8ed3de888393d842118600889ef42c233646ecff807ae')

def command(reader):
    p=original.prior
    p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'CAPTURE006_FIXED_SOURCE_ROOT')
    for path in SOURCES:reader.pin(path)
    p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'CAPTURE006_ORIGINAL_FIXED_BOOTSTRAP')
    pin=reader.snapshots[namespace.PROBE]
    p.require((pin['bytes'],pin['sha256'])==PROBE_PIN,'CAPTURE006_EXACT_COMPILED_READONLY_PROBE')
    args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(p.original.c.ROOT/TARGET),'-FixedEightAfterSession']
    return [sys.executable,'-B',str(p.original.c.ROOT/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

class Fixed006Worker(original.FixedWorker):
    def _fixed_command(self,reader):return command(reader)
