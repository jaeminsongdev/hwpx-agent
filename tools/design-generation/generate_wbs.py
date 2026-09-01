from pathlib import Path
import csv, json, textwrap, re
ROOT=Path(__file__).resolve().parents[2]
HDR="> 기준일: 2026-08-31  \n> 프로젝트 코드명: `hwpx-agent`  \n> 문서 세트 버전: `2.0-design`  \n> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**\n\n"
phases={
'P00':('Source·License·Target Freeze','없음',[
('대상 제품 기준선','primary/secondary 한/글 제품, edition, exact build, locale, bitness를 결정한다.','target-profile.yaml 초안','제품 정보와 runtime probe가 일치'),
('Windows 이미지 기준선','OS build, interactive session 방식, patch policy, image digest를 고정한다.','windows-image decision','깨끗한 이미지에서 설치/실행 smoke'),
('글꼴·프린터 기준선','필수 font set, embedding 권리, 기본/시험용 printer profile을 확정한다.','font-printer manifest','font substitution 0인 기준 fixture'),
('공식 자료 수집','HWPX/OWPML, Help, ActionTable, ParameterSetTable, Automation, Event, WebHWP 자료를 수집한다.','source archive inventory','모든 파일 URL/date/hash 기록'),
('Source lock','원본 checksum, parser rights, 보관 위치, version을 source-lock에 기록한다.','source-lock.json','재다운로드/내부 원본 hash 일치'),
('Automation 라이선스','개인 연구, 사내, 상업 서비스, 서버/VM 범위별 승인 조건을 확인한다.','license-decision.md','법무/사업/기술 승인 서명'),
('WebHWP·외부 provider 라이선스','WebHWP, 변환, OCR, 번역, 서명, 폰트 조건을 분리한다.','provider-license matrix','미승인 provider disabled'),
('기능 baseline 승인','609개 baseline과 completeness 방법을 review한다.','feature-baseline report','누락/중복/비기능 분류 review 완료'),
('P00 gate','모든 blocker와 미결정을 ROADMAP_STATUS에 반영한다.','P00 evidence bundle','다음 phase 시작 승인')]),
'P01':('Repository·CI·Security Foundation','P00',[
('Monorepo 생성','Rust/C#/TypeScript workspace와 경계를 생성한다.','buildable repository','clean checkout build'),
('도구체인 lock','Rust/.NET/Node/protobuf/schema 도구를 lock한다.','toolchain manifests','CI와 local version 일치'),
('Schema·protobuf generation','JSON Schema와 proto codegen을 단일 명령으로 만든다.','generated model packages','breaking/schema compile test'),
('CI matrix','Linux core, Windows worker, widget, docs, security job을 구성한다.','CI workflows','각 job 최소 smoke pass'),
('Secure workdir','temp/staging/quarantine/atomic output 규칙을 구현한다.','workspace utility','path traversal·interruption tests'),
('Dependency security','SBOM, license allowlist, vulnerability/secret scan을 추가한다.','SBOM/security reports','금지 라이선스·secret 0'),
('Logging baseline','request/job/trace ID, redaction, structured logging을 정의한다.','logging crate/package','PII/secret redaction tests'),
('Fixture policy','synthetic/licensed-private/malicious fixture manifest 규칙을 만든다.','fixture manifest schema','라이선스/PII 필드 누락 시 CI fail'),
('Bootstrap docs','개발 환경과 한 명의 새 개발자 smoke 절차를 작성한다.','bootstrap script/runbook','새 환경 재현 성공')]),
'P02':('Official Catalog Importer·Capability Registry','P01',[
('SourceRecord schema','도움말/PDF/XSD/runtime 항목의 공통 record를 정의한다.','source-record schema','sample records validate'),
('Help extractor','메뉴·상세 도움말을 구조화한다.','help records','원문 locator 보존'),
('Automation extractor','Action/Parameter/Object/Event 자료를 구조화한다.','automation records','필드 타입·설명·source hash 보존'),
('OWPML extractor','XSD/패키지 part/element/attribute를 색인한다.','schema records','namespace/version coverage'),
('정규화·중복 후보','label/input/output/scope 기반 candidate를 생성한다.','candidate graph','자동 병합 오탐 review'),
('Semantic capability review','후보를 stable capability와 scope/support에 매핑한다.','reviewed catalog','official item 100% disposition'),
('Binding model','target build action/method/parameter binding schema를 구현한다.','binding registry types','schema/codegen pass'),
('Runtime probe tool','default ParameterSet·실행 effect·modal을 탐사한다.','probe CLI','disposable fixture에서 trace 생성'),
('Registry signing·drift','signed registry와 build-to-build diff를 만든다.','signed registry/drift report','tamper and drift tests')]),
'P03':('HWPX Package·Preserving XML Core','P02',[
('Bounded ZIP reader','크기/entry/압축률/path 제한을 적용한다.','hwpx-package reader','malicious ZIP corpus pass'),
('Package graph','mimetype/container/manifest/relationships/part graph를 구축한다.','PackageGraph','dangling/duplicate relationship tests'),
('XML safety parser','DTD/entity/network off, depth/node/text limit을 구현한다.','safe XML reader','XML bomb/invalid namespace tests'),
('Preserving tokenizer','byte span·namespace-aware token/tree를 만든다.','hwpx-xml token model','parse-serialize untouched equality'),
('Part preservation map','byte/token/semantic/opaque/rejected 등급을 계산한다.','PreservationReport','known fixture expected map'),
('ID/reference index','part별 ID namespace와 cross-reference를 색인한다.','IdIndex','duplicate/dangling/wrong-type detection'),
('Patch engine','제한된 PatchIntent와 overlap/conflict 검사를 구현한다.','preserving patcher','property/random patch tests'),
('Atomic ZIP writer','deterministic normalized writer와 preserve writer를 분리한다.','package writer','crash/no partial output tests'),
('Round-trip·repair','100+ fixture reopen, repair diagnostics, fuzz baseline을 만든다.','roundtrip CLI/evidence','untouched policy 위반 0')]),
'P04':('DocumentGraph·OperationPlan·Transactions','P03',[
('DocumentGraph v2 types','metadata/sections/blocks/controls/resources/review/security graph를 구현한다.','domain-ir crate','serialization/golden tests'),
('Unit·ID model','mm/pt/HWPUNIT, logical/source IDs, coordinate systems을 구현한다.','unit/id module','overflow/rounding/property tests'),
('Selector engine','ID/slot/field/path/text-context selector를 구현한다.','selector module','zero/multiple/stale candidate tests'),
('OperationPlan compiler','schema/default/unit/ambiguity/dependency를 compile한다.','planner','invalid/cycle/needs-resolution tests'),
('Capability router','support/policy/preservation/backend health로 route한다.','router','routing matrix tests'),
('Workspace transaction','isolated working copy와 rollback을 구현한다.','transaction engine','fault injection/no source mutation'),
('Semantic diff','node/style/table/equation/object/reference diff를 구현한다.','diff crate','golden diff tests'),
('Idempotency·CAS','key/hash/retry/revision conflict를 구현한다.','idempotency service','duplicate and stale revision E2E'),
('VS-0 core CLI','A4 한 문단 HWPX를 plan→execute→reopen한다.','vertical CLI','actual Hancom open evidence')]),
'P05':('Text·Character·Paragraph·Page·Section','P04',[
('Text flow reader/writer','run, tab, line break, field boundary를 parse/lower한다.','text module','Unicode/run-boundary corpus'),
('Character styles','언어별 font slots, 크기, 장평, 자간, 효과, 색을 구현한다.','char style lowerer','style dedup/readback'),
('Paragraph styles','정렬, 간격, 들여쓰기, border/fill, keep를 구현한다.','para style lowerer','layout/semantic tests'),
('Tabs','default/custom tab, leader, decimal tab을 구현한다.','tab model','target readback fixtures'),
('Lists·numbering','글머리표/문단번호/개요/재시작/연속성을 구현한다.','list engine','sequence and nesting tests'),
('Page setup','preset/custom mm, orientation, margins, gutter를 구현한다.','PageSetup lowerer','impossible layout negative tests'),
('Sections·columns','section break, equal/custom columns, gaps/separator/balance를 구현한다.','section/column engine','multi-section render tests'),
('Header/footer/page number','variants, restart, fields, master page 연결을 구현한다.','header/footer module','odd/even/first-page fixtures'),
('VS-1 layout','custom paper+2단+styles 문서를 E2E 생성한다.','layout vertical slice','Hancom save/reopen/render pass')]),
'P06':('Table Engine','P05',[
('Grid/span invariant','slot→master cell, rectangular span model을 구현한다.','TableGrid','property tests'),
('Create/insert/delete','표·행·열 생성과 삽입/삭제를 구현한다.','table operations','boundary/index tests'),
('Merge/split','content preservation policy와 span 변환을 구현한다.','merge/split engine','nonrectangular/conflict tests'),
('Cell formatting','margin, border/fill, alignment, direction, protection을 구현한다.','cell style lowerer','readback/render tests'),
('Sizing·autofit','fixed/min/preferred width와 body constraints solver를 구현한다.','layout solver','overflow and font metric tests'),
('FormulaAst','수식, 상대/절대 참조, 캐시, number format을 구현한다.','formula engine','row/column move reference tests'),
('Pagination','repeat header, row/page split, caption, keep를 구현한다.','table pagination validator','boundary page suite'),
('Inspect/select','stable table/cell selector와 snapshot을 구현한다.','table inspector','merged/nested selector tests'),
('Direct/automation differential','61 capability를 target binding과 비교한다.','table conformance report','required matrix green')]),
'P07':('Native Equation Engine','P05',[
('MathAst','semantic nodes, source spans, normalization/hash를 구현한다.','math AST crate','canonicalization property tests'),
('LaTeX adapter','지원 문법·macro limits·ambiguity를 구현한다.','LaTeX parser','Tier A/negative corpus'),
('MathML adapter','namespace/content/presentation subset을 구현한다.','MathML parser','round-trip corpus'),
('EqEdit parser/compiler','target dialect precedence/symbol/escape를 구현한다.','EqEdit module','AST↔script property tests'),
('Direct native lowerer','equation control/script/style/layout를 HWPX에 생성한다.','direct equation writer','native object inspection'),
('Automation binding','native equation insertion/edit/readback을 연결한다.','equation bindings','target action probes'),
('Layout estimator','inline baseline/object extent와 render-required state를 구현한다.','equation layout module','baseline/ink-box visual tests'),
('Tier corpus','A/B/C와 legacy preserve fixture를 구축한다.','equation corpus','A 100%, B target'),
('Editor smoke','double-click edit→token 변경→save/reopen을 자동/수동 증거화한다.','oracle evidence','silent fallback 0')]),
'P08':('Images·Shapes·Drawing·Charts','P05',[
('Asset pipeline','MIME sniff/hash/dedup/relationship/size limit을 구현한다.','asset store adapter','malformed media tests'),
('Image insert','embed/link, crop, resolution, alt text를 구현한다.','image lowerer','reopen/render'),
('Geometry·anchor·wrap','좌표/size/rotation/anchor/text wrap을 구현한다.','object geometry module','page/paragraph anchor fixtures'),
('Basic shapes','line/rectangle/ellipse/text box/freeform을 구현한다.','shape lowerer','property/readback tests'),
('Appearance','line/fill/gradient/pattern/shadow/transparency/effects를 구현한다.','effect model','visual diff'),
('Composition','group/ungroup/z-order/align/distribute/connector를 구현한다.','object graph operations','graph invariant tests'),
('Charts','type/data/series/axis/legend/title/style automation bindings을 구현한다.','chart adapter','target readback/export'),
('OLE/media policy','opaque preserve, blocked activation, inventory를 구현한다.','active-content policy','security corpus'),
('Object conformance','58 capability와 asset/render thresholds를 닫는다.','object report','required matrix green')]),
'P09':('Fields·Forms·Notes·References','P05',[
('Field core','named field, date/file/page/section/object result와 lock/update를 구현한다.','field engine','field readback'),
('Form controls','text/check/radio/combo/list/date properties와 tab order를 구현한다.','form model','input/protection fixtures'),
('Notes','footnote/endnote insert/style/convert/export를 구현한다.','note engine','section-specific tests'),
('Comments','insert/style/show/resolve/delete를 구현한다.','comment model','author/time/readback'),
('Bookmark/hyperlink','target names, external link policy, edit/delete를 구현한다.','link/reference module','dangling/external tests'),
('Cross reference','target graph와 update를 구현한다.','crossref engine','rename/update tests'),
('TOC/index','mark/create/update/hide와 numbering linkage를 구현한다.','TOC/index engine','multi-level corpus'),
('Citation/bibliography','citation source and generated list를 구현/automation 연결한다.','citation adapter','provider/format evidence'),
('Mail merge/labels','data schema, preview, batch output, label layout를 구현한다.','merge engine','record count/privacy tests')]),
'P10':('Windows Hancom Automation Bridge','P03',[
('Protocol','Rust↔Agent gRPC와 Agent↔STA named-pipe protobuf를 정의한다.','proto v1/generated SDK','compatibility test'),
('Windows Agent','job lease, artifact staging, sandbox, upload를 구현한다.','agent service','lease/fencing E2E'),
('STA worker','C#/.NET message pump와 command loop를 구현한다.','STA worker','COM apartment tests'),
('HwpObject lifecycle','create/open/close/quit/process ownership을 구현한다.','HancomSession','leak/crash tests'),
('Security module','file path approval와 safe open policy를 연결한다.','security adapter','allowed/denied path tests'),
('Binding executor','signed allowlist와 typed ParameterSet을 실행한다.','executor','unknown/raw action rejection'),
('Event/modal watchdog','events, expected/unknown dialog, screenshot metadata를 구현한다.','watchdog','unknown modal fail-closed'),
('Isolation','interactive desktop/user/VM, network/clipboard/temp 정책을 구현한다.','worker image/runbook','residue/isolation audit'),
('Timeout/recycle','cancel, unknown outcome reconciliation, process recycle을 구현한다.','supervisor','hang/retry/no duplicate effect'),
('Runtime probe','target build health/capability report를 registry에 공급한다.','probe agent','profile mismatch no lease')]),
'P11':('Advanced Desktop Features','P06,P07,P08,P09,P10',[
('HWP import/export','binary HWP와 office formats를 automation 변환한다.','format adapter','loss/reopen report'),
('Track changes','enable/display/filter/accept/reject/protect를 연결한다.','review bindings','change list readback'),
('Compare/history','문서 비교·병합·한/글 이력 기능을 구현한다.','compare adapter','known-diff fixtures'),
('Chart advanced','chart editing/export behavior를 완성한다.','chart binding bundle','visual/readback'),
('Print/PDF','print profiles, PDF options, tagged PDF를 구현한다.','print/export adapter','spool/export reopen'),
('External tools','spell/dictionary/translation/assets/provider flow를 구현한다.','provider adapters','consent/license/offline tests'),
('Workstation UI','보기/창/도구상자 session capabilities를 구현한다.','UI bindings','session state probe'),
('Advanced security','password/distribution/protection/signature inspection을 연결한다.','security bindings','clean-worker audit'),
('Accessibility','alt text, headings, table headers, reading order/checker를 구현한다.','accessibility suite','checker and tagged export')]),
'P12':('Template Surgical Edit·Cross-backend Normalization','P06,P07,P08,P09,P11',[
('Template analyzer','slots/styles/sections/controls/unknown/protection을 inventory한다.','TemplateSnapshot','real/synthetic template corpus'),
('TemplateContract','fillable/immutable/repeating regions와 allowed operation을 생성한다.','contract generator','schema and human review'),
('Surgical edits','field/slot/stable ID 기반 patch와 untouched policy를 구현한다.','template editor','byte/token preservation'),
('Style mapping','semantic styles를 existing style IDs에 map하고 conflict를 처리한다.','style mapper','no unintended style duplication'),
('Unknown/OLE handling','opaque extension/active content 영향 분석과 quarantine을 구현한다.','preservation/security report','malicious template tests'),
('Cross-backend normalization','direct/automation output을 semantic snapshot으로 조정한다.','normalizer','differential fixtures'),
('Document merge/split','section/style/resource/reference collision을 처리한다.','transform engine','multi-document tests'),
('Exam engine','question/score/choice/answer/keep/split rule를 구현한다.','ExamPlan compiler','30-question fixture'),
('VS-2/VS-3','학교 양식과 수학 시험지를 end-to-end 완성한다.','vertical evidence','Hancom save/reopen/visual pass')]),
'P13':('Validation·Hancom Oracle·Render','P02,P10',[
('Validation model','pass/fail/unverified/skipped evidence와 invalidation을 구현한다.','validation-core','state transition tests'),
('Package/schema validators','ZIP/XML/XSD/relationship/reference 검사를 구현한다.','L1/L2 validators','malformed corpus'),
('Semantic snapshot','문서 의미 canonical snapshot과 feature comparator를 구현한다.','snapshot engine','determinism tests'),
('Hancom open oracle','fresh target process open/repair/error evidence를 구현한다.','L5 oracle','known corrupt fixtures'),
('Save/reopen oracle','save, close, fresh reopen, snapshot compare를 구현한다.','L6 oracle','format-specific suite'),
('Render service','page PDF/image, font substitution, bounds metadata를 생성한다.','render oracle','page count/bounds tests'),
('Visual diff','affected region, text/table/equation/object thresholds를 구현한다.','visual diff tool','golden image suite'),
('Export validator','PDF/DOCX/HWP/image/text reopen/loss를 검증한다.','export validators','conversion matrix'),
('Evidence store/report','환경 digest, artifact refs, freshness와 dashboard를 구현한다.','evidence service','tamper/invalidation tests')]),
'P14':('Projects·Revisions·Jobs·Artifacts','P04',[
('Metadata schema','tenant/project/revision/checkpoint/job/artifact/idempotency DB를 설계한다.','DB migrations','migration/rollback tests'),
('Artifact store','content hash, encryption, ACL, quarantine, signed URL을 구현한다.','artifact service','cross-tenant denial'),
('Revision CAS','immutable DAG와 expected head commit을 구현한다.','revision service','race/conflict tests'),
('History/checkpoints','semantic diff cursor, labels, branches를 구현한다.','history API','DAG/query tests'),
('Job state machine','enqueue/lease/stage/execute/validate/commit 상태를 구현한다.','job service','invalid transition tests'),
('Worker lease/fencing','capability/profile matching, lease expiry, fencing token을 구현한다.','scheduler','late worker commit rejection'),
('Idempotency/reconciliation','request hash, timeout outcome, retry policy를 구현한다.','idempotency module','duplicate side-effect tests'),
('Cancel/cleanup','safe cancellation, orphan artifact, temp cleanup을 구현한다.','cleanup worker','fault injection'),
('Retention/local mirror','purge/legal hold와 Codex project-state mirror를 구현한다.','retention/sync service','delete and conflict tests')]),
'P15':('Remote MCP Control Plane','P14',[
('Auth/tenant','OAuth/OIDC identity, tenant mapping, service tokens를 구현한다.','auth middleware','negative/expiry tests'),
('Public tool schemas','18 tool input/output와 annotations를 확정한다.','MCP descriptors','schema snapshots'),
('Handlers','auth→schema→policy→job/service 호출→structured result를 구현한다.','MCP handlers','contract tests'),
('Async job UX','job IDs, progress, cancel, terminal receipt를 구현한다.','job MCP tools','long-running E2E'),
('Artifact delivery','attachment/signed URL, range, expiry를 구현한다.','artifact_get','ACL/expiry tests'),
('Error mapping','internal errors를 stable public envelope로 map한다.','error catalog','no secret leakage'),
('Rate limit/quotas','tenant/user/capability/job class 제한을 구현한다.','quota service','burst/fairness tests'),
('Telemetry','tool/job/backend/capability SLI와 trace correlation을 구현한다.','dashboards','sample trace complete'),
('Inspector/staging','MCP Inspector와 staging HTTPS E2E를 자동화한다.','staging evidence','all tools green')]),
'P16':('ChatGPT Web Plugin·Widget','P15',[
('Official docs lock','release 시점 plugin/Apps SDK 문서와 examples를 다시 고정한다.','OpenAI source lock','manifest/UI requirements reviewed'),
('Universal package','plugin manifest, registered app mapping, assets를 구성한다.','plugin bundle','package validation'),
('Skills','9개 workflow skill을 실제 tool names와 동기화한다.','skills package','trigger/negative eval'),
('Widget shell','MCP Apps bridge, resource URI, theme/locale를 구현한다.','React widget','bridge lifecycle tests'),
('Project/revision UI','project open, history, checkpoint, conflict 화면을 구현한다.','continuity UI','Web↔Codex E2E'),
('Plan/diff UI','capability route, risk, semantic diff, warnings를 구현한다.','dry-run UI','high-risk confirmation tests'),
('Preview/job UI','page thumbnails, validation badges, progress/cancel을 구현한다.','preview UI','large job tests'),
('Upload/download','input file/asset와 artifact output flow를 구현한다.','file flow','size/type/ACL tests'),
('CSP/a11y/E2E','exact domains, keyboard, screen reader, developer-mode flow를 검증한다.','web release evidence','create/edit/validate/resume/download green')]),
'P17':('Codex Remote·Local Companion','P15',[
('Codex package','manifest, remote app, skills/agents/commands를 구성한다.','Codex bundle','package validation'),
('Remote workflow','동일 MCP project/create/edit/validate를 검증한다.','remote E2E','Web project resume'),
('Local daemon','workspace-confined local service와 health/config를 구현한다.','local daemon','sandbox tests'),
('Local MCP config','optional `.mcp.json`과 startup/auth를 구현한다.','local companion config','fresh install smoke'),
('Local file/Git','fixture/materialize/output/diff/commit helper를 구현한다.','local workflow','path traversal/large file tests'),
('Project sync','local mirror, pull/push/checkpoint를 구현한다.','sync CLI','offline/online transition'),
('Conflict handling','rebase/branch/manual merge와 stale head UI를 구현한다.','conflict resolver','concurrent Web/Codex tests'),
('Approvals','shell/automation/external side effect approval policy를 구현한다.','approval policy','denied-by-default tests'),
('Handoff/evals','AGENTS/handoff와 task eval corpus를 완성한다.','Codex evidence','remote/local parity')]),
'P18':('Quality·Security·Performance·DR','P12,P13,P16,P17',[
('Capability closure','609 rows의 상태·fixture·evidence·제약을 audit한다.','coverage dashboard','missing required field 0'),
('Fuzz/security','ZIP/XML/IR/protocol/widget/API/worker fuzz와 pentest를 수행한다.','security report','critical/high 0'),
('Large document performance','page/object/table/equation scale별 benchmark와 limit을 확정한다.','benchmark report','SLO threshold'),
('Windows capacity','worker density, recycle, cold start, queue capacity를 측정한다.','capacity model','peak load simulation'),
('Chaos/retry','network/storage/worker crash/modal/DB failover를 주입한다.','chaos evidence','no partial/duplicate commit'),
('Backup/restore','DB/object/binding/evidence backup과 restore drill을 수행한다.','DR report','RPO/RTO met'),
('Privacy/retention','PII scan, data residency, purge/legal hold를 검증한다.','privacy assessment','deletion verification'),
('Supply chain','SBOM, provenance, signing, image scanning을 완성한다.','release attestations','policy pass'),
('RC gate','G0-G6와 blocker review를 수행한다.','release candidate','all mandatory gates pass')]),
'P19':('Production Deployment·License·Submission','P18',[
('Production infra','control plane/storage/queue/Windows pool를 배포한다.','production environment','smoke/health pass'),
('License evidence','Automation/WebHWP/font/provider 계약을 production config에 연결한다.','signed license bundle','scope matches deployment'),
('Identity/secrets/domain','OAuth, secrets, domains, TLS, rotation을 설정한다.','security config','rotation/failover test'),
('Privacy/terms/support','정책 문서, support channel, data handling disclosure를 확정한다.','public metadata','legal review'),
('Canary','internal/workspace tenant로 제한 출시한다.','canary report','SLO/error/feedback threshold'),
('Rollback','service/image/registry/binding/widget를 함께 rollback한다.','rollback runbook/evidence','full rollback drill'),
('Plugin submission','manifest, screenshots, test account, review notes를 제출한다.','submission package','review checklist pass'),
('Quota/billing','필요 시 job class/worker cost/billing guardrail을 구현한다.','quota/billing config','abuse/cost tests'),
('GA gate','production smoke, incident contacts, G7를 승인한다.','1.0 release','signed release notes')]),
'P20':('Post-GA Parity·Rust-native Expansion','P19',[
('Source/build watcher','Hancom/OpenAI 문서·build 변화를 감시한다.','change feed','scheduled diff runs'),
('Catalog delta','새 source를 import하고 coverage drift를 review한다.','delta registry','official item disposition'),
('Binding re-probe','새 build의 automation binding을 재검증한다.','binding bundle','target canary green'),
('Direct backend expansion','사용량/안정성 높은 automation capability를 Rust direct로 이전한다.','new direct capabilities','differential parity'),
('WebHWP expansion','라이선스가 있는 환경에서 browser/server route를 추가한다.','WebHWP bindings','cross-backend tests'),
('Schema migration','IR/OperationPlan/project/binding migration을 제공한다.','migrators','N-1 compatibility'),
('Deprecation','removed/renamed capability와 target build sunset을 운영한다.','deprecation notices','no silent break'),
('Performance/cost','queue, storage, render, worker 효율을 지속 개선한다.','optimization report','no correctness regression'),
('Parity release cadence','분기/빌드별 matrix와 evidence report를 발행한다.','parity release','signed report')])
}

