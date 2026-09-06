#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from collections import Counter
import csv
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
errors: list[str] = []
p00_source_locks_checked = 0
p00_target_profiles_checked = 0
declared_local_evidence_links = 0
EXCLUDED_TREE_PARTS = {
    '.git',
    '__pycache__',
    'artifacts',
    'bin',
    'dist',
    'evidence',
    'licensed-private',
    'node_modules',
    'obj',
    'source-archive',
    'target',
    'target-build',
    'tmp',
}


def source_paths(pattern: str):
    for path in ROOT.rglob(pattern):
        relative = path.relative_to(ROOT)
        if not any(part in EXCLUDED_TREE_PARTS for part in relative.parts):
            yield path

try:
    import yaml
except ImportError:
    yaml = None
try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None
    FormatChecker = None

if yaml is None:
    errors.append('required dependency missing: PyYAML')
if Draft202012Validator is None:
    errors.append('required dependency missing: jsonschema')

gitignore = (ROOT / '.gitignore').read_text(encoding='utf-8')
for required_private_rule in (
    '/implementation/p00/evidence/',
    '/implementation/p01/evidence/',
    '/implementation/p02/evidence/',
):
    if required_private_rule not in gitignore:
        errors.append(f'private evidence ignore rule missing: {required_private_rule}')

# 1. Syntax parsing.
for path in source_paths('*.json'):
    try:
        json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'JSON {path.relative_to(ROOT)}: {exc}')
if yaml is not None:
    for path in [*source_paths('*.yaml'), *source_paths('*.yml')]:
        try:
            yaml.safe_load(path.read_text(encoding='utf-8'))
        except Exception as exc:
            errors.append(f'YAML {path.relative_to(ROOT)}: {exc}')

# 2. Canonical feature matrix and generated contracts.
rows_csv = list(csv.DictReader((ROOT / 'FEATURE_COVERAGE_MATRIX.csv').open(encoding='utf-8-sig')))
rows_json = json.loads((ROOT / 'specs/feature-coverage-matrix.json').read_text(encoding='utf-8'))
registry = json.loads((ROOT / 'specs/capability-contracts.generated.json').read_text(encoding='utf-8'))
canonical_capability_ids = {r['capability_id'] for r in rows_csv}
if rows_csv != rows_json:
    errors.append('feature CSV and JSON differ')
if registry.get('count') != len(rows_csv) or len(registry.get('contracts', [])) != len(rows_csv):
    errors.append('capability contract count differs from feature matrix')
if [r['feature_id'] for r in rows_csv] != [c['feature_id'] for c in registry['contracts']]:
    errors.append('capability contract order/IDs differ from feature matrix')
for key in ('feature_id', 'capability_id'):
    duplicates = [k for k, v in Counter(r[key] for r in rows_csv).items() if v > 1]
    if duplicates:
        errors.append(f'duplicate {key}: {duplicates[:10]}')

# 3. WBS and phase documents.
wbs = list(csv.DictReader((ROOT / 'WORK_BREAKDOWN_STRUCTURE.csv').open(encoding='utf-8-sig')))
wbs_json = json.loads((ROOT / 'specs/work-breakdown-structure.json').read_text(encoding='utf-8'))
if wbs_json.get('count') != len(wbs) or wbs_json.get('tasks') != wbs:
    errors.append('WBS CSV and JSON differ')
if len({r['task_id'] for r in wbs}) != len(wbs):
    errors.append('duplicate WBS task_id')
expected_phases = [f'P{i:02d}' for i in range(21)]
actual_phases = sorted({r['phase'] for r in wbs})
if actual_phases != expected_phases:
    errors.append(f'WBS phases differ: {actual_phases}')
phase_docs = sorted((ROOT / 'docs/09_roadmap').glob('P??_*.md'))
phase_doc_ids = sorted(path.name[:3] for path in phase_docs)
if phase_doc_ids != expected_phases:
    errors.append(f'phase documents differ: {phase_doc_ids}')

