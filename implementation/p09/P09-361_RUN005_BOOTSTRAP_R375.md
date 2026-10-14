# P09 초기 입력 읽기 복원과 별도 실행 준비

공식 승인은153/249, 잔여96개, next160, generation48이다. run004 제품실행 성공과 독립검사 거부는 보존한다. 새run005는 원독립checker의 BOOTSTRAP_CONTROLLER 조건을 변경하지 않고 초기qualified pin 읽기를 복원했다. P09/A12/A13은 OPEN이며 P10은 시작하지 않았다.

case160_run005_controller.py는 exact pinned run004 controller의 전체함수와 원engine·worker·oracle 본체를 유지하고, 명시적metadata inverse 검사로 task/root/physicalrun/사전검사 목적지를 바꾼다. 초기입력에서 원CODE_PINS/native.SOURCES의 실제byte pin을 확인한 뒤 현재admission을 호출한다. 이전에 누락됐던 test_case112_current_stored_runtime.py와 test_current_stored_native_bridge.py도 실제초기목록에 들어간다. 기존결과나 bootstrap 목록은 사후수정하지 않는다.

새manifest031은587bytes, capsule008은12008bytes로 원34쌍 및16384bytes 한도를 유지한다. 기존manifest·역사적물리4 준비는 새물리5 준비로 재표시하지 않는다. 새config는 명시적5/160/before153과 두실제byte pin만 허용한다. 같은boundedReader로 원선언과 새선언을 읽으며 원64reads/262144bytes 한도를 유지한다.

원22개단위검사의 본체를 유지하고 identity·bounded읽기개수 metadata만 명시적으로 투영한 뒤3개계약을 추가했다. CODE25와 실제연결검사는 fresh101/final101·helper62·시스템CPU41.34%·부모CPU1.2382414%·가용RAM41.6971959%·cleanupTrue로 통과했다. qualifier는 제품/Native/독립현재160oracle 승인이 아니다.

새DATA042/preflight042 전체검사는 선언2885개, 실제fresh284/final284, import64, 135.7113891초, 예상전체runtime598.5220282초<원600, 시스템CPU65.24%·가용RAM36.8995739%·cleanupTrue로 통과했다. 원scope·Native600/shared720·margin60/decoder5·속도·두바이트경계·자원보호는 유지한다. 이후 단일run005와 실제성공candidate의 독립검사가 모두통과해야 공식승인을 진행한다. 접근허용·OS변경·외부종료·삭제이동·원격push는 없고 PCfreeze해결은 미증명이다.
