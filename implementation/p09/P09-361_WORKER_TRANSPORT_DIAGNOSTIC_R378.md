# P09 worker 전달 경로의 제한된 비교 진단

공식승인은153/249·잔여96·next160·generation48이고 P09/A12/A13은 OPEN이다. 이번작업은제품을재실행하지않는진단이며 원run006의15초중단을해결했다고주장하지않는다.

## 실제명령과 잠금부분집합

probe_case160_cli_held_no_go.py는실제worker명령처럼 -B없이CLI를시작하고, run006초기목록의Python소스와새config/manifest/capsule217개를원FILE_SHARE_READ로잡았다. 기존소유Job/CPU/RAM보호와15초진단한도에서 GO를보내지않아원WORKER_NOT_AUTHORIZED로거부됐다. 입력읽기와잠금시간을포함한전체진단은37.7411467초, 시스템CPU36.79%·가용RAM42.4201991%·cleanupTrue이다.

이는전체Native frame이나제품scope의검증이아니다. 전체검사범위를줄여제품PASS를얻은것도아니다. 단순소스잠금이나CLI초기화가항상15초를넘는현상은이부분집합에서재현되지않았다.

## 원15초창과 GO래퍼

probe_case160_strict_worker_startup.py는원strict_product_window_v1.connect의Popen·stdin·Capture를함께사용하며 최종Rust호출만sink로가로챘다. 첫r378은15초진단timeout/cleanupFalse로끝났고 그기록을보존했다. 사후프로세스조회에서는해당worker잔여가없었다.

진단cleanup이만료된window의communicate를재호출하면서 self.progress로재진입하는문제를수정했다. Cleanup은capture.close후bounded buffer만읽어시간guard를다시통과하려하지않는다. 제품시간제한이나원window코드는변경하지않았다.

수정후r378-run002는child진입/import/bounded graph/template/제품호출가로채기/완료를모두확인했다. 총3.0715079초, 실제GO→완전capture1.5041574초<원15초, GO1·capture1·stdin닫힘True·cleanupTrue였다. 시스템CPU9.41%·가용RAM46.2555945%이다. 이PASS는진단이며Rust제품과Native는실행하지않았다.

## 현재판단과 다음작업

첫진단의중단은발생했지만 동일한연결의후속진단은통과했다. 따라서앞선중간설명의래퍼쪽재현은항상재현되는원인확정이아니다. 실제명령·Job·GO전달·capture·잠금의결합에서간헐적중단이생기는차이를계속확인해야한다. 첫실패나cleanupFalse를후속PASS로대체하지않는다.

현재production controller·checker·source범위·15/600/720·자원보호는변경하지않았다. 같은run006자동재실행·접근허용·OS변경·외부종료·삭제이동·원격push는없고 PCfreeze해결은미증명이다.
