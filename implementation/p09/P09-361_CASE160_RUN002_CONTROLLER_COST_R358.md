# P09 run002 controller 검증과 비용 최적화

run002의 새controller V29와DATA037을 연결하고18개 controller 검사를 통과했다. 전체preflight는decoder 비용을 포함한600초 기준에서 거부됐으므로 실행 자격은 아직 없다. 원 비용을 진단한 뒤 원본을 보존하는131번 lossless 표현을 추가했다. 공식 승인 수는153/249, 잔여 개별 사례는96개다.

## 실제 controller 연결

기존V28과 모든 기존·신규 raw helper source를 private namespace로 보존했다. 원 함수의metadata 역변환, 단일physical run002 identity, bounded bootstrap,25쌍 sharedBinding과 선언 재사용, 전체oracle 및 원래engine·worker 본문을 유지한다. 이미import한 모듈을 숨기거나helper64개 상한을 늘리지 않는다.

r798에서 기존14개와 추가4개를 합한18개 검사가 모두 통과했다. 실제engine·frame·worker 호출은0회다. fresh·최종 hash53개가 일치했고cleanup은true였다. 시스템CPU 최대 관측값은14.44%, 최소가용RAM은51.80887%였다.

DATA037은 실제step·authority·prior runtime·manifest026·capsule002·CODE18·전체Binding 증거의 정확한pin을 연결한다. 기존DATA036과run001은 보존했다.

## 전체 preflight의 비용 거부

원래전체preflight037은 `ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5`로 실패했다. Native·제품은 시작하지 않았다. 준비입력1,106개를 확인했지만 최종fresh는0개이며 전체preflight 통과로 승격하지 않는다.

해당실행은226.93848초였고 시스템CPU 최대 관측값은32.31%, 최소가용RAM은51.86300%, cleanup은true였다. 이번중단은CPU 보호가 아니라비용 기준 거부다.

## 원 비용 진단과 표현 최적화

r799는 원래Binding budget함수와600초 거부조건을 그대로 실행하면서 비용을 관측했다. 공유decoder5초를 포함한 예상비용은600.326911354초다. 진단용source 입력이 포함된 별도scope의 수치이며, 실패한preflight의 숨겨진정확한값과 같다고 주장하지 않는다. 진단의fresh·최종 hash1,107개가 모두 일치했다.

원scope 안에서 아직표현을 적용하지 않은 역사결과를 확인하고 가장큰131번 원본을 선택했다. 실제이전159 semantic scope에 같은pin이 포함됨을 확인했다. r800에서2,499,193byte 원본을644,411byte 표현으로 저장하고 두번복원해 정확한원본byte와 같음을 검증했다. 표현차이는1,854,782byte이며 원본은삭제·덮어쓰기하지 않았다.

기존CODE13 writer의2MiB/s 제한, exclusive생성과fsync를 유지했다. fresh·최종 hash23개가 일치했고cleanup은true였다. 시스템CPU 최대 관측값은31.87%, 최소가용RAM은50.39740%였다.

## 다음 실제 실행 조건

131번 표현을 새manifest·capsule·controller·DATA의 실제scope에 채택하고 전체비용·preflight를 다시검증해야 한다. 기존600초Native·공유decoder5초와전체720초metadata 기준을유지한다. 단순 byte차이만으로 새scope가 비용기준을 통과했다고 판단하지 않는다.

원preflight037 실패, 권위153·성공159·실패160과 사용자변경을 보존했다. 제품재실행·큐승인은하지 않았다. P09, A12, A13은OPEN이며 P10 새구현은0이다. 프리즈해결을 주장하지 않고 접근허용·UAC·OS설정변경·외부프로세스종료·원본삭제와이동·원격push도 수행하지 않았다.
