from __future__ import annotations
import csv, json, os, re, hashlib, textwrap
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / 'FEATURE_COVERAGE_MATRIX.csv'
JSON_PATH = ROOT / 'specs/feature-coverage-matrix.json'
HEADER = "> 기준일: 2026-08-31  \n> 프로젝트 코드명: `hwpx-agent`  \n> 문서 세트 버전: `2.0-design`  \n> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**\n\n"

with CSV_PATH.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
fieldnames = list(rows[0].keys())

# Obvious scope/backend corrections discovered during the v2 review.
overrides = {
    'FILE-002': dict(scope_class='workstation_ui', preferred_backend='desktop_automation', fallback_backend='', support_level='AUTOMATION_FULL', phase='P10', validation='session_state_probe', permission='workstation.control', document_ir='N/A'),
    'FILE-004': dict(scope_class='workstation_ui', preferred_backend='desktop_automation', fallback_backend='', support_level='AUTOMATION_FULL', phase='P10', validation='session_state_probe', permission='workstation.control', document_ir='N/A'),
    'FILE-011': dict(scope_class='editor_workflow', preferred_backend='desktop_automation', fallback_backend='project_state_service', support_level='AUTOMATION_FULL', phase='P10', validation='recovery_fixture|session_state_probe', permission='document.write', document_ir='ProjectState/RecoveryPolicy'),
    'FILE-023': dict(scope_class='external_service'),
    'FILE-024': dict(scope_class='external_service'),
    'FILE-027': dict(scope_class='external_service'),
    'FILE-028': dict(scope_class='external_service'),
    'FILE-029': dict(scope_class='external_service'),
    'FILE-030': dict(scope_class='external_service'),
    'FILE-031': dict(scope_class='external_service'),
    'FILE-032': dict(scope_class='external_service'),
    'FILE-035': dict(scope_class='external_service', permission='external.invoke'),
    'FILE-036': dict(scope_class='external_service', permission='external.invoke'),
    'FILE-037': dict(scope_class='external_service', permission='external.invoke'),
    'FILE-038': dict(scope_class='external_service', permission='external.invoke'),
    'FILE-039': dict(scope_class='workstation_ui', permission='workstation.control', document_ir='N/A'),
    'FILE-040': dict(scope_class='external_service', permission='print.execute', document_ir='PrintJob'),
    'EXPORT-001': dict(scope_class='workstation_ui', permission='workstation.control', document_ir='N/A'),
    'REVIEW-002': dict(scope_class='workstation_ui', permission='workstation.control', document_ir='N/A'),
    'REVIEW-003': dict(scope_class='workstation_ui', permission='workstation.control', document_ir='N/A'),
    'REVIEW-014': dict(scope_class='workstation_ui', permission='workstation.control', document_ir='N/A'),
    'REVIEW-017': dict(scope_class='workstation_ui', permission='workstation.control', document_ir='N/A'),
}
for i in range(2, 11):
    overrides[f'EXPORT-{i:03d}'] = dict(scope_class='external_service', permission='print.execute', document_ir='PrintJob')
for r in rows:
    if r['feature_id'].startswith('SEC-'):
        r['scope_class'] = 'security_control'
    if r['feature_id'] in overrides:
        r.update(overrides[r['feature_id']])

# Save corrected canonical matrix.
with CSV_PATH.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader(); w.writerows(rows)
JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

DOMAIN_META = {
    'FILE': ('파일·문서 수명주기', '01_file'),
    'EDIT': ('편집·선택·클립보드', '02_edit'),
    'SEARCH': ('찾기·치환·텍스트 변환', '03_search'),
    'CHAR': ('글자 모양·문자 입력', '04_char'),
    'PARA': ('문단·탭·목록·스타일', '05_para'),
    'PAGE': ('쪽·구역·다단·머리말', '06_page'),
    'TABLE': ('표·셀·계산', '07_table'),
    'EQ': ('수식', '08_eq'),
    'OBJ': ('그림·도형·개체·차트', '09_obj'),
    'REF': ('필드·양식·주석·참조', '10_ref'),
    'REVIEW': ('검토·비교·이력', '11_review'),
    'SEC': ('보안·보호·개인정보', '12_sec'),
    'TOOLS': ('도구·언어·외부 서비스', '13_tools'),
    'AUTO': ('스크립트·자동화·이벤트', '14_auto'),
    'VIEW': ('보기·작업환경', '15_view'),
    'EXPORT': ('인쇄·내보내기·접근성', '16_export'),
}

