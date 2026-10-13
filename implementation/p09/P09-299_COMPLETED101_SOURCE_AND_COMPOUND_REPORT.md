# P09-299~302 완료101 독립 source 마감·결합 수용

2026-10-09. 목표 ACTIVE. P09/A12/A13 OPEN.

## 판정과 잔여

runtime 사례 수용95/249, 잔여154(일반148+corpus6), 다음 index102, whole 재조정 대기92. 독립 source 마감 후보101은 이제 별도 exact compound로 수용되어 미완료 후보0이다. 이는 P09 전체 완료율이 아니다. whole1470/historical67/full249/signed16/제품완료/PC프리즈 해결은 여전히 FALSE다.

원 P291의101 본체는 terminal1 PASS/exit0 후 최종 source CPU STOP이었다. 그 root FAILED/body STOPPED/zero placeholder/부분 after474는 모두 원문 불변이다. 이번에 실패 row를 PASS로 변경하거나 제품 본체를 재실행하지 않았다. 원 본체의 정확한 결합 결과만 새 receipt로 한 번 수용했다.

## P299: 실제 전체 독립 source

- 기존 원1599 + 검토/보존 코드/마감·결합 helper26 =1625개, 120247880 bytes, ancestor308 전체.
- before/after 모두1625개/120247880 bytes 실제 읽기. 캐시 pin으로 대체하지 않음.
- Native1933 open/1933 close/remaining0; duplicate3250 open/3250 close/remaining0, offset3250, metadata identity7116, native reservations5183.
- Frame COMMITTED/등록해제, 모든 cleanup 확인, resource STOP 없음.
- 준비36개 입력72reads/fresh36/4299838bytes. source 계약29 PASS. R4 STOP 검토14를 새 세대 준비 조건으로 연결; R4 및 이전 prototype 코드는 보존하고 각 pin을 검증했다.
- before_release396.3083736000117초, original600초·획득14/global20/metadata32/byte1·2MiB/CPU98x4/RAM비율/720/read·identity·cleanup 기준 유지.
- 표본791: system CPUmax92.13%, own CPUmax1.99005%, private40206336bytes(38.34MiB), working50864128bytes(48.51MiB), available RAMmin23.16637436024126%. early90 경고1/대기2window/1초.
- source 실제 PASS는 본체 재실행이나 단독 runtime 수용이 아니다.

receipt: `implementation/p09/evidence/locked-r07/p299-r5-case101-source-actual-run02.v1.json`
480412 bytes / SHA256 `e9b571513abaabdf8485f6b3849b1cd9b2e38152ec71a7fb57e46c4417f1d742`.

## P300 STOP 검토와 P301 최적화

P300 결합 준비는 metadata 단계에서 CPU STOP. 69read/4664975bytes/69bound/finalfresh0, contracts 미실행/compound·runtime_plan 없음. 정리 확인. 원 실패 그대로 보존했다. 원 본체 및 통과한 P299 full source는 반복하지 않았다.

원95 대기1회/7window/3.5초, 바깥90 경고0: 기존 inner95가 먼저 대기하는 코드 구조 때문에 CPU가95 이상으로 바로 올라가면 outer90 조기 대기는 도달하지 못한다. 이는 순서상 개선 지점이지 시스템 CPU포화 원인 증명이 아니다. 마지막4개 system100/ownCPU0/readdelta0, ownCPUmax1.318267%, private44195840bytes로 직접 연산 포화는 입증되지 않았다.

실패 receipt: `implementation/p09/evidence/locked-r07/p300-r5-case101-compound-run01.v1.json`
31915 bytes / SHA256 `f005fb4d34898abc65e4c2e6ba2501389a421af6519c7a278f4c4828027328af`.

