# P09 폰트 바이너리 참조 프로필

`hwpml-2011-font-binary-static/v10`은 `shape/v6`의 불변 규칙에 `Contents/header.xml`의
HWPML 2011 head namespace font/substFont의 비한정 binaryItemIDRef를 package manifest item에
연결하는 두 규칙만 추가한다. v1~v9, text-style/chart/caption-owner 규칙과 프로필 기본값은 바꾸지 않는다.

## 원본 형식 근거

Hancom 모델 commit `1453388472c703a4b299a0834f425cdac16644b9`의
[font.cpp](https://github.com/hancom-io/hwpx-owpml-model/blob/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Head/font.cpp)와
[substFont.cpp](https://github.com/hancom-io/hwpx-owpml-model/blob/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Head/substFont.cpp)는
ReadAttribute/WriteElement에서 해당 참조를 읽고 쓴다. 이는 어휘 근거이며 Native 렌더나 참조 대상 글꼴의 유효성 증거가 아니다.

검증한 로컬 캐시는 official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/Head 아래에 있다.
font.cpp는3395bytes/SHA256 `502963997102641ca5d5393b642ed70b9a0287694c49b7dc2a0752f93b2905e4`,
substFont.cpp는2051bytes/SHA256 `8904c3597495f20abd00bb6fcb48841a795a125e52ffa49f8b171d4c60ccedbc`다.
원 캐시와 라이선스는 수정하지 않았다.

## 원본 편집의 추가 검사

폰트 참조 치환 compiler는 글꼴·대체 글꼴의 모든 선언된 바이너리 참조를 불변 source graph의
manifest item 및 실제 비어 있지 않은 binary part에 결속한다. XML 또는 text/* 미디어, spine/infrastructure를
글꼴 바이너리로 사용하지 않는다. 누락·잘못된 대상은 `BinaryReference`로 거부한다.
이미 검증된 패키지의 파트·manifest 색인을 공유하며 추가 ZIP 읽기나 graph import는 없다.

이 프로필의 ID 결속만으로는 대상의 media/payload 의미를 보장하지 않는다. 별도 compiler 검사를
통과해도 폰트 유효성·가용성·설치·활성화·라이선스·플랫폼 fallback 또는 Native 보안/렌더 자격은 없다.
기존 typed reader의 substFont 속성 허용 범위를 확대하지 않는다. 다른 namespace/한정 속성,
미등록 ID-like 속성과 중복 선언은 기존 거부 정책을 유지한다.

## 검증과 이관

308은 새10개와 영향 기존14개를24pass·716fresh/final716로 확인했다. 원 v6의 UnknownIdLikeAttribute와
새 v10의 DanglingReference를 같은 선언-only 파생 원본에서 구분했고, 실제 manifest/opaque payload를
갖춘 별도 파생 원본의 치환·보존과 잘못된 대상의 거부를 확인했다. 합성 opaque payload는 실제 글꼴이 아니다.
기존 실패305는 유지하며 원본 HWPX나 과거 영수증을 덮어쓰거나 성공으로 재분류하지 않는다.

기존 API·영수증은 자동 이관하지 않는다. 폰트 원본 compiler가 이 프로필을 명시적으로 선택할 뿐이며
다른 writer/작업은 기존 프로필을 유지한다. SEARCH-024 전체 제품과 P09 Gate는 미완료다.
