# Artifact 키의 Windows 읽기 전용 보관 연결

Artifact AES 암호화와 다운로드 HMAC 서명이 부모 프로세스의 임시 키에만 의존하지 않도록,
Windows 자격 증명 저장소의 정확한 항목에서 키를 읽는 연결을 제공한다. 기존 AES 암호화·AEAD 결속·서명 구현은 그대로 사용한다.
이 연결은 키 생성·발급·덮어쓰기·삭제나 제품 실행 권한을 제공하지 않는다.

## 신뢰 설정과 항목 결속

서버 launcher는 `ArtifactCustodyProfile`과 활성 AES 참조·유지할 복호화 참조·별도 HMAC 참조를 설정한다.
profile은1~120byte의 ASCII 영숫자와 점·밑줄·하이픈만 허용한다. 공개 제품 요청이나 문서에서 profile·키 bytes를 받는 API는 없다.

`ArtifactCustodyProfile::credential_target`은 OS 저장소 접근 없이 installer용 비밀이 아닌 locator를 만든다.
`hwpx-agent.artifact-custody/v1`,profile,purpose,key reference 각각의 UTF8 bytes 앞에8byte big-endian 길이를 붙여 SHA256으로 결속한다.
target은 `hwpx-agent.artifact-custody.v1:{purpose}:{full_sha256}`이며 purpose는 `aes256-gcm`과 `download-hmac-sha256`으로 분리한다.
기존 remote-sync JWT namespace나 전역 기본 keyring store를 사용하지 않는다.

CredentialBlob은 정확히72byte다. 첫8byte는 ASCII `HWPXKEY1`, 다음32byte는 완전한 target UTF8 bytes의 SHA256,
마지막32byte는 해당 용도의 키다. 형식·크기·target 결속이 다르면 거부한다. 발급자는 독립적인 안전한 난수 키를 사용해야 한다.
이 계약에 평문 키 파일이나 자동 bootstrap writer는 없다.

## 읽기와 키 교체

`WindowsArtifactKeyCustody::bind`는 profile만 결속하고 자격 증명을 읽거나 열거하지 않는다.
`load_keyring`은 활성 참조를 포함한1~16개의 중복 없는 명시적 참조를 먼저 검증한 뒤 정확한 항목만 읽는다.
유지할 이전 AES 참조도 함께 읽으므로 활성 키를 교체한 후 이전 암호문을 복호화할 수 있다.
누락된 이전 키를 새 키로 대체하거나 암호문을 삭제·재암호화하지 않는다.

`load_download_signer`는 별도 HMAC 용도의 항목을 읽어 기존 HTTPS·TTL·서명 검사를 사용하는 `DownloadSigner`를 만든다.
키 bytes는 zeroizing buffer에서 기존 crypto 객체로 전달하며 profile/provider의 Debug는 locator와 비밀을 숨긴다.
OS 오류는 고정 오류 범주로만 반환한다. 누락·가용성·형식·결속·보관 범위 실패에 파일/환경변수·키 재생성 fallback은 없다.