새 `leading_metadata_entry_pressure.py`는 원 reader._read/entry32 wrapper 앞에서 원 hard CPU/RAM/IO600 callback을 먼저 실행한 후90%부터 기존 표본으로 bounded 대기한다. 그 뒤 원 reader/entry32/inner95·90 callback을 그대로 호출한다. 원 pacer/clock/credit/read counter/byte pacing/720/guard/fresh 읽기는 바꾸지 않는다. cleanup은 guard/sleep 없이 outer wrapper를 복원한 다음 원 entry cleanup을 수행한다. 단독 합성18 계약 및 실제 작은2파일의4read/fresh2가 통과했다.

qualification: `implementation/p09/evidence/locked-r07/p301-leading-entry90-qualification-run01.v1.json`.

STOP 뒤의 3초 bounded 프로세스 이름/CPU-delta 관측에는 git2/cargo0/rustc0/python0이었다. 이미 STOP 이후의 별도 시점이라 당시 포화 원인을 특정하는 증거가 아니며, 다른 프로세스의 명령행/로그/비밀값을 출력하거나 종료하지 않았다.

## P302: 실제 metadata-only 결합

새 executor는 원 P300 실패를 검토12 계약으로 바인딩하고, P301의18 계약 및 실제 qualification pin을 확인한 뒤 원 P300 classifier/22 결합 계약을 그대로 사용한다.

- 원101 본체/P299 Native·full-byte source 재실행 없음. 실패 receipt 및 코드 변경/덮어쓰기 없음.
- 준비와 종료 전체 fresh:158read/9600892bytes/78bound/finalfresh78, STOP 없음, watcher cleanup 확인.
- 새 pre-entry outer158calls/158completed/failed0/닫힘; 원 inner95·90 callback 및 entry32 reader 유지 확인.
- 관측19개: system CPUmax83.3%, own CPUmax4.009077%, private49025024bytes(46.75MiB), working59580416bytes(56.82MiB), availableRAMmin23.078651781822728%.
- 실제 이번 결합에서는 leading90 경고/대기0이었다. 그러므로 이번 성공이 최적화 덕분이라고 단정하거나 PC 프리즈 해결을 주장하지 않는다. 높은 CPU 순서 거부·대기 조건은 별도 합성 계약으로 검증했다.
- 새 post-source metadata executor4개는 현재 두 fresh metadata 읽기로 바인딩했다. 이4개가 기존 Native1625 scope에 포함되었다고 주장하지 않는다. 원 본체 원1599와 P299 full source26개는 원 pin·two-byte·Native identity 조건 그대로 검증한다.
- 원100 수용94/next101을 원 classifier로 재계산하고 원 실패101의 prior와 동일함을 확인. 새 compound는95/next102/잔여154/whole92로 딱 한 번 전진. 실패 본문·부분 source를 원 PASS로 바꾸지 않음.

receipt: `implementation/p09/evidence/locked-r07/p302-case101-leading-metadata-compound-run01.v1.json`
144055 bytes / SHA256 `173d2e27a1b93ee3a2312a61f33298e5e53fd779d04bb2cc59523dad3e0b41d8`.

수용 후 별도 보호된 metadata reader로 원 root/body, 성공 source, 원100 pair·compiled249·1470 catalog·legacy plan, 현재62 source helper/4 post-source metadata helper를 다시 확인하고 typed validator를 재계산했다. 제품 테스트나 full source Native 실행은 반복하지 않았다.

## 다음 단계

새101 exact compound를 anchor로 연결하는 다음 runtime controller와 그 qualification이 필요하다. 다음 미수용 index102부터 한 사례씩 진행하고, 이미 수용된 본체와 전체 입력 검사를 무조건 반복하지 않는다. 다음 실행 중 CPU 보호 STOP이 생기면 해당 phase/코드/표본/정리 증거를 검토한 뒤 근거 있는 최적화만 적용한다.

기존수용·실패·원본/private/P00~P08 및 dirty 변경은 보존. 접근허용/한글/빌드/Git/OS·Defender/WSL 설정 변경 없음. 목표는 ACTIVE이며 P09 Gate가 권위 있게 닫히기 전 P10으로 넘어가지 않는다.
