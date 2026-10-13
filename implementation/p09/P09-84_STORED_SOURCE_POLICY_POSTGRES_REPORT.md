# P09-84 저장 정책의 실제 PostgreSQL·암호화 파일 연결

## 결과

P09-83의 strict stored source policy consumer에 실제 SQL20 policy read repository와 실제 PostgreSQL artifact metadata/암호화 disk를 연결했다. server fixed scope의 source revision/head/Result/package/provenance/whole graph 및 최신 policy version/철회/양쪽 ACL을 읽고, 원래 typed decoder와 전체 form state binding을 재사용한다. 이 새 연결은 library consumer이며 signed 등록 서비스/실제 scanner·issuer/registered app·제품 실행·native acceptance 완료가 아니다.

새 Rust5개와 검사 runner1개를 추가했다. parent3개에는 module export만 추가했다. 기존 SQL1~20·migration SHA·17-prefix artifact constructor·exact19 revision constructor·lease/CAS·form decoder/domain guard·의존성/설정은 변경하지 않았다. 새 artifact/revision constructor는 registry20개 전체 checksum 및21번째 추가 row까지 확인하는 exact20 profile이다.

## 실제 실행

서로 다른 disposable PostgreSQL18.4 DB와 host encrypted directory 두 번에서 같은 최종 소스59개 및 같은 probe executable로 각각292 assertions가 통과했다. 하나의292 unique coverage를 독립적으로 두 번 실행한 것이며584개의 서로 다른 검사로 부풀리지 않는다.

- 원래 SQL85: idempotency28/authorized full IR25/source policy32.
- ten pinned original/generated source/output paths: genuine SQL lease/CAS source commit, 실제 ArtifactService metadata/암호화 ingest, SQL policy 등록 및 whole policy read/state/graph/receipt 비교70.
- 새 프로세스의 같은 whole receipt/source 검증40. 같은 DB 내 process restart이지 DB restart는 아니다.
- changed20 checksum/future21을 새 artifact/revision 양쪽에서 거부4.
- policy direct table grant/FORCE RLS off/helper EXECUTE를 새 revision admission에서 거부3.
- 실제 policy artifact ACL 취소·복구 후 재검증, append-only revoke와 cached/fresh denial80.
- 독립 새 프로세스에서 revoke 후 정책 fallback 거부10.

각 DB에 policy versions10/revocations10이 남는 것도 확인했다. plaintext/source originals와 모든59 executed source hash는 동일했다. raw scanner 판단/actor scope/worker operation validation/explicit policy choices는 fixture이며 실제 외부 발급 권한 증거가 아니다. 원래 AES-GCM, PG metadata/revision/lease/CAS/read, raw digest/ACL/state 검증 및 source importer/policy domain consumer를 실제 실행했다. fixture paths10개는 distinct digest10개나 새 native captures10개가 아니다.

검사는 preinstalled pinned image,127.0.0.1 ephemeral port, tmpfs/no volume/no host mount로 실행했다. Docker bridge는 사용했으므로 network-none으로 주장하지 않는다. runtime passwords는 기록하지 않았다. 각 실행의 owned container와38개/158595 bytes encrypted test files는 owner 검사 뒤 제거했고 제거를 확인했다. 원본은 삭제하지 않았다.

## 회귀 및 실패

최종 소스의 hwpx-package/CLI 전체 batch107 targets/1096 tests(CLI162/package934)가 failed0/ignored0/filtered0으로 통과했다. 저장 제공자100개도 이 한 batch에 포함됐다. 별도 지난 batch 결과를 대체·합산한 추정치가 아니라 이번 실제 전체 실행의107 result rows를 receipt에 보존했다.

artifact-service/revision-service lib25+16=41 tests도 모두 통과했다.5 crate lib/tests/examples strict lint와 새 Rust5개 개별 format, parent diff checks, runner syntax가 통과했다.

실패 records/whole preimages를 성공과 별도로 보존했다. 처음 legacy artifact가 schema20을 거부한다는 잘못된 검사 가정은 실제17-prefix 동작을 확인하고 검사 가정만 고쳤다. 최초 fixture receipt digest 불일치는 정확한 receipt bytes로 수정했다. registry mutation은 immutable trigger가 거부했으므로 owned disposable admin transaction에서만 fault를 준비하고 trigger를 복구한 뒤 admission을 검사하도록 수정했다. 기존 제품 guard를 완화하지 않았다.

이후 한 차례의55000 committed-oracle 실패와 한 차례의 원래 policy SQL fixture 실패는 원인을 확정하지 못했다. 현재 동일 최종 소스의 완전한 두 회차에서는 재현되지 않았지만 원인 해결/장기 안정성으로 세지 않는다. 안전한 closed codes/Boolean diagnostics를 검사 runner에 추가했고 과거 실패를 보존했다.

기존 P09 conformance validator는 matrix_drift로 실패했다.6 rows(REF-021/022/031/032/033/034)의 component source hashes가 현재 note_hwpx.rs/bookmark_hwpx.rs/hyperlink_hwpx.rs와 다르다. 세 파일은 P83 current source checkpoint와 정확히 같고 이번 작업에서 수정하지 않았다. summary/claims는 동일하지만 실패는 실패다. matrix/old validator/source-lock/qualification을 수정해 green으로 만들지 않았으며 upstream 단계는 도달하지 않았다. 이 검증기 전체를 PASS라고 하지 않는다.

## 보존

P59–P83 pin entries7580, P48 original source1551 files/51047460 bytes, native originals75가 current bytes 또는 whole source archives와 일치했다. P83 source556개 중553개는 현재 동일하며 parent3개의 whole preimages와 module 제거 역비교가 정확했다.206개의 historical changed pin entries는 whole archives로 보존했다. original qualification 전체를 재실행한 것은 아니다.

P83 당시 test executable pin은 historical receipt이며 이번 현재 test executable은 새 source linkage로 재빌드됐다. 과거 assembly executable은 원래 hash 그대로 보존만 했고 다시 실행한 것으로 세지 않았다.

root PLANS.md는 사용자 삭제 지시대로 부재다. 과거 PLANS archives/실패/native/private evidence, P17 frozen guards 및 unrelated user changes는 유지했다. Hwp/COM/UI/접근허용/운영 DB·grant/배포/stage/commit/push는 실행하지 않았다.

## 다음 실제 요구

typed policy registration service에서 fresh source/payload/domain 검증과 policy generation CAS를 수행하고 실제 issuer/인증/Scanner/registered app 및 제품 operation/publication에 연결해야 한다. full importer의 unsupported field meanings/comments 등도 남았다. conformance 원문 해시 drift의 별도 admission/synchronization 및 과거 SQL intermittence의 원인 확정도 아직 필요하다.

A12/A13/P09 Gate OPEN, 목표 active, P10 새 구현 없음. P26 failed_semantic_non_green/P62 UNRESOLVED/current native admission INPUT_CHANGED_RE_ADMISSION_REQUIRED/full native34 NOT_RUN 상태는 이번 component 결과로 변경하지 않는다.
