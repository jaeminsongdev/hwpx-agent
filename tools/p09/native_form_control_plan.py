"""Private native worker plans from all 15 pinned original fixtures, not public actions.

Body paragraph ordinal is a runtime-checkable candidate, NOT a proven native ID.
Every form must have a unique body paragraph/type pair. Runtime must observe all
three anchor scopes, reject any disagreement and qualify saved/reopened packages.
No collection position, reservation ID, invented native ID or guessed Pos is used.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from xml.etree import ElementTree as ET
from tools.p09 import record_native_form_property_surface as prior

ROOT = prior.ROOT
MANIFEST = 'fixtures/target-build/p09-35-native-form-diagnostics-01/output/fixture-manifest.json'
MANIFEST_SHA = 'ef1bdad32cf06b07725a17888b7378e9720b2111539675c20178ab850f1d9750'
SCHEMA = 'hwpx-agent.private-native-form-control-plan/v1'
HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
HS = '{http://www.hancom.co.kr/hwpml/2011/section}'
TAGS = {HP+'edit': '+edt', HP+'radioBtn': '+rbt'}
ALL_FORMS = {HP+t for t in ('edit', 'radioBtn', 'checkBtn', 'comboBox', 'listBox')}


def require(value: bool, code: str) -> None:
    if not value:
        raise ValueError(code)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def xml(raw: bytes) -> ET.Element:
    require(0 < len(raw) <= 2*1024*1024 and b'<!DOCTYPE' not in raw.upper()
            and b'<!ENTITY' not in raw.upper(), 'control_plan_xml_bound')
    return ET.fromstring(raw)


def compile_case(row: dict, raw: bytes) -> dict:
    require(type(row) is dict and type(raw) is bytes and 0 < len(raw) <= 4194304
            and re.fullmatch(r'P09-35-C(?:0[1-9]|1[0-5])', row['case_id'])
            and type(row['package_bytes']) is int and len(raw) == row['package_bytes']
            and sha(raw) == row['package_sha256'], 'control_plan_source_identity')
    rows, para_base = [], 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        require(len(members) <= 512 and len({m.filename.casefold() for m in members}) == len(members)
                and sum(m.file_size for m in members) <= 16*1024*1024
                and all(m.file_size <= 2*1024*1024 and not m.flag_bits & 1 for m in members),
                'control_plan_package_bound')
        sections = row['complete_map']['sections']
        require(type(sections) is list and 1 <= len(sections) <= 16
                and len({s['part'] for s in sections}) == len(sections), 'control_plan_section_alias')
        for section_index, section in enumerate(sections):
            # This initial worker covers the COMPLETE original 15-case body profile.
            # It does not make an arbitrary-document or nested-list binding claim.
            require(section['part'] == f'Contents/section{section_index}.xml', 'control_plan_section_profile')
            part = archive.read(section['part'])
            root = xml(part)
            paragraphs = root.findall(HP+'p')
            require(root.tag == HS+'sec' and len(paragraphs) == len(section['map']['paragraph_ids'])
                    and list(root.iter(HP+'p')) == paragraphs, 'control_plan_nested_or_missing_paragraph')
            seen = 0
            for paragraph_index, paragraph in enumerate(paragraphs):
                for run_index, run in enumerate(paragraph.findall(HP+'run')):
                    for inline_index, node in enumerate(run):
                        if node.tag not in ALL_FORMS:
                            continue
                        require(node.tag in TAGS and node.find(HP+'sz') is not None
                                and node.find(HP+'pos') is not None
                                and node.find(HP+'sz').get('protect') == '0'
                                and node.find(HP+'pos').get('treatAsChar') == '1'
                                and all(k not in node.attrib for k in ('id', 'instid', 'instId')),
                                'control_plan_unsupported_or_protected')
                        name = node.get('name')
                        tab, rgb = node.get('tabOrder', ''), node.get('foreColor', '')
                        require(type(name) is str and 0 < len(name.encode('utf-8')) <= 1024
                                and not any(ord(c) < 32 for c in name)
                                and re.fullmatch(r'0|[1-9][0-9]{0,8}', tab)
                                and re.fullmatch(r'#[0-9A-Fa-f]{6}', rgb), 'control_plan_exact_intent')
                        rows.append({'section_part': section['part'], 'section_sha256': sha(part),
                            'paragraph_id': section['map']['paragraph_ids'][paragraph_index],
                            'physical_paragraph_ordinal': paragraph_index, 'run_ordinal': run_index,
                            'inline_ordinal': inline_index, 'native_identity_observation': 'missing',
                            'runtime_anchor_candidate': {'List': 0, 'Para': para_base+paragraph_index},
                            'native_ctrl_type': TAGS[node.tag], 'name': name, 'tab_order': int(tab),
                            'foreground_rgb': int(rgb[1:], 16), 'shape_locked': False})
                        seen += 1
            require(seen == len(section['map']['component_controls'])
                    and seen == sum(1 for n in root.iter() if n.tag in ALL_FORMS),
                    'control_plan_complete_form_inventory')
            para_base += len(paragraphs)
    require(type(row['controls']) is int and len(rows) == row['controls'] and 1 <= len(rows) <= 128,
            'control_plan_complete_case_inventory')
    require(len({(r['runtime_anchor_candidate']['Para'], r['native_ctrl_type']) for r in rows}) == len(rows),
            'control_plan_ambiguous_anchor')
    require(len({r['name'].casefold() for r in rows}) == len(rows)
            and len({r['tab_order'] for r in rows}) == len(rows), 'control_plan_global_uniqueness')
    return {'schema_version': SCHEMA, 'case_id': row['case_id'], 'source_package_sha256': sha(raw),
            'source_package_bytes': len(raw), 'controls': rows,
            'anchor_mapping_qualified': False, 'native_runtime_qualified': False,
            'public_action_or_p09_gate': False}


def original_plans() -> list[dict]:
    manifest_raw = prior.color.history.progress.original.public.checked(ROOT/MANIFEST, MANIFEST_SHA, 4*1024*1024)
    manifest = json.loads(manifest_raw, object_pairs_hook=prior.io.duplicate_guard)
    require(len(manifest['cases']) == 15, 'control_plan_original_fifteen_required')
    plans = []
    for index, row in enumerate(manifest['cases']):
        require(row['case_id'] == f'P09-35-C{index+1:02}' and '/' not in row['file']
                and '\\' not in row['file'] and row['file'].endswith('.hwpx'), 'control_plan_fixture_path')
        raw = prior.color.history.progress.original.public.checked((ROOT/MANIFEST).parent/row['file'], row['package_sha256'], 4194304)
        plans.append(compile_case(row, raw))
    return plans