각 기존 항목의 persistence가 읽기 전후 모두 `Local`이어야 한다. 읽기용 modifier만 지정해서 기존 항목의 persistence가 바뀌었다고 간주하지 않는다.
Local은 같은 사용자의 같은 PC의 이후 로그온 세션에 유지되는 범위다.
[Windows Credential Manager의 persistence 정의](https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw)와
[고정 사용 버전의 keyring 동작](https://docs.rs/windows-native-keyring-store/1.1.0/windows_native_keyring_store/)을 따른다.
OS attribute/secret의 다중 읽기는 원자적 key-set snapshot이나 권한 lease가 아니다. 이미 로드한 crypto 객체에 즉시 철회를 소급 적용하지 않는다.

## 검증 범위

[461](../../implementation/p09/evidence/p09-361-artifact-windows-key-custody461.v1.json)의 신규 모델8개는 locator·용도 분리·정확한 blob·
잘못된 key set의 읽기 전 거부·실패의 비우회·활성 키 교체 후 이전 암호문 복호화·누락/잘못된 키 거부·비노출을 확인했다.
OS 시험의 별도 프로세스 exit0도 관측했으나, 그 종료 코드만으로 reader 본문 완료를 확정하지 않았다.

[462](../../implementation/p09/evidence/p09-361-artifact-windows-key-custody462.v1.json)는 모델8개와 생산 코드를 그대로 보존해 재실행하지 않고,
완료 handshake를 보강한 OS 시험1개만 확인했다. 검증기가 생성한 nonce의 새 시험 항목3개만 `Local`로 저장했다.
부모는 키 bytes나 키 환경변수를 자식에게 전달하지 않았고 crypto 객체를 폐기한 뒤 별도 프로세스를 실행했다.
자식은 OS 저장소에서 다시 읽은 키로 이전·현재 AES 암호문2건을 복호화하고 HMAC 서명1건을 확인했다.
부모는 자식의 정확한1test pass와 최종 완료 marker를1KiB 이하의 출력에서 확인했다.

잘못된 용도 blob·Session persistence·삭제된 HMAC 키도 거부했다. 시험 항목3개의 삭제는 Rust 시험과 외부 검증기 양쪽에서 확인했다.
검증기가 중단되면 이미 부재를 확인한 해당 nonce의3개 항목만 정리하며, 기존 자격 증명을 열거하거나 변경하지 않는다.
462는235fresh/final235·산출물1final·진단없음·cleanupTrue·35.734초다. 시스템CPU최고60.90%·가용RAM최저19.245%이며 기존 자원 보호를 유지했다.

이 검증은 합성 공개 payload와 전용 시험 키의 실제 OS 저장소 연결이다. 운영 키 발급·운영 DB·PC 재부팅 후 복구·
키 유실 복구나 현재 scanner/registry·신뢰 제품 route·한글 Native·P09 Gate 완료를 증명하지 않는다.

## 실제 SQL24 저장 경로 연결

[464](../../implementation/p09/evidence/p09-361-catalog-windows-custody-sql464.v1.json)는 새 전용 DB와 새 시험 키 scope에서
기존 실제 카탈로그 HWPX compiler·현재 guard3회·staged validator·SQL job/등록/CAS/완료와 disk AEAD를 이 OS provider에 연결했다.
키 설치 프로세스에는 DB 비밀번호를 전달하지 않았고, 설치가 끝난 뒤 별도 seed/execute/restart 프로세스는 AES/HMAC 환경변수 없이
정확한 OS 항목에서만 키를 읽었다. Python 부모는 DB bootstrap용 임시 자격만 보관하고 artifact 키 bytes를 만들거나 전달하지 않았다.

실제 artifact 서비스의 서명 URL 발급·검증·AEAD 다운로드도 저장 직후와 DB 재시작 뒤에 확인했다. URL·키 값은 출력하지 않았다.
원 source/output·intent/precommit·현재 head의 독립 readback, cold request lookup과 다른 AES 키 거부는 원 경로를 사용했다.
새 DB의 전후 artifact6/job2/attempt2/intent1/revision2/head2와 ciphertext6개 bytes/SHA가 같았다.
재시작 readback은 새 claim/시도/CAS를 실행하지 않았다. 기존 schema23 연결의24 거부와 최소 권한·RLS도 유지했다.

키 전달 경계의 신규 모델4개와 영향 있는 SQL6개 probe를 확인했다. 과거 모델8개·공식249 큐와 이전 DB/job은 반복하지 않았다.
900fresh/final900·설치 설정1final·산출물2final·진단없음·cleanupTrue다. 소유 postmaster2회 정상 종료와 전용 키3개 삭제를 확인했다.
전체181.797초, 빌드15.171초/Job CPU13.594초/private최고991.38MiB, SQL8.157초/CPU5.875초/private최고76.89MiB였다.
시스템CPU최고61.70%·가용RAM최저17.980%이며 기존 한 코어/낮은 우선순위·CPU cap·RAM/commit95% 보호를 유지했다.

전용 DB와 암호문·영수증은 보존했고 합성 시험 키는 정리했다. 실제 운영 DB/운영 키 발급·PC 재부팅·키 유실 복구,
합성 scanner/route 밖의 신뢰 제품 실행·Native/Gate 완료로 승격하지 않는다.

## 남은 복구와 신뢰 경계

새 공통 job의 v2 intent와 원 manifest 없는 복구는467 구성요소·468 실제 SQL에서 확인했다.
468은 원 handles/state/요청 파일3개를 다른 이름으로 보존한 동안 DB 재시작 전후 복구했고 모두 바이트 그대로 복원했다.
905fresh/final905·설정1final·산출물2final·cleanupTrue이며 새 claim/CAS/시도는 없었다.
기존 v1 API는 원 manifest를 받는 호환 경로이며 v1 관측을 자동 승격하지 않는다.
다음은 공개 요청 key의 기존 job과 locator·복구된 revision/receipt/result를 현재 scope에서 결속하는 제품 연결이다.
[intent v1에서 v2로의 계약](p09-stored-commit-intent-v1-to-v2.md)을 따르며 복구는 실행/재시도·현재 route 권한이 아니다.
운영 키 발급·키 유실 복구와 실제 scanner/현재 신뢰 registry도 별도로 마감해야 한다.