wbs_task_ids = {r['task_id'] for r in wbs}
for row in wbs:
    dependencies = [
        d.strip()
        for d in row['dependencies'].split(',')
        if d.strip() and d.strip().lower() not in {'none', '없음'}
    ]
    unknown_dependencies = [d for d in dependencies if d not in wbs_task_ids and d not in expected_phases]
    if unknown_dependencies:
        errors.append(f"{row['task_id']} has unknown dependencies: {unknown_dependencies}")
    if row['task_id'] in dependencies:
        errors.append(f"{row['task_id']} depends on itself")
    if row['parallelizable'] == 'yes':
        expected_dependency = [f"{row['phase']}-01"]
        if dependencies != expected_dependency:
            errors.append(f"{row['task_id']} parallel dependency differs: {dependencies}")

for phase in expected_phases:
    phase_rows = [r for r in wbs if r['phase'] == phase]
    if not phase_rows:
        continue
    last = phase_rows[-1]
    expected_last_dependencies = [r['task_id'] for r in phase_rows[:-1]]
    actual_last_dependencies = [d.strip() for d in last['dependencies'].split(',') if d.strip()]
    if last['parallelizable'] != 'no' or actual_last_dependencies != expected_last_dependencies:
        errors.append(f"{last['task_id']} does not join all prior phase tasks")

# 4. Canonical semantic references and enum vocabularies.
migration_registry = json.loads((ROOT / 'specs/capability-id-migrations.v1.json').read_text(encoding='utf-8'))
legacy_ids: set[str] = set()
for migration in migration_registry.get('migrations', []):
    legacy_id = migration['legacy_id']
    if legacy_id in legacy_ids:
        errors.append(f'duplicate capability migration: {legacy_id}')
    legacy_ids.add(legacy_id)
    if legacy_id in canonical_capability_ids:
        errors.append(f'migration source is already canonical: {legacy_id}')
    unknown_targets = [target for target in migration['canonical_ids'] if target not in canonical_capability_ids]
    if unknown_targets:
        errors.append(f'{legacy_id} has unknown migration targets: {unknown_targets}')

for path in (ROOT / 'specs/examples').rglob('*.json'):
    obj = json.loads(path.read_text(encoding='utf-8'))
    if obj.get('schema_version') != 'hwpx-agent.operation-plan/v2':
        continue
    for operation in obj.get('operations', []):
        capability_id = operation.get('capability_id')
        if capability_id not in canonical_capability_ids:
            errors.append(f'{path.relative_to(ROOT)} references non-canonical capability: {capability_id}')

for path in (ROOT / 'docs').rglob('*.md'):
    text = path.read_text(encoding='utf-8')
    for legacy_id in legacy_ids:
        if legacy_id in text:
            errors.append(f'{path.relative_to(ROOT)} contains legacy capability: {legacy_id}')

registry_schema = json.loads((ROOT / 'specs/capability-registry.schema.json').read_text(encoding='utf-8'))
contract_schema = json.loads((ROOT / 'specs/capability-contract-v1.schema.json').read_text(encoding='utf-8'))
expected_risk = ['low', 'medium', 'high', 'critical']
registry_risk = registry_schema['$defs']['capability']['properties']['risk']['enum']
contract_risk = contract_schema['properties']['risk']['enum']
if registry_risk != expected_risk or contract_risk != expected_risk:
    errors.append(f'risk enum drift: registry={registry_risk}, contract={contract_risk}')

validation_schema = json.loads((ROOT / 'specs/validation-report.schema.json').read_text(encoding='utf-8'))
check_state = validation_schema['properties']['checks']['items']['properties']['state']['enum']
expected_check_state = ['pass', 'fail', 'unverified', 'skipped_by_policy']
if check_state != expected_check_state:
    errors.append(f'validation check state drift: {check_state}')