SELECTORS = {
    'FILE': ('DocumentOrProjectSelector', {
        'type':'object','additionalProperties':False,
        'properties':{
            'project_id':{'type':'string'}, 'revision_id':{'type':'string'},
            'artifact_id':{'type':'string'}, 'document_slot':{'type':'string'},
        }, 'minProperties':1
    }),
    'EDIT': ('RangeControlOrCursorSelector', {
        'type':'object','additionalProperties':False,
        'properties':{
            'range':{'$ref':'operation-plan-v2.schema.json#/$defs/selector'},
            'node_ids':{'type':'array','items':{'type':'string'}},
            'control_id':{'type':'string'}, 'cursor':{'type':'object','additionalProperties':True}
        }, 'minProperties':1
    }),
    'SEARCH': ('SearchScopeSelector', {
        'type':'object','additionalProperties':False,
        'properties':{
            'revision_id':{'type':'string'}, 'scope':{'enum':['document','section','selection','node_set']},
            'section_ids':{'type':'array','items':{'type':'string'}},
            'range':{'type':'object','additionalProperties':True}
        }, 'required':['scope']
    }),
    'CHAR': ('TextRangeSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'range':{'type':'object','additionalProperties':True},'run_ids':{'type':'array','items':{'type':'string'}},'style_id':{'type':'string'}},
        'minProperties':1
    }),
    'PARA': ('ParagraphRangeSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'paragraph_ids':{'type':'array','items':{'type':'string'}},'range':{'type':'object','additionalProperties':True},'style_id':{'type':'string'}},
        'minProperties':1
    }),
    'PAGE': ('SectionOrPageSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'section_ids':{'type':'array','items':{'type':'string'}},'page_numbers':{'type':'array','items':{'type':'integer','minimum':1}},'range':{'type':'object','additionalProperties':True}},
        'minProperties':1
    }),
    'TABLE': ('TableCellSelector', {
        'type':'object','additionalProperties':False,
        'properties':{
            'table_id':{'type':'string'}, 'cell_range':{'type':'object','properties':{'start':{'type':'string'},'end':{'type':'string'}},'required':['start','end'],'additionalProperties':False},
            'row_indices':{'type':'array','items':{'type':'integer','minimum':0}}, 'column_indices':{'type':'array','items':{'type':'integer','minimum':0}},
            'insertion':{'type':'object','additionalProperties':True}
        }, 'minProperties':1
    }),
    'EQ': ('EquationOrInsertionSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'equation_id':{'type':'string'},'equation_ids':{'type':'array','items':{'type':'string'}},'insertion':{'type':'object','additionalProperties':True},'range':{'type':'object','additionalProperties':True}},
        'minProperties':1
    }),
    'OBJ': ('ObjectOrInsertionSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'object_id':{'type':'string'},'object_ids':{'type':'array','items':{'type':'string'}},'insertion':{'type':'object','additionalProperties':True},'anchor_id':{'type':'string'}},
        'minProperties':1
    }),
    'REF': ('ReferenceFieldOrInsertionSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'reference_id':{'type':'string'},'field_name':{'type':'string'},'control_id':{'type':'string'},'insertion':{'type':'object','additionalProperties':True},'range':{'type':'object','additionalProperties':True}},
        'minProperties':1
    }),
    'REVIEW': ('ReviewSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'change_ids':{'type':'array','items':{'type':'string'}},'comment_ids':{'type':'array','items':{'type':'string'}},'author_ids':{'type':'array','items':{'type':'string'}},'range':{'type':'object','additionalProperties':True},'revision_id':{'type':'string'}},
        'minProperties':1
    }),
    'SEC': ('SecurityTargetSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'revision_id':{'type':'string'},'range':{'type':'object','additionalProperties':True},'object_ids':{'type':'array','items':{'type':'string'}},'protection_id':{'type':'string'}},
        'minProperties':1
    }),
    'TOOLS': ('ToolSessionOrDocumentSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'revision_id':{'type':'string'},'range':{'type':'object','additionalProperties':True},'session_id':{'type':'string'},'locale':{'type':'string'}},
        'minProperties':1
    }),
    'AUTO': ('AutomationSessionSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'session_id':{'type':'string'},'worker_id':{'type':'string'},'revision_id':{'type':'string'},'control_id':{'type':'string'}},
        'minProperties':1
    }),
    'VIEW': ('WorkstationViewSelector', {
        'type':'object','additionalProperties':False,
        'required':['session_id'],
        'properties':{'session_id':{'type':'string'},'window_id':{'type':'string'},'pane_id':{'type':'string'}}
    }),
    'EXPORT': ('ExportOrPrintSelector', {
        'type':'object','additionalProperties':False,
        'properties':{'revision_id':{'type':'string'},'artifact_id':{'type':'string'},'page_range':{'type':'string'},'range':{'type':'object','additionalProperties':True}},
        'minProperties':1
    }),
}

BASE_ARGS = {
    'FILE': {'type':'object','additionalProperties':False,'properties':{'format':{'type':'string'},'output_name':{'type':'string'},'options':{'type':'object','additionalProperties':True}}},
    'EDIT': {'type':'object','additionalProperties':False,'properties':{'content':{},'mode':{'type':'string'},'properties':{'type':'object','additionalProperties':True}}},
    'SEARCH': {'type':'object','additionalProperties':False,'properties':{'query':{'type':'string'},'replacement':{'type':'string'},'regex':{'type':'boolean'},'case_sensitive':{'type':'boolean'},'whole_word':{'type':'boolean'},'direction':{'enum':['forward','backward','all']},'style_filter':{'type':'object','additionalProperties':True}}},
    'CHAR': {'type':'object','additionalProperties':False,'properties':{'value':{},'properties':{'type':'object','additionalProperties':True},'merge_mode':{'enum':['replace','merge','toggle']}}},
    'PARA': {'type':'object','additionalProperties':False,'properties':{'value':{},'properties':{'type':'object','additionalProperties':True},'merge_mode':{'enum':['replace','merge']}}},
    'PAGE': {'type':'object','additionalProperties':False,'properties':{'value':{},'properties':{'type':'object','additionalProperties':True},'apply_scope':{'enum':['section','selected_sections','whole_document','from_here']}}},
    'TABLE': {'type':'object','additionalProperties':False,'properties':{'value':{},'properties':{'type':'object','additionalProperties':True},'formula':{'type':'string'},'style_id':{'type':'string'}}},
    'EQ': {'type':'object','additionalProperties':False,'properties':{'source':{'type':'object','additionalProperties':True},'style':{'type':'object','additionalProperties':True},'layout':{'type':'object','additionalProperties':True}}},
    'OBJ': {'type':'object','additionalProperties':False,'properties':{'asset_ref':{'type':'object','additionalProperties':True},'geometry':{'type':'object','additionalProperties':True},'properties':{'type':'object','additionalProperties':True}}},
    'REF': {'type':'object','additionalProperties':False,'properties':{'name':{'type':'string'},'value':{},'properties':{'type':'object','additionalProperties':True},'target':{'type':'object','additionalProperties':True}}},
    'REVIEW': {'type':'object','additionalProperties':False,'properties':{'action':{'type':'string'},'author':{'type':'string'},'note':{'type':'string'},'options':{'type':'object','additionalProperties':True}}},
    'SEC': {'type':'object','additionalProperties':False,'properties':{'secret_ref':{'type':'string'},'policy_id':{'type':'string'},'options':{'type':'object','additionalProperties':True},'confirmation_token':{'type':'string'}}},
    'TOOLS': {'type':'object','additionalProperties':False,'properties':{'provider':{'type':'string'},'locale':{'type':'string'},'options':{'type':'object','additionalProperties':True},'consent_token':{'type':'string'}}},
    'AUTO': {'type':'object','additionalProperties':False,'properties':{'binding_id':{'type':'string'},'parameters':{'type':'object','additionalProperties':True},'timeout_ms':{'type':'integer','minimum':1,'maximum':300000},'expected_dialog_policy':{'type':'string'}}},
    'VIEW': {'type':'object','additionalProperties':False,'properties':{'enabled':{'type':'boolean'},'value':{},'options':{'type':'object','additionalProperties':True}}},
    'EXPORT': {'type':'object','additionalProperties':False,'properties':{'format':{'type':'string'},'options':{'type':'object','additionalProperties':True},'destination':{'type':'object','additionalProperties':True},'printer_profile_id':{'type':'string'}}},
}

def clone(x): return json.loads(json.dumps(x, ensure_ascii=False))