# Existing phase filenames.
road=ROOT/'docs/09_roadmap'
phase_files={p:next(road.glob(f'{p}_*.md')) for p in phases}
rows=[]
for phase,(title,deps,tasks) in phases.items():
    first_task_id=f'{phase}-01'
    last_task_index=len(tasks)
    for idx,(name,desc,out,verify) in enumerate(tasks,1):
        tid=f'{phase}-{idx:02d}'
        if idx == 1:
            task_dependencies=deps
            parallelizable='no'
        elif idx == last_task_index:
            task_dependencies=','.join(f'{phase}-{n:02d}' for n in range(1,last_task_index))
            parallelizable='no'
        else:
            task_dependencies=first_task_id
            parallelizable='yes'
        rows.append({'task_id':tid,'phase':phase,'phase_title':title,'task':name,'implementation':desc,'dependencies':task_dependencies,'outputs':out,'verification':verify,'owner_role':('Product/Legal/Architecture' if phase=='P00' else 'Engineering'),'parallelizable':parallelizable})
    body=[f'# {phase} — {title}\n\n',HDR,f'## 선행 조건\n\n`{deps}`\n\n',
          '## 목표\n\n',f'{title}를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.\n\n',
          f'## 작업 분해 구조 ({len(tasks)}개)\n\n',
          '| Task | 작업 | 구현 내용 | 산출물 | 검증 |\n|---|---|---|---|---|\n']
    for idx,(name,desc,out,verify) in enumerate(tasks,1):
        body.append(f'| `{phase}-{idx:02d}` | {name} | {desc.replace("|","/")} | `{out}` | {verify.replace("|","/")} |\n')
    body += ['\n## 구현 순서와 병렬화\n\n',
             '1. 첫 task에서 source/contract/실패 조건을 고정한다.\n',
             '2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.\n',
             '3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.\n',
             '4. backend 연결 후 semantic readback과 required target evidence를 수집한다.\n',
             '5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.\n\n',
             '## Phase hard gate\n\n']
    for idx,(name,desc,out,verify) in enumerate(tasks,1):
        body.append(f'- [ ] `{phase}-{idx:02d}` 산출물 `{out}` 존재, 검증: {verify}.\n')
    body += ['- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.\n',
             '- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.\n',
             '- [ ] source artifact를 in-place로 수정한 경로가 없다.\n',
             '- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.\n\n',
             '## 금지\n\n- hard gate를 “나중에 테스트”로 넘기지 않는다.\n- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.\n- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.\n']
    phase_files[phase].write_text(''.join(body),encoding='utf-8')