# 5. JSON Schema conformance.
if Draft202012Validator is not None:
    format_checker = FormatChecker()
    schema_paths = sorted((ROOT / 'specs').glob('*.schema.json'))
    for path in schema_paths:
        schema = json.loads(path.read_text(encoding='utf-8'))
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f'invalid JSON Schema {path.relative_to(ROOT)}: {exc}')

    feature_schema = json.loads((ROOT / 'specs/feature-row.schema.json').read_text(encoding='utf-8'))
    fv = Draft202012Validator(feature_schema, format_checker=format_checker)
    for idx, row in enumerate(rows_json):
        for err in fv.iter_errors(row):
            errors.append(f'feature[{idx}]: {err.message}')

    contract_schema = json.loads((ROOT / 'specs/capability-contract-v1.schema.json').read_text(encoding='utf-8'))
    cv = Draft202012Validator(contract_schema, format_checker=format_checker)
    for idx, contract in enumerate(registry['contracts']):
        for err in cv.iter_errors(contract):
            errors.append(f'contract[{idx}]: {err.message}')

    op_schema = json.loads((ROOT / 'specs/operation-plan-v2.schema.json').read_text(encoding='utf-8'))
    ov = Draft202012Validator(op_schema, format_checker=format_checker)
    for path in (ROOT / 'specs/examples').rglob('*.json'):
        obj = json.loads(path.read_text(encoding='utf-8'))
        if obj.get('schema_version') == 'hwpx-agent.operation-plan/v2':
            for err in ov.iter_errors(obj):
                errors.append(f'{path.relative_to(ROOT)} {list(err.path)}: {err.message}')

    source_lock_schema = json.loads((ROOT / 'specs/source-lock.schema.json').read_text(encoding='utf-8'))
    source_lock_validator = Draft202012Validator(source_lock_schema, format_checker=format_checker)
    for path in sorted((ROOT / 'implementation/p00').glob('source-lock*.json')):
        obj = json.loads(path.read_text(encoding='utf-8'))
        p00_source_locks_checked += 1
        for err in source_lock_validator.iter_errors(obj):
            errors.append(f'{path.relative_to(ROOT)} {list(err.path)}: {err.message}')
        duplicate_source_ids = [
            source_id
            for source_id, count in Counter(s['source_id'] for s in obj.get('sources', [])).items()
            if count > 1
        ]
        if duplicate_source_ids:
            errors.append(f'{path.relative_to(ROOT)} duplicate source_id: {duplicate_source_ids}')

    if yaml is not None:
        target_profile_schema = json.loads((ROOT / 'specs/target-profile.schema.json').read_text(encoding='utf-8'))
        target_profile_validator = Draft202012Validator(target_profile_schema, format_checker=format_checker)
        for path in sorted((ROOT / 'implementation/p00').glob('target-profile*.yaml')):
            obj = yaml.safe_load(path.read_text(encoding='utf-8'))
            p00_target_profiles_checked += 1
            for err in target_profile_validator.iter_errors(obj):
                errors.append(f'{path.relative_to(ROOT)} {list(err.path)}: {err.message}')

# 6. Skills and Markdown structure.
root_skills = sorted(ROOT.glob('skills/*/SKILL.md'))
for path in root_skills:
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n') or '\nname:' not in text or '\ndescription:' not in text:
        errors.append(f'invalid skill frontmatter: {path.relative_to(ROOT)}')
for path in source_paths('*.md'):
    text = path.read_text(encoding='utf-8')
    if text.count('```') % 2:
        errors.append(f'unbalanced code fence: {path.relative_to(ROOT)}')