def specialize_args(prefix: str, cap: str, title: str):
    s = clone(BASE_ARGS[prefix])
    props = s.setdefault('properties', {})
    required = []
    op = cap.split('.',1)[1] if '.' in cap else cap
    # Cross-domain concrete argument patterns.
    if cap == 'page.paper_preset':
        s = {'type':'object','additionalProperties':False,'required':['preset'],'properties':{'preset':{'enum':['A3','A4','A5','B4_ISO','B4_JIS','B5_ISO','B5_JIS','LETTER','LEGAL','TABLOID','USER_PROFILE']},'orientation':{'enum':['portrait','landscape']}}}
    elif cap == 'page.paper_custom':
        s = {'type':'object','additionalProperties':False,'required':['width_mm','height_mm'],'properties':{'width_mm':{'type':'number','exclusiveMinimum':0,'maximum':2000},'height_mm':{'type':'number','exclusiveMinimum':0,'maximum':2000},'orientation':{'enum':['portrait','landscape']},'name':{'type':'string'}}}
    elif cap in {'page.margin_all','page.margin_header_footer','page.gutter'}:
        s = {'type':'object','additionalProperties':False,'properties':{'top_mm':{'type':'number','minimum':0},'bottom_mm':{'type':'number','minimum':0},'left_mm':{'type':'number','minimum':0},'right_mm':{'type':'number','minimum':0},'header_mm':{'type':'number','minimum':0},'footer_mm':{'type':'number','minimum':0},'gutter_mm':{'type':'number','minimum':0},'gutter_side':{'enum':['left','right','top','inside']}},'minProperties':1}
    elif cap.startswith('page.column_'):
        s = {'type':'object','additionalProperties':False,'properties':{'count':{'type':'integer','minimum':1,'maximum':32},'equal_width':{'type':'boolean'},'widths_mm':{'type':'array','items':{'type':'number','exclusiveMinimum':0}},'gaps_mm':{'type':'array','items':{'type':'number','minimum':0}},'separator':{'type':'object','additionalProperties':True},'direction':{'enum':['left_to_right','right_to_left']},'balance_last_page':{'type':'boolean'}},'minProperties':1}
    elif cap == 'table.create':
        s = {'type':'object','additionalProperties':False,'required':['rows','columns'],'properties':{'rows':{'type':'integer','minimum':1,'maximum':10000},'columns':{'type':'integer','minimum':1,'maximum':1024},'width_mm':{'type':'number','exclusiveMinimum':0},'column_widths_mm':{'type':'array','items':{'type':'number','exclusiveMinimum':0}},'row_heights_mm':{'type':'array','items':{'type':'number','minimum':0}},'style_id':{'type':'string'},'initial_cells':{'type':'array','items':{'type':'array'}}}}
    elif any(k in op for k in ['insert_rows','delete_rows','insert_columns','delete_columns']):
        s = {'type':'object','additionalProperties':False,'required':['index','count'],'properties':{'index':{'type':'integer','minimum':0},'count':{'type':'integer','minimum':1,'maximum':10000},'inherit_format_from':{'enum':['before','after','none']}}}
    elif any(k in op for k in ['merge_cells','split_cells','split_table','join_table']):
        s = {'type':'object','additionalProperties':False,'properties':{'rows':{'type':'integer','minimum':1},'columns':{'type':'integer','minimum':1},'direction':{'enum':['horizontal','vertical']},'preserve_content':{'enum':['concatenate','first','distribute','reject_if_multiple']}},'minProperties':1}
    elif 'formula' in op or op in {'sum','average','product','count','min','max'}:
        s = {'type':'object','additionalProperties':False,'properties':{'formula':{'type':'string'},'formula_ast':{'type':'object','additionalProperties':True},'recalculate':{'type':'boolean'},'cache_policy':{'enum':['update','preserve','clear']}},'anyOf':[{'required':['formula']},{'required':['formula_ast']}]} 
    elif cap in {'eq.insert_native','eq.edit_native','eq.latex_input','eq.mathml_input','eq.eqedit_input','eq.ast_input'}:
        s = {'type':'object','additionalProperties':False,'required':['source'],'properties':{'source':{'oneOf':[{'type':'object','required':['latex'],'properties':{'latex':{'type':'string'}},'additionalProperties':False},{'type':'object','required':['mathml'],'properties':{'mathml':{'type':'string'}},'additionalProperties':False},{'type':'object','required':['eqedit'],'properties':{'eqedit':{'type':'string'}},'additionalProperties':False},{'type':'object','required':['ast'],'properties':{'ast':{'type':'object','additionalProperties':True}},'additionalProperties':False}]},'display':{'enum':['inline','block']},'style':{'type':'object','additionalProperties':True},'unsupported_policy':{'const':'fail_closed'}}}
    elif prefix == 'EQ' and op not in {'roundtrip_readback','editor_smoke','legacy_script_preserve'}:
        s = {'type':'object','additionalProperties':False,'required':['ast_fragment'],'properties':{'ast_fragment':{'type':'object','additionalProperties':True},'replace_target_path':{'type':'string'},'style':{'type':'object','additionalProperties':True}}}
    elif cap in {'obj.image_insert','obj.video_insert','obj.audio_insert','obj.ole_insert'}:
        s = {'type':'object','additionalProperties':False,'required':['asset_ref'],'properties':{'asset_ref':{'$ref':'artifact-ref.schema.json'},'link_mode':{'enum':['embed','link','package_relationship']},'geometry':{'type':'object','additionalProperties':True},'alt_text':{'type':'string'},'mime_type':{'type':'string'}}}
    elif cap in {'obj.position','obj.size','obj.anchor','obj.wrap','obj.rotate','obj.crop','obj.transparency'}:
        s = {'type':'object','additionalProperties':False,'properties':{'x_mm':{'type':'number'},'y_mm':{'type':'number'},'width_mm':{'type':'number','exclusiveMinimum':0},'height_mm':{'type':'number','exclusiveMinimum':0},'rotation_deg':{'type':'number'},'anchor':{'enum':['character','paragraph','page','section']},'wrap':{'type':'string'},'crop':{'type':'object','additionalProperties':True},'opacity':{'type':'number','minimum':0,'maximum':1}},'minProperties':1}
    elif cap.startswith('search.find'):
        s = {'type':'object','additionalProperties':False,'required':['query'],'properties':{'query':{'type':'string','minLength':1},'regex':{'type':'boolean'},'case_sensitive':{'type':'boolean'},'whole_word':{'type':'boolean'},'include_hidden':{'type':'boolean'},'style_filter':{'type':'object','additionalProperties':True},'max_results':{'type':'integer','minimum':1,'maximum':100000}}}
    elif cap.startswith('search.replace'):
        s = {'type':'object','additionalProperties':False,'required':['query','replacement'],'properties':{'query':{'type':'string','minLength':1},'replacement':{'type':'string'},'regex':{'type':'boolean'},'case_sensitive':{'type':'boolean'},'whole_word':{'type':'boolean'},'style_filter':{'type':'object','additionalProperties':True},'max_replacements':{'type':'integer','minimum':1,'maximum':100000},'preview_only':{'type':'boolean'}}}
    elif cap in {'char.font_size','eq.font_size'}:
        s = {'type':'object','additionalProperties':False,'required':['size_pt'],'properties':{'size_pt':{'type':'number','minimum':1,'maximum':4096},'relative':{'type':'boolean'}}}
    elif cap in {'char.text_color','char.highlight','eq.color'} or 'background_color' in cap:
        s = {'type':'object','additionalProperties':False,'required':['color'],'properties':{'color':{'oneOf':[{'type':'string','pattern':'^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$'},{'type':'object','additionalProperties':True}]},'theme_role':{'type':'string'}}}
    elif prefix in {'CHAR','PARA','PAGE','TABLE','OBJ','REF'} and any(k in op for k in ['enable','hidden','protect','printable','lock','show_hide','repeat_header','allow_page_split','first_page_special']):
        s = {'type':'object','additionalProperties':False,'required':['enabled'],'properties':{'enabled':{'type':'boolean'}}}
    elif cap.startswith('sec.') and any(k in op for k in ['password','encrypted','distribution','protect','restriction']):
        s = {'type':'object','additionalProperties':False,'properties':{'secret_ref':{'type':'string','description':'Secret manager reference; plaintext secrets are forbidden.'},'protection_policy':{'type':'object','additionalProperties':True},'allow_copy':{'type':'boolean'},'allow_print':{'type':'boolean'},'confirmation_token':{'type':'string'}},'minProperties':1}
    elif cap == 'sec.password_bypass':
        s = {'type':'object','additionalProperties':False,'properties':{}}
    elif prefix == 'VIEW':
        s = {'type':'object','additionalProperties':False,'properties':{'enabled':{'type':'boolean'},'value':{},'persist_scope':{'enum':['session','user_profile']},'options':{'type':'object','additionalProperties':True}},'minProperties':1}
    elif prefix == 'EXPORT' and op.startswith('print_'):
        s = {'type':'object','additionalProperties':False,'properties':{'printer_profile_id':{'type':'string'},'page_range':{'type':'string'},'copies':{'type':'integer','minimum':1,'maximum':9999},'duplex':{'enum':['off','long_edge','short_edge']},'n_up':{'type':'integer','minimum':1,'maximum':64},'scaling':{'type':'object','additionalProperties':True},'watermark':{'type':'object','additionalProperties':True},'spool_only':{'type':'boolean'}},'minProperties':1}
    elif prefix == 'EXPORT' and op.startswith('export_'):
        fmt = op[len('export_'):]
        s = {'type':'object','additionalProperties':False,'properties':{'format':{'const':fmt},'page_range':{'type':'string'},'options':{'type':'object','additionalProperties':True},'output_name':{'type':'string'},'loss_policy':{'enum':['fail_on_loss','report_loss','best_effort_explicit']}},'required':['format']}
    elif prefix == 'AUTO':
        s = clone(BASE_ARGS['AUTO'])
        if cap == 'auto.action_execute':
            s['required']=['binding_id','parameters']
        if cap in {'auto.macro_define','auto.macro_run'}:
            s = {'type':'object','additionalProperties':False,'properties':{'macro_id':{'type':'string'},'script':{'type':'string'},'confirmation_token':{'type':'string'}}}
    elif prefix == 'FILE' and any(x in op for x in ['open_','save','export','convert','import']):
        s = {'type':'object','additionalProperties':False,'properties':{'input_artifact_id':{'type':'string'},'format':{'type':'string'},'output_name':{'type':'string'},'options':{'type':'object','additionalProperties':True},'loss_policy':{'enum':['fail_on_loss','report_loss','best_effort_explicit']}},'minProperties':1}
    elif prefix == 'TOOLS' and (op in {'translation','spellcheck','grammarcheck'} or 'dictionary' in op):
        s = {'type':'object','additionalProperties':False,'properties':{'provider':{'type':'string'},'source_locale':{'type':'string'},'target_locale':{'type':'string'},'mode':{'type':'string'},'consent_token':{'type':'string'},'options':{'type':'object','additionalProperties':True}},'required':['provider']}
    return s

