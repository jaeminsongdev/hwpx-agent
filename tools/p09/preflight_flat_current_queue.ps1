param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(116, 249)]
    [int] $Case
)

$ErrorActionPreference = 'Stop'
$p09PreflightRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
Set-Location -LiteralPath $p09PreflightRoot

# 이 스크립트는 제품/Native 실행이나 수용 기록을 쓰지 않는다.
# 원 Guard/읽기 제한을 유지하고, 실패한 단계와 기존 자원 표본의 집계만 반환한다.
# Python -c로 실행하므로 이 진단용 PowerShell 파일은 제품의 Python import closure가 아니다.
$p09PreflightCode = @'
import json
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, 'tools/p09')
import flat_current_queue_runtime as r
import flat_current_queue_acceptance as m

a = m.a
g = None
q = None
stage = 'configuration'
error = None
out = {}
started = time.monotonic()
try:
    a.require(Path.cwd().resolve() == r.c.ROOT.resolve(), 'EXACT_REPOSITORY_ROOT')
    a.require(len(sys.argv) == 2, 'ONE_PREFLIGHT_CASE')
    step = r.configure(int(sys.argv[1]))
    stage = 'admission'
    g = a.Guard()
    g.acquire()
    q = a.AcceptanceReader(r.c.ROOT, g.check)
    stage = 'prior_authority_full_candidate_and_inherited_bootstrap'
    required, rust = r.binding_attempt(q, 1)
    before = set(sys.modules)
    entry, proof = r.entry()
    engine, inner = r.template()
    a.require(before == set(sys.modules), 'NO_NEW_CASE_CONTROLLER_IMPORT')
    api = engine.run_owned.__globals__
    terminal = engine.terminal_api(q)
    stage = 'exact_original_runtime_closure'
    for key in ('FAILED_FIRST_PIN', 'FAILED_STOP_PIN'):
        a.read_exact(q, api[key])
    for directory, name, size, digest in api['FAILED_PREIMAGES']:
        path = 'implementation/p09/evidence/' + directory + '/' + name
        a.exact(q.pin(path), dict(path=path, bytes=size, sha256=digest), 'PRESERVED_FAILED_PREIMAGE')
    names = {r.SELF, r.TEST, r.native.SELF, r.native.TEST, r.scope.SELF, r.scope.TEST}
    for module in tuple(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).absolute()
            if path.is_relative_to(r.c.ROOT / 'tools/p09') and path.suffix == '.py':
                names.add(path.relative_to(r.c.ROOT).as_posix())
    a.require(len(names) <= 64, 'ORIGINAL_HELPER_BOUND')
    for name in sorted(names):
        q.pin(name)
    for pin in r.native.SOURCES:
        a.exact(q.pin(pin['path']), pin, 'NATIVE_DEFINITION_PIN')
    required = r.scope.extend(required, q.snapshots)
    stage = 'current_Rust787_and_complete_original600_budget'
    p = api['build'].QueryPacer(g.check)
    a.require(api['build'].base.inputs.rust_inputs(r.c.ROOT, p.reserve) == rust, 'WHOLE_CURRENT_RUST')
    model = r.stable.runtime_budget(required, p.requests)
    a.exact(r.run_for(r.task_for(1)), 1, 'EXACT_CURRENT_TASK')
    a.exact(api['MARKER_ARGS'], [f'current-queue-case{step.index}-runtime-only'], 'EXACT_CURRENT_MARKER')
    a.require(step.path in required and len(rust) == 787, 'WHOLE_SCOPE_AND_STEP_DATA')
    a.require(model['predicted_runtime_combined_seconds'] < 600, 'ORIGINAL600_COST')
    stage = 'final_fresh_input_reads'
    q.finish()
    time.sleep(.5)
    g.check(force=True)
    out.update(
        state='PASS_FLAT_NEXT_CASE_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE',
        index=step.index, before=step.before, case=step.case, config_pin=step.pin,
        inputs=len(required), bytes=sum(x['bytes'] for x in required.values()),
        imported_paths=len(names), new_case_module_imports=0,
        current_Rust=len(rust), Rust_inventory_requests=p.requests,
        complete_runtime_budget=model,
        qualified115_wrapper_AST_undo_exact=proof['original115_wrapper_AST_restored_exactly'],
        original112_engine_AST_undo_exact=inner['original_engine_AST_restored_exactly'],
    )
except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
    candidate = str(exc) if isinstance(exc, ValueError) else type(exc).__name__.upper()
    error = candidate if re.fullmatch('[A-Z0-9_]{1,256}', candidate) else 'REDACTED_PREFLIGHT_FAILURE'
    out.update(state='STOPPED_FLAT_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE')
finally:
    if g is not None:
        try:
            g.close()
        except (ValueError, OSError):
            error = 'ORIGINAL_GUARD_CLEANUP_FAILED'
            out['state'] = 'STOPPED_FLAT_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE'

samples = g.samples if g is not None else []
hot = 0
reasons = []
for row in samples:
    hot, reason = a.c.decision(row, hot)
    if reason and reason not in reasons:
        reasons.append(reason)
parent_cpus = [x['parent_cpu_machine_percent'] for x in samples
               if x.get('parent_cpu_machine_percent') is not None]
tail_keys = ('time_utc', 'system_cpu_percent', 'available_ram_percent',
             'commit_used_percent', 'parent_cpu_machine_percent', 'parent_private_mib')
cleanup = bool(g is not None and g.cleanup)
out.update(
    stage=stage, error_code=error, original_resource_stop_reasons=reasons,
    fresh_inputs=len(q.snapshots) if q else 0,
    fresh_read_passes=q.read_passes if q else 0,
    fresh_bytes_read=q.bytes_read if q else 0,
    final_fresh_hashes=q.final_fresh_hashes if q else 0,
    original_resource_samples=len(samples),
    system_CPU_max_percent=max((x['system_cpu_percent'] for x in samples), default=None),
    available_RAM_min_percent=min((x['available_ram_percent'] for x in samples), default=None),
    commit_max_percent=max((x['commit_used_percent'] for x in samples), default=None),
    parent_CPU_max_machine_percent=max(parent_cpus, default=None),
    parent_private_max_MiB=max((x['parent_private_mib'] for x in samples), default=None),
    original_sample_tail_limit=6,
    original_sample_tail=[{k: x[k] for k in tail_keys} for x in samples[-6:]],
    elapsed_seconds=time.monotonic() - started, cleanup_confirmed=cleanup,
    second_sampler_or_external_profiler=False,
    product_worker_or_Native_frame_executed=False, queue_delta=0,
    CPU_RAM_rates_deadlines_or_input_checks_weakened=False,
    diagnostic_script_is_part_of_product_Python_import_closure=False,
    PC_freeze_resolved=False,
)
print(json.dumps(out))
raise SystemExit(0 if error is None and cleanup else 2)
'@

python -B -c $p09PreflightCode $Case
exit $LASTEXITCODE
