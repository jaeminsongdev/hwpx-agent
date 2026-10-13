# P269 원 parent 표본을 사용하는 실패 연결 검증

2026-10-09. runtime 수용87/249, 잔여162(일반156+corpus6), 다음index94.
P09·A12·A13 OPEN. 원600초·CPU/RAM 기준은 변경하지 않음. 실제 full runtime 연결 NOT_RUN.
PC 프리즈 원인·해결 미확정. 실제94 본체 PASS·원 parent 중단 사유·원 Job 정리는 여전히 확인할 수 없다.

## P268 실패 보존 / 재현

P269 첫 사전 호출은 출력 경로가 P268 원 파일을 가리킨 오타 때문에 `NO_OVERWRITE`로 자원 admission 전 차단됐다. 원 파일을 덮어쓰지 않았고 제품/Native probe도 실행하지 않았다. 해당 source/test는 `evidence/preflight-controller-snapshots/p269-preflight-path-run001/`에 길이/SHA 검증 후 별도 보존했다. 출력 경로는 P269로 수정하고 원 실패 witness 경로는 P268로 유지한다.

P268 합성80개 계약은 통과했지만 실제 작은 연결은 FAILED였다. 원 watcher STOP null/cleanup true, IO365읽기/176bound=fresh 완료. 작은3파일 잠금7개는 모두 닫혔고 stream duplicate0, 완료 byte boundary0. CPU max26.93%, 자체 max2.230483%, private56041472bytes였다. CPU 보호 중단으로 분류하지 않는다.

원 P268 helper/test/report/root를 수정하지 않는다. 새 P269는 원 실패 receipt SHA·길이와 원 코드 pin을 다시 확인한다. 저장된 P268 원 예외가 wrapper 코드로 가려졌으므로 receipt에서 원 오류를 복원했다고 하지 않는다.

별도 작은 합성 원 bridge에서 실제 코드를 실행해 `BACKPRESSURE_NO_ORIGINAL_SAMPLE`을 재현했다. 합성 `ORIGINAL_RUN`이 원 `Windows.sample`을 거치지 않고 `pins`를 호출해 비공개 LatestOriginalSample이 비어 있었다. P185 guard가 이를 거절하는 것은 올바르다. 이는 실제94의 사라진 중단 원인에 대한 증명이 아니다.

## 수정과 qualification

새 immutable `qualify_rejected_parent_connection_r2.py`는 작은 합성 parent 안에서 원 bridge가 선택한 `Windows`를 생성하고 원 `sample` 메서드로 실제 표본을 얻는다. 원 method가 비공개 LatestOriginalSample을 갱신하므로 CPU를 합성하거나 guard를 우회하지 않는다.

원 half-second debounce, 두 admission 표본/3초 admission 창, 원 decision의 CPU≥98 4회 연속·RAM·commit, interval-missing 최대6회 처리·20ms 대기, 원1200 parent/600 Native 보호를 유지한다. 추가 thread/제품/Job은 없다. 작은 parent 표본은 최대16개로 제한하고 미측정 Job CPU는 None이다. `OriginalParentSamples`는 작은 qualification용이며 실제 full c.run 대체 코드가 아니다.

기존52+P26828+새8 총88개 합성 계약을 유지한다. P26828개도 현재 r2의 연결/잠금 코드로 재확인한다. 예비88개는 통과했다. 실제 completion은 `evidence/locked-r07/p269-rejected-parent-connection-run01.v1.json`의 state로 판단한다. 없거나 FAILED면 qualification 완료가 아니다.

실제 probe는 새 helper/test와 불변 P267 helper의3파일만 원 frame에서 전후 읽는다. 전체 scope/제품/94 재실행은 아니다. 잠금7/duplicate6/Native reservations13/metadata checks20/원byte1·2MiB 및Native20/s/원600/원CPU·RAM guard를 유지한다. 모두 close/잔여0이고 두 source boundary가 완료돼야 작은 probe만 수용한다. 원 Job cleanup commit은 하지 않는다.

새 버전은 예상과 다른 원 오류 코드도 즉시 닫힌 형태로 out에 기록한다. 거절된 parent row가 있으면 qualification 성공 여부와 무관하게 원 frame/owner 종료 후 diagnostic-only sidecar를 보존한다. 따라서 또 다른 오류가 생겨도 오류를 가리거나 실패 자료를 버리고 자동 재시도하지 않는다.

원94 failed root/0byte 파일과 기존 통과 본체는 그대로 둔다. 전체 실행기 연결·추가 controller scope·사전검증은 후속 단계이며 이 작은 PASS만으로 94 수용/95 건너뛰기/P09 Gate 승격은 하지 않는다.

## 원 증거 SHA-256

- P267 receipt160731bytes: `b0e307c3548c41f843565d87bdfa9a073dc47fd8c722883c875ba332e0afc06d`
- 원94 root1345290bytes: `c347fd3df25cd2b4d52db6f8c27e6325c039f803ab0987f8e0902ac9005f31f9`
- 원P268 FAILED root147778bytes: `2c3a6fbe93444e56af7e293fcebe35574911dfb37e79f1b78ff99307a599fcf3`
- 원P268 helper16511bytes: `2d8a4d5c1eca7177ac739175dfb800c10d7ac8ee8c00f63cb93119004d8d3fea`
- 원P268 test12764bytes: `4307cf4de757cb0776a5574843f2f425d4e991494a3c469e667733ed79cf324f59`
