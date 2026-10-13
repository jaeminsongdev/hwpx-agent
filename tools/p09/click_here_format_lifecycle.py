"""Fixed P55 field lifecycle inputs and independent complete ZIP comparison, no COM."""
import io
import json
import zipfile
from tools.p09 import verify_click_here_format_preservation as previous

m, ROOT = previous.m, previous.ROOT
require, sha, canonical = previous.require, previous.sha, previous.canonical
HARNESS = 'implementation/p09/tools/run-hancom-2020-click-here-format-preservation.ps1'
LIBRARY = 'implementation/p09/tools/click-here-format-lifecycle.ps1'
INSPECTOR = 'tools/p09/inspect_click_here_lifecycle_typelib.ps1'
PLANS = 'implementation/p09/evidence/private/p09-55-click-format-plans-20261003-r01'
DIRECT = 'fixtures/target-build/p09-22-click-here-update-target-20261002-02/output'
MANIFEST_SHA = 'd61d28d10aff3e9b7ee4e73a397ba0e96e97630737ff9718862b6ddb12387876'
P54_SHA = 'c300baf9ccbd79084a6ab8f841cf1c2dde6bc7982ee18b50e3f4205a9aa16b36'


def preserved():
    raw = m.prior.candidate.bounded(ROOT/previous.CAPSULE)
    require(sha(raw) == P54_SHA, 'p55_original_source_receipt')
    receipt = json.loads(raw, object_pairs_hook=m.prior.candidate.prior.io.duplicate_guard)
    require(previous.pins() == receipt['source_sha256'] and previous.preservation() == receipt['preservation'],
        'p55_original_source_graph')
    require(m.public_inventory(m.original_plans()) == receipt['original_complete_two_case_public_inventory'],
        'p55_original_source_plans')
    return {'p54_source_receipt_sha256': P54_SHA, 'p54_six_source_sha256': receipt['source_sha256'],
        'complete_original_identity_graph_sha256': sha(canonical(receipt['preservation'])),
        'historical_native_files_exact': 75, 'predecessor_workflows_reexecuted': False}


def original_inputs():
    manifest, direct = m.original.prepare(ROOT/DIRECT/'fixture-manifest.json', MANIFEST_SHA)
    plans = m.original_plans()
    rows = []
    for index, ((_, source), plan) in enumerate(zip(m.original.CASES.items(), plans), 1):
        original_row = manifest['cases'][index-1]
        rows.append({'case_id': f'P09-55-C{index:02}', 'worker_plan_case_id': plan['case_id'],
            'source_file': m.original.DISCOVERY+'/'+source[0], 'source_package_sha256': source[1],
            'plan_file': f'p09-55-c{index:02}-plan.json', 'plan_sha256': sha(canonical(plan)),
            'plan_bytes': len(canonical(plan)), 'sdk_expected_file': DIRECT+'/'+source[2],
            'sdk_expected_package_sha256': original_row['output_package_sha256'],
            'sdk_expected_section_sha256': direct[original_row['case_id']][1]['section_sha256'],
            'run_directory': 'implementation/p09/evidence/private/'+
                f'p09-55-click-format-20261003-r01-c{index:02}-attempt01', 'native_runtime_qualified': False})
    return rows, plans


def bundle_manifest(rows):
    return {'schema_version': 'hwpx-agent.click-here-format-lifecycle-plan-bundle/v1', 'cases': rows,
        'native_dispatch_or_runtime_qualified': False, 'p09_complete': False}


def prepare_bundle():
    rows, plans = original_inputs()
    directory = ROOT/PLANS
    m.prior.environment.q.shared.within(directory.parent, ROOT/'implementation/p09/evidence/private')
    require(not directory.exists(), 'p55_exclusive_plan_directory_exists')
    # Generated disposable plans only. Original captures/direct SDK packages remain read-only.
    directory.mkdir()
    for row, plan in zip(rows, plans):
        with (directory/row['plan_file']).open('xb') as stream:
            stream.write(canonical(plan))
    with (directory/'fixture-manifest.json').open('xb') as stream:
        stream.write(canonical(bundle_manifest(rows)))
    return inspect_bundle()


