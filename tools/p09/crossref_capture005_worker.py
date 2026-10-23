"""Fixed005 worker composition; unchanged original one-core/non-killing lifecycle, no CLI."""
import json,sys
import crossref_fixed_worker as original
import crossref_capture005_namespace as namespace

TARGET='implementation/p09/tools/run-crossref-capture005-worker.ps1'
PROGRAM='implementation/p09/tools/crossref-capture005-worker-program.ps1'
PROFILE='implementation/p09/tools/crossref-capture005-namespace.ps1'
SOURCES=original.SOURCES+(TARGET,PROGRAM,PROFILE,namespace.PROBE)
PROBE_PIN=(5150720,'9c07898c40bb95ce1ed60b42d10481152bda8aaf7bb68e9c453fffef736756d9')

def command(reader):
    p=original.prior
    p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'CAPTURE005_FIXED_SOURCE_ROOT')
    for path in SOURCES:reader.pin(path)
    p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'CAPTURE005_ORIGINAL_FIXED_BOOTSTRAP')
    pin=reader.snapshots[namespace.PROBE]
    p.require((pin['bytes'],pin['sha256'])==PROBE_PIN,'CAPTURE005_EXACT_COMPILED_READONLY_PROBE')
    args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(p.original.c.ROOT/TARGET),'-FixedEightAfterSession']
    return [sys.executable,'-B',str(p.original.c.ROOT/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

class Fixed005Worker(original.FixedWorker):
    def _fixed_command(self,reader):return command(reader)
