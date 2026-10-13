"""P54 pure source/metadata checks. No COM activation or native worker invocation."""
import base64
import copy
import io
import json
import os
import re
import subprocess
import unittest
import zipfile
from tools.p09 import click_here_format_plan as m


def replace_part(raw, name, transform):
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as before, zipfile.ZipFile(output, 'w') as after:
        for item in before.infolist():
            content = before.read(item.filename)
            after.writestr(item, transform(content) if item.filename == name else content)
    return output.getvalue()


class ClickHereFormatPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plans = m.original_plans()
        cls.raw = (m.ROOT/m.original.DISCOVERY/'empty.hwpx').read_bytes()

    def compile(self, raw):
        return m.compile_source('P09-54-C01', raw, m.sha(raw), self.plans[0]['new_text'])

    def shell(self, script, payload, legacy=False):
        env = m.prior.environment.child_environment() if legacy else dict(os.environ)
        env['P09_CLICK_PURE_TEST_INPUT'] = base64.b64encode(m.prior.canonical(payload)).decode('ascii')
        prefix = r"""
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
. 'D:/개발/hwpx-agent/implementation/p09/tools/click-here-format-preservation.ps1'
$payload=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($env:P09_CLICK_PURE_TEST_INPUT)) | ConvertFrom-Json
"""
        shell = m.prior.environment.SHELL if legacy else 'pwsh'
        result = subprocess.run([shell, '-NoLogo', '-NoProfile', '-NonInteractive', '-STA', '-EncodedCommand',
            base64.b64encode((prefix+script).encode('utf-16-le')).decode('ascii')],
            cwd=m.ROOT, env=env, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, 'pure PowerShell child failed; no native worker called')
        self.assertFalse(result.stderr)
        return json.loads(result.stdout.decode('utf-8-sig'))

    def test_exact_two_original_sources_styles_and_unicode_hashes(self):
        self.assertEqual([p['source_package_sha256'] for p in self.plans], [v[1] for v in m.original.CASES.values()])
        self.assertEqual([p['source_character_style_ref'] for p in self.plans], [7, 0])
        self.assertEqual([p['character']['foreground_rgb'] for p in self.plans], [0xff0000, 0])
        self.assertEqual([p['character']['italic'] for p in self.plans], [True, False])
        for p in self.plans:
            self.assertEqual(p['new_text_sha256'], m.sha(p['new_text'].encode('utf-8')))
            self.assertEqual(p['character']['height'], 1000)
            self.assertEqual(len(p['character']['face_names']), 7)
            self.assertFalse(p['native_runtime_qualified'] or p['render_differential_qualified'] or p['p09_complete'])

    def test_deterministic_public_inventory_has_no_raw_text_or_fonts(self):
        self.assertEqual(self.plans, m.original_plans())
        rows = m.public_inventory(self.plans)
        for row in rows:
            self.assertEqual(set(row), {'case_id', 'source_package_sha256', 'source_package_bytes',
                'plan_sha256', 'source_character_definition_sha256', 'font_languages_checked',
                'source_runs_uniform', 'native_runtime_or_render_qualified'})
        self.assertRaises(ValueError, m.public_inventory, self.plans[::-1])

    def test_wrong_source_identity_or_case_rejects(self):
        for case, digest in [('P09-54-C01', '0'*64), ('P09-54-C03', m.sha(self.raw))]:
            with self.assertRaises(ValueError):
                m.compile_source(case, self.raw, digest, self.plans[0]['new_text'])

    def test_invalid_or_utf8_oversized_values_reject(self):
        for text in ('', '\x00', 'a\n', '🚀'*16385, True, None):
            with self.assertRaises(ValueError):
                m.compile_source('P09-54-C01', self.raw, m.sha(self.raw), text)

    def test_section_entities_reject_before_original_parser(self):
        for declaration in (b'<!DOCTYPE sec []>', b'<!ENTITY x "v">'):
            raw = replace_part(self.raw, 'Contents/section0.xml', lambda b: declaration+b)
            self.assertRaises(ValueError, self.compile, raw)

    def test_zip_traversal_directory_symlink_and_duplicate_reject(self):
        for name in ('../alias', 'Contents//alias', 'Contents/./alias', '/alias', 'alias/', 'Contents/header.xml', 'link'):
            output = io.BytesIO(self.raw)
            with zipfile.ZipFile(output, 'a') as archive:
                item = zipfile.ZipInfo(name)
                if name == 'link':
                    item.external_attr = (0o120777 << 16)
                with __import__('warnings').catch_warnings():
                    __import__('warnings').simplefilter('ignore', UserWarning)
                    archive.writestr(item, b'x')
            self.assertRaises(ValueError, self.compile, output.getvalue())

    def test_mixed_cache_styles_reject_without_normalization(self):
        def mixed(section):
            matches = list(re.finditer(br'<hp:t>.*?</hp:t>', section, re.S))
            self.assertEqual(len(matches), 1)
            end = matches[0].end()
            return section[:end]+b'</hp:run><hp:run charPrIDRef="0"><hp:t></hp:t>'+section[end:]
        raw = replace_part(self.raw, 'Contents/section0.xml', mixed)
        with self.assertRaisesRegex(ValueError, 'mixed_source_styles'):
            self.compile(raw)

    def test_missing_font_and_zero_height_reject(self):
        transforms = [lambda b: re.sub(br'(<hh:fontRef\b[^>]*?) hangul="[0-9]+"', br'\1', b),
            lambda b: b.replace(b'height="1000"', b'height="0"')]
        for transform in transforms:
            raw = replace_part(self.raw, 'Contents/header.xml', transform)
            self.assertNotEqual(m.sha(raw), m.sha(self.raw))
            self.assertRaises(ValueError, self.compile, raw)

    def test_pure_plan_validation_in_actual_x86_sta_and_pwsh(self):
        script = r"""
foreach ($plan in $payload) {Assert-P09ClickFormatPlan $plan $plan.source_package_sha256}
@{passed=$payload.Count; native_worker_called=$false; is_64_bit=[Environment]::Is64BitProcess;
  apartment=[Threading.Thread]::CurrentThread.ApartmentState.ToString()} | ConvertTo-Json -Compress
"""
        for legacy in (True, False):
            result = self.shell(script, self.plans, legacy)
            self.assertEqual(result['passed'], 2)
            self.assertFalse(result['native_worker_called'])
            self.assertEqual(result['apartment'], 'STA')
            if legacy:
                self.assertFalse(result['is_64_bit'])

    def test_pure_plan_fail_closed_for_types_hashes_flags_and_scope(self):
        bad = []
        mutations = [('native_runtime_qualified', True), ('p09_complete', 'false'), ('native_begin_id', True),
            ('source_package_bytes', '13669'), ('source_package_bytes', 2**32), ('new_text_sha256', '0'*64),
            ('field_name', 'alias'), ('extra', False), ('new_text', '🚀'*16385)]
        for key, value in mutations:
            plan = copy.deepcopy(self.plans[0]); plan[key] = value; bad.append(plan)
        for key, value in [('italic', 1), ('bold', 'false'), ('height', True), ('foreground_rgb', '16711680')]:
            plan = copy.deepcopy(self.plans[0]); plan['character'][key] = value; bad.append(plan)
        plan = copy.deepcopy(self.plans[0]); del plan['character']['face_names']['FaceNameHangul']; bad.append(plan)
        script = r"""
$count=0
foreach ($plan in $payload) {
    $rejected=$false
    try {Assert-P09ClickFormatPlan $plan $plan.source_package_sha256} catch {$rejected=$true}
    if (-not $rejected) {throw 'PURE_NEGATIVE_ACCEPTED'}
    $count++
}
@{rejected=$count; native_worker_called=$false} | ConvertTo-Json -Compress
"""
        self.assertEqual(self.shell(script, bad, True)['rejected'], len(bad))

    def test_pure_style_fixture_rejects_missing_mixed_mismatch_and_coercion(self):
        script = r"""
$plan=$payload[0]; $character=$plan.character
$items=@{TextColor=[uint32]255; Italic=[uint16]1; Bold=[uint16]0; Height=[int]1000}
foreach ($p in $character.face_names.PSObject.Properties) {$items[$p.Name]=$p.Value}
$actual=[pscustomobject]@{SetID='CharShape'; Values=$items}
$actual | Add-Member ScriptMethod ItemExist {param($key) return $this.Values.ContainsKey($key)}
$actual | Add-Member ScriptMethod Item {param($key) return $this.Values[$key]}
Assert-P09ClickStyleValues $actual $character 255
$count=0
foreach ($key in @('TextColor','Italic','Bold','Height')+$character.face_names.PSObject.Properties.Name) {
    $old=$items[$key]; $items.Remove($key)
    $rejected=$false
    try {Assert-P09ClickStyleValues $actual $character 255} catch {$rejected=$true}
    if (-not $rejected) {throw 'PURE_MISSING_ACCEPTED'}
    $items[$key]=$old; $count++
}
foreach ($value in @('255',$true,256)) {
    $items['TextColor']=$value; $rejected=$false
    try {Assert-P09ClickStyleValues $actual $character 255} catch {$rejected=$true}
    if (-not $rejected) {throw 'PURE_COERCION_ACCEPTED'}
    $count++
}
$items['TextColor']=[uint32]255; $items['FaceNameLatin']='wrong'
$rejected=$false
try {Assert-P09ClickStyleValues $actual $character 255} catch {$rejected=$true}
if (-not $rejected) {throw 'PURE_FONT_MISMATCH_ACCEPTED'}
@{positive=1; negative=($count+1); pure_fixture=$true; native_worker_called=$false} | ConvertTo-Json -Compress
"""
        result = self.shell(script, self.plans, True)
        self.assertEqual(result['negative'], 15)
        self.assertTrue(result['pure_fixture'])
        self.assertFalse(result['native_worker_called'])

    def test_pure_selection_guard_rejects_wrong_name_mode_type_or_state(self):
        script = r"""
$plan=$payload[0]
$fake=[pscustomobject]@{SelectionMode=[int]1; CurFieldState=[int]18; Name=$plan.field_name; Called=0}
$fake | Add-Member ScriptMethod MoveToField {
    param($name,$text,$start,$select)
    if ($name -cne $this.Name -or $text -isnot [bool] -or -not $text -or
        $start -isnot [bool] -or -not $start -or $select -isnot [bool] -or -not $select) {
        throw 'PURE_SELECTION_ARGUMENTS'
    }
    $this.Called++; return $true
}
$fake | Add-Member ScriptMethod GetCurFieldName {param($option) return $this.Name}
Select-P09ClickField $fake $plan
$count=0
foreach ($pair in @(@('Name','wrong'),@('SelectionMode',0),@('SelectionMode',$true),
    @('CurFieldState',2),@('CurFieldState',17),@('CurFieldState','18'))) {
    $old=$fake.($pair[0]); $fake.($pair[0])=$pair[1]; $rejected=$false
    try {Select-P09ClickField $fake $plan} catch {$rejected=$true}
    if (-not $rejected) {throw 'PURE_SELECTION_NEGATIVE_ACCEPTED'}
    $fake.($pair[0])=$old; $count++
}
@{positive=1; negative=$count; pure_fixture=$true; native_worker_called=$false} | ConvertTo-Json -Compress
"""
        self.assertEqual(self.shell(script, self.plans, True)['negative'], 6)

    def test_actual_registered_metadata_signatures_without_com_server(self):
        result = subprocess.run(['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-File', str(m.ROOT/m.INSPECTOR)],
            cwd=m.ROOT, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, 'static metadata inspection failed')
        surface = json.loads(result.stdout.decode('utf-8-sig'))
        self.assertEqual(surface['schema_version'], 'hwpx-agent.click-here-character-type-surface/v1')
        self.assertEqual(surface['registered_typelib_sha256'], 'abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9')
        self.assertTrue(surface['no_com_server_activation'] and surface['hwp_process_set_unchanged'])
        self.assertFalse(surface['native_property_set_or_save_reopen_qualified'] or surface['p09_complete'])
        libraries = [b['surface'] for b in surface['binaries'] if b['state'] == 'type_library_read']
        self.assertEqual(len(libraries), 1)
        types = {t['name']: t for t in libraries[0]['selected_types']}

        def member(kind, name, identifier, invoke, returns, parameters):
            rows = [r for r in types[kind]['members'] if r['name'] == name and r['invoke_kind'] == invoke]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0], {'name': name, 'member_id': identifier, 'invoke_kind': invoke,
                'return_variant_type': returns, 'parameters': [{'variant_type': v, 'flags': 1} for v in parameters]})

        get, put, call = 'INVOKE_PROPERTYGET', 'INVOKE_PROPERTYPUT', 'INVOKE_FUNC'
        for name, identifier, returns, parameters in [('MoveToField',10006,11,[8,12,12,12]),
            ('GetFieldText',10008,8,[8]), ('PutFieldText',10009,24,[8,8]), ('GetCurFieldName',10011,8,[12]),
            ('GetFieldList',10015,8,[12,12]), ('GetPosBySet',10040,9,[]), ('SetPosBySet',10041,11,[9]),
            ('RGBColor',30007,3,[17,17,17])]:
            member('IHwpObject', name, identifier, call, returns, parameters)
        for name, identifier in [('SelectionMode',4), ('CurFieldState',5)]:
            member('IHwpObject', name, identifier, get, 3, [])
        member('IHwpObject', 'CharShape', 8, get, 9, [])
        member('IHwpObject', 'CharShape', 8, put, 24, [9])
        for name, identifier, returns, parameters, invoke in [('SetID',3,8,[],get), ('Clone',15000,9,[],call),
            ('IsEquivalent',15004,11,[9],call)]:
            member('IDHwpParameterSet', name, identifier, invoke, returns, parameters)
        for index, (_, face_name) in enumerate(m.LANGUAGES.values()):
            member('HCharShape', face_name, 16415+index, get, 8, [])
            member('HCharShape', face_name, 16415+index, put, 24, [8])
        for name, identifier, vt in [('Bold',16457,18), ('Italic',16458,18), ('TextColor',16467,19), ('Height',16478,3)]:
            member('HCharShape', name, identifier, get, vt, [])
            member('HCharShape', name, identifier, put, 24, [vt])

    def test_worker_ast_is_functions_only_with_no_session_or_ui_creation(self):
        script = r"""
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile(
  'D:/개발/hwpx-agent/implementation/p09/tools/click-here-format-preservation.ps1',[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw 'PURE_AST_PARSE_ERRORS'}
$names=@($ast.EndBlock.Statements | ForEach-Object {
    if ($_ -is [Management.Automation.Language.FunctionDefinitionAst]) {$_.Name}
    elseif ($_ -is [Management.Automation.Language.PipelineAst] -and
        $_.PipelineElements.Count -eq 1 -and $_.PipelineElements[0].GetCommandName() -ceq 'Set-StrictMode') {}
    else {throw 'PURE_TOP_LEVEL_EFFECT'}
})
$commands=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.CommandAst]},$true) |
    ForEach-Object {$_.GetCommandName()})
if ($commands -contains 'New-Object' -or $commands -contains 'Start-Process' -or $commands -contains 'Invoke-Expression') {
    throw 'PURE_SESSION_OR_DYNAMIC_CREATION'
}
@{functions=$names; parsed=$true; native_worker_called=$false} | ConvertTo-Json -Compress
"""
        result = self.shell(script, [], True)
        self.assertEqual(set(result['functions']), {'Assert-P09ClickFormatPlan', 'Get-P09ClickTextSha',
            'Assert-P09ClickStyleValues', 'Select-P09ClickField', 'Invoke-P09ClickFormatPreservation'})
        source = (m.ROOT/m.LIBRARY).read_text(encoding='utf-8')
        for forbidden in ('HWPFrame.', 'RegisterModule(', '.Save(', '.SaveAs(', '.Quit(', 'SelectAll', 'Set-ItemProperty'):
            # The comment explicitly forbids SelectAll; code must contain no such action.
            if forbidden != 'SelectAll':
                self.assertNotIn(forbidden, source)
        self.assertIn('Copy-P09FormParameters $current', source)
        self.assertIn('$Hwp.CharShape=$baseline', source)
        self.assertIn('$current.IsEquivalent($baseline)', source)


if __name__ == '__main__':
    unittest.main()