PREFIX_IMPLEMENTATION = {
    'FILE': ('문서/프로젝트 수명주기 서비스가 입력 artifact와 target profile을 검증한 뒤, 새 immutable working revision에서 패키지 또는 변환 작업을 수행한다.', 'HWPX ZIP/OPF/relationship를 안전하게 읽고 필요한 part만 생성·패치한다. 다른 형식 변환은 직접 경로가 검증된 경우에만 사용한다.', '버전별 allowlist binding으로 열기·저장·변환 action을 실행하고 결과 파일을 새 artifact로 회수한다.'),
    'EDIT': ('selector를 stable node/range로 resolve하고, 편집 전후 위치 맵을 유지하며 operation transaction 안에서 mutation한다.', 'DocumentGraph에서 대상 노드를 수정하고 preserving patch compiler가 영향 part만 갱신한다.', 'cursor/selection을 locator로 재현한 뒤 allowlisted action을 실행하고 대상 범위를 다시 읽어 semantic diff를 검증한다.'),
    'SEARCH': ('정규화된 TextIndex와 style/control index에서 후보를 찾고, replacement는 사전 diff를 생성한 뒤 transaction으로 적용한다.', 'XML run 경계와 control 경계를 유지하는 rope/range map으로 검색·치환한다.', '한/글 찾기/바꾸기 ParameterSet을 binding registry에서 구성하되 결과 위치를 추출해 제품 index와 대조한다.'),
    'CHAR': ('대상 TextRun을 필요한 경계에서 분할하고 CharacterStyle delta를 적용한 뒤 동일 스타일 run을 안전하게 병합한다.', 'charPr/style registry를 deduplicate하고 language font slots·단위·색을 HWPX 표현으로 lower한다.', '대상 범위를 선택하고 CharShape 계열 binding을 실행한 뒤 char shape readback으로 값을 확인한다.'),
    'PARA': ('대상 문단 집합과 list/style dependency를 resolve하고 ParagraphStyle/ListDefinition을 원자적으로 갱신한다.', 'paraPr/tab/list/style part를 참조 무결성 있게 생성·재사용하고 문단 속성 ID를 교체한다.', 'ParaShape/Style/List 계열 binding을 실행하고 문단 속성·번호 결과를 다시 읽는다.'),
    'PAGE': ('section selector를 resolve하고 용지·여백·구역·다단·머리말/꼬리말 그래프를 갱신한다. 적용 범위를 반드시 명시한다.', 'secPr/pagePr/header/footer/master-page relationship와 HWPUNIT 변환을 갱신하고 page layout constraints를 검사한다.', 'PageSetup/Section/Column/HeaderFooter 계열 binding을 적용하고 section properties 및 실제 페이지 수를 readback한다.'),
    'TABLE': ('논리 TableGrid와 CellSpanMap을 먼저 변경하고 셀 콘텐츠·스타일·수식·페이지 분할 제약을 함께 검증한다.', 'table/cell XML, row/column span, borderFill, para contents, formula/cache를 참조 무결성 있게 패치한다.', 'Table 계열 action/ParameterSet binding을 사용해 셀 선택을 재현하고 실행 후 grid와 cell properties를 열거해 비교한다.'),
    'EQ': ('입력 source를 MathAst로 parse·normalize한 뒤 semantic hash를 만들고 EqEdit compiler와 native lowerer를 통과시킨다.', 'native equation control과 EqEdit script, object properties를 생성·수정하며 이미지 fallback을 금지한다.', 'EquationCreate/Edit binding으로 native 수식 개체를 만들고 script readback·편집기 smoke·save/reopen을 수행한다.'),
    'OBJ': ('ObjectGraph에서 asset, geometry, anchor, wrap, z-order, effects를 갱신하고 relationship closure를 검사한다.', 'BinData/relationships/drawing control을 생성·패치하고 media hash dedup과 좌표 변환을 수행한다.', 'Picture/Shape/Chart/Object action binding을 실행하고 control properties·render bounds를 readback한다.'),
    'REF': ('Field/Reference graph와 target anchors를 갱신하고 이름 충돌, 순환 참조, 갱신 정책을 검사한다.', 'field/control/note/bookmark/hyperlink/reference XML과 relationship를 생성하고 stable logical ID를 유지한다.', '필드·각주·메모·차례·메일머지 계열 binding을 실행하고 결과 control/field 목록과 표시 값을 readback한다.'),
    'REVIEW': ('ReviewGraph에서 변경·검토자·메모·비교 결과를 명시적으로 변경하며 제품 revision DAG와 한/글 review semantics를 구분한다.', '공개 스키마로 안전하게 표현 가능한 review 정보만 직접 수정하고 unknown revision XML은 보존한다.', 'track-change/review/comment/compare binding을 isolated copy에서 실행하고 변경 목록을 다시 열거한다.'),
    'SEC': ('보호 상태와 사용자 권한을 먼저 검사하고, secret은 secret manager reference로만 전달하며 고위험 작업은 명시적 확인을 요구한다.', '읽기·감사·보존 가능한 security metadata만 직접 처리한다. 암호화/서명 생성은 검증된 공식 경로 없이는 수행하지 않는다.', '보안 action은 전용 licensed worker와 최소 권한 계정에서 실행하고 결과 보호 상태를 재열기하여 확인한다.'),
    'TOOLS': ('외부 provider 또는 편집기 도구를 capability/consent/license 정책으로 resolve하고 원문·결과·provider provenance를 분리 저장한다.', '순수 텍스트 변환처럼 결정적인 기능만 직접 구현하며 provider 고유 결과를 한컴 기능으로 가장하지 않는다.', '한/글 도구 action 또는 승인된 외부 API를 호출하고 변경 전후 diff·provider receipt를 남긴다.'),
    'AUTO': ('AutomationBroker가 version-scoped allowlist binding을 resolve하고 세션·파일 경로·timeout·modal 정책을 포함한 실행 envelope를 만든다.', '직접 HWPX 경로가 아니라 automation infrastructure 자체를 기술하므로 direct backend는 probe/trace artifact만 읽는다.', 'STA worker에서 HwpObject lifecycle을 관리하고 ParameterSet type을 검증한 뒤 실행·readback·trace·process recycle을 수행한다.'),
    'VIEW': ('문서 artifact를 바꾸지 않는 session-scoped UI state로 처리하고 사용자 profile 저장은 별도 동의와 권한을 요구한다.', 'HWPX에 기록하지 않는다. 문서 설정과 혼동되는 입력은 capability planning 단계에서 거부한다.', '활성 한/글 session/window에만 적용하고 session probe로 상태를 확인한다.'),
    'EXPORT': ('원본 revision을 immutable로 두고 ExportJob/PrintJob을 생성하며 output artifact와 loss/evidence report를 분리 저장한다.', 'HWPX/텍스트/구조 추출처럼 검증된 형식만 직접 export하고 renderer provenance를 기록한다.', '한/글 export/print action을 target profile로 실행하고 생성 파일 reopen 또는 spool receipt를 검증한다.'),
}

