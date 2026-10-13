"""Exact original two CLICK_HERE sources and explicit complete-style candidate policy."""
from __future__ import annotations
import io
import re
import zipfile
from xml.etree import ElementTree as ET
from tools.p09 import qualify_click_here_update_target as original
from tools.p09 import qualify_native_form_binding_batch as prior

ROOT, require, sha = prior.ROOT, prior.require, prior.sha
HP, HH = original.HP, original.HH
PDF = 'fixtures/target-build/official-source-cache/devcenter-archive-main-20260906/hwp-automation/HwpAutomation.pdf'
PDF_SHA = 'c787c69d46f26a9fca49ac9d34106bb4f146fb29da9f1caf92c6e77d46cef45b'
LIBRARY = 'implementation/p09/tools/click-here-format-preservation.ps1'
INSPECTOR = 'tools/p09/inspect_click_here_character_typelib.ps1'
LANGUAGES = {'hangul': ('HANGUL', 'FaceNameHangul'), 'latin': ('LATIN', 'FaceNameLatin'),
    'hanja': ('HANJA', 'FaceNameHanja'), 'japanese': ('JAPANESE', 'FaceNameJapanese'),
    'other': ('OTHER', 'FaceNameOther'), 'symbol': ('SYMBOL', 'FaceNameSymbol'), 'user': ('USER', 'FaceNameUser')}


def xml(raw):
    require(len(raw) <= 2097152 and b'<!doctype' not in raw.lower() and b'<!entity' not in raw.lower(),
            'click_format_xml_boundary')
    return ET.fromstring(raw)


def compile_source(case_id, raw, expected_sha, new_text):
    require(type(case_id) is str and case_id in ('P09-54-C01', 'P09-54-C02')
        and sha(raw) == expected_sha and 0 < len(raw) <= 4194304,
        'click_format_source_identity')
    require(type(new_text) is str and 0 < len(new_text.encode('utf-8')) <= 65536
        and not re.search('[\x00-\x1f\x7f]', new_text), 'click_format_text_profile')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        require(0 < len(names) <= 512 and len(names) == len(set(names))
            and all(not n.startswith(('/', '\\')) and '\\' not in n and ':' not in n
                and all(part not in ('', '.', '..') for part in n.split('/')) for n in names)
            and sum(i.file_size for i in archive.infolist()) <= 16777216
            and all(i.file_size <= 2097152 and not i.flag_bits & 1
                and i.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                and (i.external_attr >> 16) & 0o170000 not in (0o120000, 0o040000)
                for i in archive.infolist()), 'click_format_zip_boundary')
        section, header = archive.read('Contents/section0.xml'), archive.read('Contents/header.xml')
    xml(section)
    native = original.native(section, header)
    require(len(set(native['selected_character_style_refs'])) == 1 and len(native['character_definition_sha256']) >= 1,
            'click_format_mixed_source_styles_rejected')
    catalog = xml(header)
    source_ref = native['selected_character_style_refs'][0]
    definitions = [n for n in catalog.iter(HH+'charPr') if n.get('id') == source_ref]
    require(len(definitions) == 1, 'click_format_character_definition')
    style = definitions[0]
    require(re.fullmatch('[0-9]+', style.get('height', '')) and re.fullmatch('#[0-9A-Fa-f]{6}', style.get('textColor', '')),
            'click_format_source_style_scalar')
    refs = [n for n in style if n.tag == HH+'fontRef']
    require(len(refs) == 1 and set(refs[0].attrib) == LANGUAGES.keys(), 'click_format_source_font_refs')
    faces = {}
    for key, (language, item) in LANGUAGES.items():
        groups = [n for n in catalog.iter(HH+'fontface') if n.get('lang') == language]
        require(len(groups) == 1 and re.fullmatch('[0-9]+', refs[0].get(key, '')), 'click_format_font_catalog')
        fonts = [n for n in groups[0] if n.tag == HH+'font' and n.get('id') == refs[0].get(key)]
        require(len(fonts) == 1 and type(fonts[0].get('face')) is str and 0 < len(fonts[0].get('face')) <= 256
            and not re.search('[\x00-\x1f\x7f]', fonts[0].get('face')),
                'click_format_font_identity')
        faces[item] = fonts[0].get('face')
    character = {'foreground_rgb': int(style.get('textColor')[1:], 16), 'height': int(style.get('height')),
        'italic': any(n.tag == HH+'italic' for n in style), 'bold': any(n.tag == HH+'bold' for n in style), 'face_names': faces}
    require(0 < character['height'] <= 1000000, 'click_format_source_height_boundary')
    return {'schema_version': 'hwpx-agent.private-click-here-format-preservation-plan/v1', 'case_id': case_id,
        'source_package_sha256': expected_sha, 'source_package_bytes': len(raw), 'source_section_sha256': sha(section),
        'field_name': 'p09-click-field', 'native_begin_id': native['native_begin_id'], 'native_field_id': native['native_field_id'],
        'parameters_sha256': native['parameters_sha256'],
        'source_character_definition_sha256': native['character_definition_sha256'][0],
        'source_character_style_ref': int(source_ref), 'source_field_text_sha256': native['display_sha256'],
        'new_text': new_text, 'new_text_sha256': sha(new_text.encode('utf-8')), 'character': character,
        'formatting_policy': 'preserve_entire_uniform_source_selected_character_parameter_set',
        'source_character_runs_uniform': True, 'native_runtime_qualified': False,
        'render_differential_qualified': False, 'p09_complete': False}


def original_plans():
    result = []
    for index, (_, (file, digest, _, text)) in enumerate(original.CASES.items(), 1):
        raw = prior.candidate.bounded(ROOT/original.DISCOVERY/file)
        result.append(compile_source(f'P09-54-C{index:02}', raw, digest, text))
    return result


def public_inventory(plans):
    require(type(plans) is list and len(plans) == 2 and [p['case_id'] for p in plans] == ['P09-54-C01', 'P09-54-C02'],
            'click_format_complete_two_inventory')
    return [{'case_id': p['case_id'], 'source_package_sha256': p['source_package_sha256'],
        'source_package_bytes': p['source_package_bytes'], 'plan_sha256': sha(prior.canonical(p)),
        'source_character_definition_sha256': p['source_character_definition_sha256'],
        'font_languages_checked': 7, 'source_runs_uniform': True, 'native_runtime_or_render_qualified': False} for p in plans]
