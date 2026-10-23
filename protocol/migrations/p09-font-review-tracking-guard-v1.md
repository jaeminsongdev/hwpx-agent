# P09 폰트 메모 필드와 관측 추적 표시 보호

폰트 후보는 원본에 관측된 HP run의 charTcId와 문단의 paraTcId를 선택된 하위 text까지 상속한다.
표시가 있으면 그 부분의 폰트 치환을 Protection으로 거부한다. ID0/1은 관측 식별자이며 false/true
잠금 Boolean으로 해석하지 않는다. 이 규칙은 SourceFontStyleAxis의 run_property/text_style과
현재 저장/공통 준비·계획 경로에 적용된다. 전체 문서 보호나 Native 추적 변경 자격은 아니다.

## 선택된 문맥의 선형 관측

이미 읽은 각 XML part에서 기존 관측 보호/불확실 서식 map과 함께 tracking map을 한 번 구성한다.
현재 node의 HP p/paraTcId 또는 run/charTcId 존재와 부모의 관측 flag를 합친다. native namespace와
비한정 속성 이름을 확인하며 부모 순서/범위를 검사한다. 선택된 text의 inherited flag가 있으면
이름 matcher·서식 복제·patch/writer 전에 거부한다. 선택마다 부모를 다시 걷거나 XML을 재파싱하지 않는다.
기존 직접 run tracking 검사, source/selector/field·표 보호·출력 readback·영수증은 유지한다.

## 캐시와 review 영역

명시적으로 포함한 숨은 설명과 MEMO payload는 기존 원본 mapper와 selector로만 선택한다.
MEMO editable=0은 payload를 일반 cached result로 바꾸지 않는다. 반대로 원 cached result나 enclosing
DATE 필드는 선택에서 조용히 건너뛰거나 MEMO 예외로 우회하지 않는다. 제외 정책의 선택은 NoMatches다.
비선택 서식·원문·metadata·제어와 원 catalog는 보존한다.

현재 typed admission이 지원하지 않는 p.lock과 합성 중첩 DATE/MEMO 입력은 source/body/review 수입
거부다. 이 입력을 정상 Native 원본이나 nested-cache 의미 검증으로 승격하지 않는다. 유효한 기존
표/셀 fixture의 table lock, cell protect, table size protect는 별도 선택 거부와 비선택 보존으로 확인했다.

## 수정 전 증거와 현재 검증

326의9pass/7fail과327의14pass/6fail을 보존한다. 초기 scope helper가 빈 블록을 고르던 오류를
고쳤고 미지원 문단 속성과 중첩 입력의 수입 거부를 구분했다. 이후328은 production을 바꾸지 않은
상태에서 실제 폰트 후보 반환3개와 수입 거부4개를763fresh/final763으로 확인했다. 후보 반환3개는
FAILED 원본이며 정상 제품 수용으로 바꾸지 않는다. 수정 전 각 시험은 첫 ID0에서 실패했으므로 ID1은 추정하지 않는다.

329는 이3개 실패와 영향13개, 새 text 축/공통 compiler4개를 실행해20pass·765fresh/final765를 확인했다.
수입 단계4개는 재실행하지 않고 보존해 대표 고유24개다. 단일24개 실행이 아니며 원 실패·원본을 보존한다.
현재 검증은 두 축의 ID0/1·선택된 상위/직접 표시·정상 review/캐시·현재 표 보호 조합에 한정한다.
기존56개·공식249개와 한글/COM은 실행하지 않았다.

style_filter/preview_only·전체 유효 서식/fallback·신뢰된 registry·실제 실행/저장/게시·Native 및 나머지
전체 보호 의미는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작을 유지한다.
