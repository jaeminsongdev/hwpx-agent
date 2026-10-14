# P09 제품 완료 창 중단과 제한된 worker 진단

공식승인은153/249·잔여96·next160·generation48이며 P09/A12/A13은 OPEN이다. 초기qualified입력 읽기와 실제함수환경 연결을 수정했지만 새run006은독립제품승인까지통과하지 않았다. 원실패와 성공run004는보존한다.

## 실제 실행 중단

run006은STOPPED_NOT_ACCEPTED/STOP_STRICT_PRODUCT_WINDOW로445.66초에종료됐다. 원15초창의마지막검사는15.0273502초였다. GO쓰기1회·capture1회였으나 완전한제품결과는없었다. product_body_observed=False이며 actual_product_child_executed는null이므로 실제제품child실행여부를확정하지않는다.

Native frame은CLOSED·완료바이트경계1개·잔여잠금핸들0이다. 초기입력목록은283개로원qualified테스트읽기를포함한다. cleanup/owned_tree_empty=True이다. 시스템CPU최대58.86%·부모CPU최대2.1342918%·가용RAM최소39.2245594%였다. Job관찰에서python.exe와conhost.exe만나타났고 Rust프로세스는관찰되지않았다. 관찰간격 사이의실행까지부정하는증거는아니다. 원본3550322bytes/SHA256 626b59716a1bb06a26d8aaa9b0d5912d2d3d80cf86fecde9d1d12e9a6cc674843이다.

## 제품을 실행하지 않는 진단

probe_case160_worker_startup.py는원GO/Job/worker 경로를실행하되 최종Rust subprocess.call을진단sink로가로챘다. child진입·controller import·bounded graph·template·product call가로채기·완료의모든단계가3.0812102초에통과했다. stdout232bytes·stderr0·시스템CPU32.81%·가용RAM37.3556087%·cleanupTrue이다. 이PASS는실제제품이나Native입력잠금의PASS가아니다.

probe_case160_cli_no_go.py는실제CLI entrypoint와task로소유Job 안에서시작했으며 GO를보내지않았다.3.0698715초에원WORKER_NOT_AUTHORIZED로거부돼보호조건을확인했다. 시스템CPU20.86%·가용RAM37.3742321%·cleanupTrue이며 제품/Native는실행하지않았다.

## 남은 원인 확인

실행초기화가항상15초를넘는다는가설은두진단에서재현되지않았다. 실제실행과진단의명령·GO전달·Native파일잠금 조건차이를다음에확인한다. 타임아웃을늘리거나조건을제거하거나같은run006을자동재시도하지않는다. 기존source scope·checker·600/720·15초·Job/CPU/RAM 보호는유지한다. 접근허용·OS변경·외부종료·삭제이동·원격push는없고 PCfreeze해결은미증명이다.