DOMAIN_ERRORS = {
    'FILE':['FILE_FORMAT_UNSUPPORTED','FILE_PACKAGE_INVALID','FILE_CONVERSION_LOSS','ARTIFACT_CHECKSUM_MISMATCH'],
    'EDIT':['SELECTOR_NOT_FOUND','RANGE_STALE','EDIT_PRECONDITION_FAILED','TRANSACTION_ABORTED'],
    'SEARCH':['SEARCH_PATTERN_INVALID','SEARCH_SCOPE_INVALID','REPLACEMENT_LIMIT_EXCEEDED','RANGE_STALE'],
    'CHAR':['TEXT_RANGE_INVALID','FONT_UNAVAILABLE','STYLE_CONFLICT','VALUE_OUT_OF_RANGE'],
    'PARA':['PARAGRAPH_NOT_FOUND','LIST_REFERENCE_INVALID','STYLE_CONFLICT','LAYOUT_CONSTRAINT_FAILED'],
    'PAGE':['SECTION_NOT_FOUND','PAPER_SIZE_INVALID','MARGIN_EXCEEDS_PAPER','LAYOUT_OVERFLOW'],
    'TABLE':['TABLE_NOT_FOUND','CELL_RANGE_INVALID','MERGE_CONFLICT','FORMULA_INVALID','TABLE_LAYOUT_OVERFLOW'],
    'EQ':['EQUATION_SOURCE_AMBIGUOUS','EQUATION_LATEX_UNSUPPORTED','EQEDIT_COMPILE_FAILED','NATIVE_EQUATION_READBACK_MISMATCH'],
    'OBJ':['OBJECT_NOT_FOUND','ASSET_UNSUPPORTED','OBJECT_GEOMETRY_INVALID','RELATIONSHIP_BROKEN','RENDER_MISMATCH'],
    'REF':['REFERENCE_TARGET_MISSING','FIELD_NAME_CONFLICT','REFERENCE_CYCLE','FIELD_REFRESH_FAILED'],
    'REVIEW':['REVIEW_ITEM_NOT_FOUND','REVIEW_STATE_CONFLICT','TRACKING_UNAVAILABLE','COMPARE_FAILED'],
    'SEC':['SECURITY_POLICY_DENIED','SECRET_REFERENCE_INVALID','PROTECTED_DOCUMENT','SIGNATURE_WOULD_INVALIDATE','SECURITY_STATE_MISMATCH'],
    'TOOLS':['PROVIDER_UNAVAILABLE','CONSENT_REQUIRED','LOCALE_UNSUPPORTED','EXTERNAL_RESULT_UNVERIFIED'],
    'AUTO':['AUTOMATION_BINDING_NOT_FOUND','AUTOMATION_PARAMETER_INVALID','AUTOMATION_TIMEOUT','AUTOMATION_MODAL_BLOCKED','AUTOMATION_PROCESS_CRASH'],
    'VIEW':['WORKSTATION_SESSION_REQUIRED','WINDOW_NOT_FOUND','UI_CAPABILITY_UNAVAILABLE','SESSION_STATE_MISMATCH'],
    'EXPORT':['EXPORT_FORMAT_UNSUPPORTED','EXPORT_LOSS_POLICY_BLOCKED','PRINT_PROFILE_NOT_FOUND','EXPORT_REOPEN_FAILED','SPOOL_FAILED'],
}