def inspect_bundle():
    rows, plans = original_inputs()
    directory = ROOT/PLANS
    m.prior.environment.q.shared.within(directory, ROOT/'implementation/p09/evidence/private')
    expected = {row['plan_file']: canonical(plan) for row, plan in zip(rows, plans)}
    expected['fixture-manifest.json'] = canonical(bundle_manifest(rows))
    require(set(p.name for p in directory.iterdir()) == set(expected), 'p55_plan_bundle_inventory')
    for name, raw in expected.items():
        require(m.prior.candidate.bounded(directory/name) == raw, 'p55_plan_bundle_bytes')
    return {'files': {name: {'sha256': sha(raw), 'bytes': len(raw)} for name, raw in expected.items()},
        'case_count': 2, 'native_runtime_qualified': False, 'raw_document_values_present': False}


def parts(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 4194304, 'p55_package_boundary')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        names = [i.filename for i in entries]
        require(0 < len(entries) <= 512 and len(names) == len(set(names)) and
            sum(i.file_size for i in entries) <= 16777216 and all(i.file_size <= 2097152
                and not i.flag_bits & 1 and i.compress_type in (0,8)
                and (i.external_attr >> 16) & 0o170000 not in (0o120000,0o040000)
                and not i.filename.startswith(('/', '\\')) and ':' not in i.filename
                and '\\' not in i.filename and all(p not in ('','..','.') for p in i.filename.split('/'))
                for i in entries), 'p55_zip_boundary')
        return {i.filename: archive.read(i) for i in entries}


def compare_saved_package(case_id, actual):
    rows, _ = original_inputs()
    matches = [r for r in rows if r['case_id'] == case_id]
    require(len(matches) == 1, 'p55_package_case_scope')
    row = matches[0]
    expected = m.prior.candidate.bounded(ROOT/row['sdk_expected_file'])
    require(sha(expected) == row['sdk_expected_package_sha256'], 'p55_sdk_package_changed')
    target, source = parts(actual), parts(expected)
    changed = {n for n in source.keys() & target.keys() if source[n] != target[n]}
    missing, extra = source.keys()-target.keys(), target.keys()-source.keys()
    native_exact = False
    try:
        m.xml(target['Contents/section0.xml']); m.xml(target['Contents/header.xml'])
        native_exact = m.original.native(target['Contents/section0.xml'], target['Contents/header.xml']) == \
            m.original.native(source['Contents/section0.xml'], source['Contents/header.xml'])
    except (ValueError, KeyError, m.ET.ParseError):
        pass
    exact = not changed and not missing and not extra
    return {'case_id': case_id, 'state': 'exact_sdk_expanded_package_contract' if exact else 'rejected_whole_package_differs',
        'package_sha256': sha(actual), 'package_bytes': len(actual), 'expanded_parts': len(target),
        'whole_expanded_bytes_exact': exact, 'expanded_inventory_exact': not missing and not extra,
        'changed_parts_count': len(changed), 'missing_parts_count': len(missing), 'extra_parts_count': len(extra),
        'complete_click_here_observed_section_state_exact': native_exact,
        'archive_recompression_only': exact and actual != expected, 'raw_document_values_or_entry_names_present': False,
        'native_runtime_rollback_or_render_differential_qualified': False, 'p09_complete': False}


def preflight_command(row, *, plan_sha=None, harness_sha=None):
    require(row in original_inputs()[0], 'p55_exact_case_row')
    return [m.prior.environment.SHELL, '-NoLogo', '-NoProfile', '-NonInteractive', '-STA', '-File', str(ROOT/HARNESS),
        '-CaseId', row['case_id'], '-ExpectedPlanSha256', row['plan_sha256'] if plan_sha is None else plan_sha,
        '-ExpectedLifecycleLibrarySha256', sha(m.prior.candidate.bounded(ROOT/LIBRARY)),
        '-ExpectedHarnessSha256', sha(m.prior.candidate.bounded(ROOT/HARNESS)) if harness_sha is None else harness_sha,
        '-PreflightOnly']