# 7. Generated human-readable capability contracts.
contract_md = sorted((ROOT / 'docs/04_feature_catalog/contracts').glob('*_contracts.md'))
heading_pattern = re.compile(r'^##\s+(?:Feature|기능)\s+', re.MULTILINE)
heading_count = sum(len(heading_pattern.findall(p.read_text(encoding='utf-8'))) for p in contract_md)
# Generated files use "## <feature_id> — ...". Fall back to stable feature-id counting.
if heading_count == 0:
    feature_id_pattern = re.compile(r'^##\s+[A-Z]+-\d{3}\b', re.MULTILINE)
    heading_count = sum(len(feature_id_pattern.findall(p.read_text(encoding='utf-8'))) for p in contract_md)
if heading_count != len(rows_csv):
    errors.append(f'capability contract markdown headings={heading_count}, expected={len(rows_csv)}')

# 8. Plugin blueprints: manifest references and package shape.
plugin_roots = [
    ROOT / 'specs/examples/plugin-universal',
    ROOT / 'specs/examples/plugin-codex-remote',
    ROOT / 'specs/examples/plugin-codex-local',
]
for plugin_root in plugin_roots:
    manifest_path = plugin_root / '.codex-plugin/plugin.json'
    if not manifest_path.exists():
        errors.append(f'missing plugin manifest: {manifest_path.relative_to(ROOT)}')
        continue
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for key in ('skills',):
        ref = manifest.get(key)
        if not ref or not (plugin_root / ref).resolve().exists():
            errors.append(f'{manifest_path.relative_to(ROOT)} missing ref {key}={ref!r}')
    interface = manifest.get('interface', {})
    for key in ('composerIcon', 'logo'):
        ref = interface.get(key)
        if not ref or not (plugin_root / ref).resolve().exists():
            errors.append(f'{manifest_path.relative_to(ROOT)} missing ref interface.{key}={ref!r}')
    apps_ref = manifest.get('apps')
    if apps_ref and not (plugin_root / apps_ref).resolve().exists():
        errors.append(f'{manifest_path.relative_to(ROOT)} missing apps ref {apps_ref!r}')

if not (plugin_roots[0] / '.app.json').exists():
    errors.append('universal plugin blueprint missing .app.json')
for plugin_root in plugin_roots[1:]:
    if not (plugin_root / '.mcp.json').exists():
        errors.append(f'{plugin_root.relative_to(ROOT)} missing .mcp.json')

# 9. Markdown relative links, when present.
link_pattern = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
for path in source_paths('*.md'):
    text = path.read_text(encoding='utf-8')
    for target in link_pattern.findall(text):
        target = target.strip().split('#', 1)[0]
        if not target or target.startswith(('http://', 'https://', 'mailto:', 'sandbox:', '#')):
            continue
        target = target.strip('<>')
        resolved = (path.parent / target).resolve()
        try:
            relative_target = resolved.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f'markdown link escapes repository: {path.relative_to(ROOT)} -> {target}')
            continue
        if resolved.exists():
            continue
        parts = relative_target.parts
        if (
            len(parts) >= 3
            and parts[0] == 'implementation'
            and parts[1] in {'p00', 'p01', 'p02'}
            and parts[2] == 'evidence'
        ):
            declared_local_evidence_links += 1
        else:
            errors.append(f'broken markdown link: {path.relative_to(ROOT)} -> {target}')

result = {
    'root': str(ROOT),
    'files': sum(1 for p in source_paths('*') if p.is_file()),
    'features': len(rows_csv),
    'capability_contracts': len(registry['contracts']),
    'contract_markdown_headings': heading_count,
    'feature_domains': len({r['domain'] for r in rows_csv}),
    'schemas_checked': len(schema_paths) if Draft202012Validator is not None else 0,
    'p00_source_locks_checked': p00_source_locks_checked,
    'p00_target_profiles_checked': p00_target_profiles_checked,
    'roadmap_phases': len(expected_phases),
    'wbs_tasks': len(wbs),
    'root_skills': len(root_skills),
    'declared_local_evidence_links': declared_local_evidence_links,
    'errors': errors,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(1 if errors else 0)
