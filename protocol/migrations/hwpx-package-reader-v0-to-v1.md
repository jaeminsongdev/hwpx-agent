# HWPX package reader v0 → bounded reader v1

P03-01에서 기존 public package-reader contract가 없는 상태(`v0`)에 `hwpx-package` bounded reader v1을 처음 도입한다. 이 migration은 source ZIP을 변경하거나 이전 출력 형식을 변환하지 않는다.

v1 consumer는 반드시 validated `PackageLimits`를 제공하고 `PackageError::code()`를 기준으로 실패를 처리한다. 성공한 `open`은 archive 구조와 모든 entry metadata가 bounded profile을 통과했다는 뜻이지만 entry payload가 이미 검증됐다는 뜻은 아니다. Payload verification은 `read_entry`가 성공했을 때만 성립한다. 실패한 `read_entry`의 partial bytes는 공개되지 않는다.

향후 v2 변경 중 아래 항목은 additive로 간주하지 않는다.

- ZIP64, data descriptor, encryption 또는 새 compression method 허용
- hard ceiling 상향 또는 unlimited 설정 도입
- path/collision/nested-package rejection 완화
- local/central/CRC/streamed-size 검증 생략
- partial streaming bytes를 caller에게 먼저 공개

이 변경들은 별도 profile/version, migration 문서와 기존 malicious corpus를 보존한 regression Gate를 요구한다. 기존 v1 archive rejection을 성공으로 바꾸는 것은 보안 호환성 변경이며 자동 승격하지 않는다.