# WBS files
fields=['task_id','phase','phase_title','task','implementation','dependencies','outputs','verification','owner_role','parallelizable']
with (ROOT/'WORK_BREAKDOWN_STRUCTURE.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
(ROOT/'specs/work-breakdown-structure.json').write_text(json.dumps({'schema_version':'hwpx-agent.wbs/v1','generated_at':'2026-08-31','count':len(rows),'tasks':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Enhance master roadmap with WBS stats and vertical order.
master=road/'00_master_roadmap.md'
t=master.read_text(encoding='utf-8')
append=f'''\n## 구현 작업 수\n\n`WORK_BREAKDOWN_STRUCTURE.csv`에는 총 **{len(rows)}개** 실행 task가 있다. 각 phase 문서는 task별 구현 내용·산출물·검증·hard gate를 포함한다.\n\n## 권장 첫 구현 경로\n\n`P00 → P01 → P02 → P03 → P04 → P05`를 완료한 뒤 `P06/P07`을 우선 병렬 수행하여 표·자유 문서 크기·native 수식의 VS-1을 만든다. 동시에 `P10` Windows worker를 시작하고, VS-1이 실제 한/글 oracle을 통과한 뒤 P08/P09/P11/P12를 확장한다. 서비스와 앱은 P14/P15/P16/P17에서 붙인다.\n\n## 지원 표기 규칙\n\nphase task가 끝났더라도 capability는 target-profile evidence가 없으면 `implemented_unverified`다. 마케팅/사용자 응답에서 “지원”으로 표시하려면 registry status `verified`와 required evidence freshness가 모두 충족돼야 한다.\n'''
if '## 구현 작업 수' not in t: t += append
master.write_text(t,encoding='utf-8')
print('wbs tasks',len(rows))