RISK_BY_PREFIX = {'SEC':'high','AUTO':'high','TOOLS':'medium','VIEW':'low','EXPORT':'medium','FILE':'medium','EDIT':'medium','SEARCH':'low','CHAR':'low','PARA':'low','PAGE':'medium','TABLE':'medium','EQ':'medium','OBJ':'medium','REF':'medium','REVIEW':'medium'}
HIGH_WORDS = ('password','signature','digital_sign','macro','ole','external','mail','upload','print','delete','distribution','privacy','sanitize','close','process','com_addins')

def feature_prefix(fid): return fid.split('-',1)[0]

def risk_for(row):
    cap=row['capability_id']
    if row['support_level'] in {'DISABLED_BY_POLICY','UNSUPPORTED'}: return 'critical'
    if any(w in cap for w in HIGH_WORDS): return 'high'
    return RISK_BY_PREFIX[feature_prefix(row['feature_id'])]

def mutability(row):
    cap=row['capability_id']
    if row['support_level'] in {'READ_ONLY'} or any(x in cap for x in ('inspect','check','find_','readback','probe','enumerate','window_list','preview')):
        return 'read_only'
    if row['scope_class'] == 'workstation_ui': return 'session_mutation'
    if row['scope_class'] == 'external_service' and ('print' in cap or 'send_' in cap or 'upload' in cap): return 'external_side_effect'
    return 'artifact_mutation'

def fallback_policy(row):
    sl=row['support_level']
    if sl=='HYBRID': return 'Direct backend first when preserving and target constraints pass; otherwise route to a verified desktop binding. Never switch after partial mutation.'
    if sl=='DIRECT_FULL': return 'No implicit automation dependency. Fail if direct capability preconditions are not met.'
    if sl=='AUTOMATION_FULL': return 'Requires an available target-matched licensed worker; no semantic approximation by the direct backend.'
    if sl=='OPTIONAL_EXTERNAL': return 'Requires configured provider, license/consent, and explicit user-visible provenance; otherwise capability is unavailable.'
    if sl=='READ_ONLY': return 'Inspection only. Any mutation request is rejected.'
    if sl=='PRESERVE_ONLY': return 'Opaque data is retained byte/token-equivalently; creation or semantic editing is rejected.'
    if sl=='DISABLED_BY_POLICY': return 'Denied by default policy. Enabling requires a separate security ADR, tenant allowlist, and explicit confirmation.'
    return 'Return CAPABILITY_UNSUPPORTED with target-profile evidence; do not approximate.'

def validation_steps(row):
    vals=[v for v in row['validation'].split('|') if v]
    mapping={
        'schema':'Validate OperationPlan and produced package against version-pinned JSON/XSD constraints.',
        'semantic_reopen':'Reparse output into DocumentGraph and compare requested postconditions.',
        'hancom_open':'Open the artifact in the target Hancom build and record success/error evidence.',
        'save_reopen':'Save in target Hancom, close, reopen, and compare semantic snapshot.',
        'render_diff':'Render affected pages and compare geometry/text/object diff within the feature threshold.',
        'formula_readback':'Read table formula and cached result; compare normalized FormulaAst.',
        'page_split':'Assert row/cell/page split and repeat-header behavior on boundary fixtures.',
        'session_state_probe':'Read current workstation state through the target binding and compare requested value.',
        'recovery_fixture':'Crash/restart the worker under a controlled fixture and verify recovery artifact selection.',
        'export_open':'Open the exported format with the designated validator and record loss report.',
        'security_audit':'Re-open in a clean worker and inspect protection, link, script, OLE, and signature state.',
    }
    out=[]
    for v in vals:
        out.append({'id':v,'procedure':mapping.get(v, f'Execute the `{v}` validator defined in the target profile and attach its evidence artifact.')})
    if not out:
        out=[{'id':'capability_specific','procedure':'Run the capability-specific semantic readback and attach target-build evidence.'}]
    return out

def contract_for(row):
    pref=feature_prefix(row['feature_id'])
    selector_name, selector_schema=SELECTORS[pref]
    overview,direct,automation=PREFIX_IMPLEMENTATION[pref]
    sl=row['support_level']
    direct_required=sl in {'DIRECT_FULL','HYBRID','READ_ONLY','PRESERVE_ONLY'} and row['preferred_backend']=='direct_hwpx'
    automation_required=sl in {'AUTOMATION_FULL','HYBRID'} or row['preferred_backend']=='desktop_automation'
    binding_state = 'target_binding_required' if automation_required else 'not_required_unless_fallback'
    if sl in {'UNSUPPORTED','DISABLED_BY_POLICY'}: binding_state='execution_forbidden'
    return {
        'contract_version':'hwpx-agent.capability-contract/v1',
        **row,
        'selector':{'name':selector_name,'schema':selector_schema},
        'args_schema':specialize_args(pref,row['capability_id'],row['feature_ko']),
        'mutability':mutability(row),
        'risk':risk_for(row),
        'preconditions':[
            'Resolve target_profile and an exact capability registry revision.',
            'Validate caller permission and tenant policy before opening the source artifact.',
            'Resolve selector against the source revision; selectors may not silently retarget after edits.',
            'Run dry-run planning and verify preservation, backend availability, and requested validation gates.',
        ] + (["Acquire a target-build automation lease and verify the licensed worker health probe."] if automation_required else []),
        'semantic_effect':f"Apply semantic capability `{row['capability_id']}` ({row['feature_ko']}) to the resolved target without changing unrelated document meaning.",
        'execution_algorithm':[
            overview,
            'Create an isolated working copy or session; never mutate the source artifact in place.',
            'Execute the selected binding exactly once under an idempotency key and record CapabilityReceipt.',
            'Read back semantic state, run required validators, then atomically commit a new revision or discard the working copy.',
        ],
        'direct_hwpx_algorithm': direct if direct_required or row['fallback_backend']=='direct_hwpx' else 'Direct execution is not claimed for this capability. The direct backend may inspect/preserve opaque data only as allowed by support_level.',
        'desktop_automation_algorithm': automation if automation_required or row['fallback_backend']=='desktop_automation' else 'Desktop automation is not part of the normal route; it may be used only as a separately declared oracle if the target profile permits.',
        'automation_binding':{
            'state':binding_state,
            'binding_key':f"{row['capability_id']}@{{target_product}}/{{target_build}}/{{locale}}",
            'must_record':['action_or_method_id','parameter_set_id','parameter_types','default_source','runtime_probe','manual_source_hash','verified_builds'],
            'rule':'The semantic contract is stable; concrete HAction/ParameterSet names are generated and version-pinned in P02/P10 rather than guessed in this design document.'
        },
        'fallback_policy':fallback_policy(row),
        'validation_steps':validation_steps(row),
        'error_codes':DOMAIN_ERRORS[pref] + ['CAPABILITY_UNAVAILABLE_FOR_TARGET','PERMISSION_DENIED','REVISION_CONFLICT','VALIDATION_FAILED'],
        'audit_fields':['capability_id','feature_id','target_profile','registry_revision','selected_backend','binding_revision','input_artifact_sha256','output_artifact_sha256','semantic_diff_hash','validation_report_id','actor','request_id','idempotency_key'],
        'release_gate':{
            'phase':row['phase'],
            'required_fixture_classes':['happy_path','boundary','negative','preservation','target_build'] + (['security'] if risk_for(row) in {'high','critical'} else []),
            'claim_rule':'The capability may be advertised only when its target-profile row is green and all required evidence is current.'
        }
    }

contracts=[contract_for(r) for r in rows]
contracts_obj={
    'schema_version':'hwpx-agent.capability-contract-registry/v1',
    'generated_at':'2026-08-31',
    'source':'FEATURE_COVERAGE_MATRIX.csv',
    'count':len(contracts),
    'warning':'Concrete Hancom action/ParameterSet identifiers are target-build bindings generated in P02/P10; they are intentionally not guessed here.',
    'contracts':contracts
}
(ROOT/'specs/capability-contracts.generated.json').write_text(json.dumps(contracts_obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

contract_schema={
    '$schema':'https://json-schema.org/draft/2020-12/schema',
    '$id':'https://hwpx-agent.local/schemas/capability-contract-v1.schema.json',
    'title':'CapabilityContract v1','type':'object','additionalProperties':True,
    'required':['contract_version','feature_id','capability_id','support_level','selector','args_schema','mutability','risk','preconditions','execution_algorithm','fallback_policy','validation_steps','error_codes','release_gate'],
    'properties':{
        'contract_version':{'const':'hwpx-agent.capability-contract/v1'},
        'feature_id':{'type':'string','pattern':'^[A-Z]+-[0-9]{3}$'},
        'capability_id':{'type':'string','pattern':'^[a-z][a-z0-9_.-]+$'},
        'support_level':{'type':'string'},
        'selector':{'type':'object','required':['name','schema']},
        'args_schema':{'type':'object'},
        'mutability':{'enum':['read_only','session_mutation','external_side_effect','artifact_mutation']},
        'risk':{'enum':['low','medium','high','critical']},
        'preconditions':{'type':'array','items':{'type':'string'}},
        'execution_algorithm':{'type':'array','items':{'type':'string'}},
        'validation_steps':{'type':'array','items':{'type':'object'}},
        'error_codes':{'type':'array','items':{'type':'string'}},
        'release_gate':{'type':'object'}
    }
}
(ROOT/'specs/capability-contract-v1.schema.json').write_text(json.dumps(contract_schema,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Human-readable per-feature contracts.
contracts_dir=ROOT/'docs/04_feature_catalog/contracts'
contracts_dir.mkdir(parents=True,exist_ok=True)
by_pref=defaultdict(list)
for c in contracts: by_pref[feature_prefix(c['feature_id'])].append(c)

for pref,(domain,slug) in DOMAIN_META.items():
    out=[f"# {domain} — 기능별 구현 계약\n\n",HEADER,
         f"이 문서는 `{domain}` 영역 {len(by_pref[pref])}개 기능의 실행 계약이다. `FEATURE_COVERAGE_MATRIX.csv`의 분류와 `specs/capability-contracts.generated.json`의 기계 판독 계약을 사람이 구현할 수 있게 풀어쓴다. 구체적인 HAction/ParameterSet 문자열은 대상 한/글 build에서 P02/P10 importer와 runtime probe가 확정하며, 여기서 임의로 추정하지 않는다.\n\n"]
    for c in by_pref[pref]:
        out.append(f"## {c['feature_id']} — {c['feature_ko']}\n\n")
        out.append(f"- **Semantic capability:** `{c['capability_id']}`\n")
        out.append(f"- **분류:** `{c['scope_class']}` / `{c['support_level']}` / 위험 `{c['risk']}` / 변경성 `{c['mutability']}`\n")
        out.append(f"- **기본 경로:** `{c['preferred_backend']}` → fallback `{c['fallback_backend'] or '없음'}`\n")
        out.append(f"- **권한·단계:** `{c['permission']}` / `{c['phase']}`\n")
        out.append(f"- **IR 위치:** `{c['document_ir']}`\n")
        out.append(f"- **Selector:** `{c['selector']['name']}`\n\n")
        out.append("### 입력 계약\n\n```json\n"+json.dumps(c['args_schema'],ensure_ascii=False,indent=2)+"\n```\n\n")
        out.append("### 실행 절차\n\n")
        for i,step in enumerate(c['execution_algorithm'],1): out.append(f"{i}. {step}\n")
        out.append("\n**Direct HWPX:** "+c['direct_hwpx_algorithm']+"\n\n")
        out.append("**Desktop automation:** "+c['desktop_automation_algorithm']+"\n\n")
        out.append("**Fallback:** "+c['fallback_policy']+"\n\n")
        out.append("### 검증·오류·완료 기준\n\n")
        for v in c['validation_steps']: out.append(f"- `{v['id']}` — {v['procedure']}\n")
        out.append("- **오류:** "+", ".join(f"`{e}`" for e in c['error_codes'])+"\n")
        out.append(f"- **릴리스:** `{c['release_gate']['phase']}`에서 happy/boundary/negative/preservation/target-build fixture를 통과하고 registry row가 green일 때만 지원을 표기한다.\n\n")
    (contracts_dir/f'{slug}_contracts.md').write_text(''.join(out),encoding='utf-8')

usage = f"""# 기능별 구현 계약 사용법

{HEADER}
## 산출물

- `specs/capability-contract-v1.schema.json`: 계약 한 건의 상위 스키마.
- `specs/capability-contracts.generated.json`: **609개 전 기능**의 기계 판독 계약.
- `docs/04_feature_catalog/contracts/`: 영역별 사람이 읽는 구현 계약.
- `FEATURE_COVERAGE_MATRIX.csv`: 지원 상태와 phase의 canonical 표.

## 구현자가 기능 하나를 시작하는 순서

1. `feature_id` 또는 `capability_id`로 matrix와 generated contract를 찾는다.
2. selector와 `args_schema`를 Rust type 및 JSON Schema로 승격한다.
3. target profile의 capability binding이 없으면 P02/P10 binding 작업을 먼저 수행한다.
4. `support_level`에 맞는 direct/automation 경로만 구현한다.
5. happy, boundary, negative, preservation, target-build fixture를 만든다.
6. semantic readback과 required oracle evidence가 성공한 뒤 registry 상태를 `implemented_unverified → verified`로 바꾼다.
7. MCP에 새 공개 도구를 만들지 말고 기존 `OperationPlan` operation으로 노출한다.

## 중요한 제한

이 계약의 `automation_binding.binding_key`는 안정된 lookup key다. 실제 HAction·ParameterSet 명칭과 필드 타입은 한컴 공식 ActionTable/ParameterSetTable 및 설치된 대상 build runtime probe에서 생성해야 한다. 문서에 문자열을 추정해 박는 것은 금지한다.
"""
(ROOT/'docs/04_feature_catalog/17_contract_usage.md').write_text(usage,encoding='utf-8')

# Regenerate feature catalog tables to reflect corrected rows.
intro_by_pref={
'FILE':'파일 생성·열기·저장·변환·인쇄·외부 전송을 artifact mutation, workstation UI, external service로 분리한다. 원본은 불변이며 모든 결과는 새 artifact다.',
'EDIT':'LLM이 커서 동작을 흉내 내지 않고 stable selector와 transaction으로 의미 편집한다. 순수 편집기 undo/clipboard는 automation session 기능이다.',
'SEARCH':'텍스트·스타일·컨트롤 인덱스를 사용해 run 경계를 넘는 검색을 지원하고, 치환 전에는 반드시 diff와 상한을 계산한다.',
'CHAR':'언어별 글꼴 슬롯, 글자 크기·장평·자간·장식·색·언어 정보를 CharacterStyle delta로 표현한다.',
'PARA':'문단 정렬·간격·들여쓰기·탭·목록·스타일을 참조 그래프로 관리하고 번호 매기기 연속성을 검증한다.',
'PAGE':'문서 크기, 여백, 방향, 제본, 구역, 다단, 머리말·꼬리말, 쪽 번호를 구역 단위로 모델링한다.',
'TABLE':'논리 grid와 병합 master cell을 보존하고, 수식은 FormulaAst로 관리한다. 페이지 분할과 반복 머리행을 실제 렌더로 확인한다.',
'EQ':'모든 수식은 MathAst→EqEdit→native equation으로 생성하며 이미지 fallback을 금지한다.',
'OBJ':'그림·도형·차트·미디어를 asset relationship와 geometry/anchor/wrap 그래프로 관리한다.',
'REF':'필드·양식·각주·메모·책갈피·상호참조·차례·메일머지의 target graph와 갱신 정책을 관리한다.',
'REVIEW':'한/글 변경 추적/비교와 제품 revision DAG를 혼동하지 않고 별도 그래프로 유지한다.',
'SEC':'보안 기능은 별도 trust boundary에서 처리한다. 암호·서명·보호 우회는 절대 암묵적으로 수행하지 않는다.',
'TOOLS':'맞춤법·사전·번역·자산 등은 provider, consent, license, provenance가 있는 외부 기능으로 취급한다.',
'AUTO':'오토메이션은 raw action 실행기가 아니라 버전 고정 allowlisted semantic binding 계층이다.',
'VIEW':'보기·작업 창·도구 상자는 session-scoped workstation state이며 HWPX artifact 기능과 분리한다.',
'EXPORT':'인쇄·내보내기는 별도 job이다. 원본을 바꾸지 않고 loss report와 reopen/spool evidence를 생성한다.',
}
for pref,(domain,slug) in DOMAIN_META.items():
    rs=by_pref[pref]
    out=[f"# {domain} 기능 설계\n\n",HEADER,"## 구현 원칙\n\n",intro_by_pref[pref]+"\n\n",
         "## 공통 처리 순서\n\n1. capability lookup과 target version 확인.\n2. selector/입력 schema 검증.\n3. dry-run에서 route·위험·보존 영향 계산.\n4. isolated output/session에서 실행.\n5. domain-specific semantic readback.\n6. 필요 시 실제 한/글 open/save/render.\n7. evidence와 새 revision 또는 session receipt commit.\n\n",
         f"## 기능 목록 ({len(rs)}개)\n\n",
         "| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |\n|---|---|---|---|---|---|---|---|\n"]
    for r in rs:
        out.append(f"| {r['feature_id']} | {r['feature_ko'].replace('|','/')} | `{r['capability_id']}` | `{r['scope_class']}` | `{r['support_level']}` | `{r['preferred_backend']}` | {r['phase']} | {r['validation'].replace('|','·')} |\n")
    out.append("\n## 상세 구현 계약\n\n")
    out.append(f"각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/{slug}_contracts.md`에 있다.\n\n")
    out.append("## 완료 체크리스트\n\n- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.\n- [ ] target build binding과 source checksum이 기록됐다.\n- [ ] 정상·경계·오류·보안/preservation fixture가 있다.\n- [ ] direct/automation 차이를 differential test로 기록했다.\n- [ ] 사용자 warning/degradation 문구가 정의됐다.\n")
    (ROOT/f'docs/04_feature_catalog/{slug}.md').write_text(''.join(out),encoding='utf-8')

# Update summary counts.
counts=Counter(r['support_level'] for r in rows)
scopes=Counter(r['scope_class'] for r in rows)
domains=Counter(r['domain'] for r in rows)
summary=["# 한/글 기능 전수 매트릭스 요약\n\n",HEADER,
         "`FEATURE_COVERAGE_MATRIX.csv`가 canonical 원본이다. 이 목록은 2026-08-31 설계 baseline이며, P02 official catalog importer가 대상 build별 authoritative registry를 생성한다.\n\n",
         f"- 총 기능: **{len(rows)}개**\n",
         f"- 영역: **{len(domains)}개**\n",
         f"- 기능별 상세 계약: **{len(contracts)}개**\n\n",
         "## 지원 수준\n\n| 수준 | 개수 |\n|---|---:|\n"]
for k,v in counts.most_common(): summary.append(f"| `{k}` | {v} |\n")
summary.append("\n## 기능 범위\n\n| 범위 | 개수 |\n|---|---:|\n")
for k,v in scopes.most_common(): summary.append(f"| `{k}` | {v} |\n")
summary.append("\n## 영역별 개수\n\n| 영역 | 개수 |\n|---|---:|\n")
for k,v in domains.items(): summary.append(f"| {k} | {v} |\n")
summary.append("\n## 읽는 법\n\n`DIRECT_FULL`은 직접 HWPX 경로만으로 완결됨을, `AUTOMATION_FULL`은 대상 한/글 데스크톱 경로가 필수임을, `HYBRID`는 상황에 따라 두 경로를 선택함을 뜻한다. `OPTIONAL_EXTERNAL`은 별도 provider/라이선스/동의가 필요하다. `PRESERVE_ONLY`, `DISABLED_BY_POLICY`, `UNSUPPORTED`는 생성·실행을 지원한다고 표시해서는 안 된다.\n")
(ROOT/'FEATURE_COVERAGE_MATRIX.md').write_text(''.join(summary),encoding='utf-8')

print('generated contracts',len(contracts))
print('support counts',counts)
print('scope counts',scopes)
