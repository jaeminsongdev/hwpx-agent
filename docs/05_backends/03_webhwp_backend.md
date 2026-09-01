# WebHWPBackend

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 적용 조건

웹한글 기안기 제품/API 라이선스와 배포 환경이 있는 조직에서만 활성화한다. desktop automation의 완전 대체로 가정하지 않는다.

## adapter

- HwpCtrl lifecycle and document load/save.
- Action/ParameterSet wrapper.
- control enumeration and position APIs.
- event subscription.
- browser/tenant auth and document storage connector.

## capability probe

desktop Action registry를 그대로 재사용하지 않는다. WebHWP의 API 변경 사항과 지원 파일 형식을 기준으로 별도 registry profile을 생성하고, 동일 semantic operation fixture로 conformance를 측정한다.

## 사용 사례

- 사용자가 브라우저에서 문서를 직접 확인·수정해야 하는 기관 workflow.
- server-side direct output을 WebHWP에서 열고 사용자 승인 후 저장.
- remote interactive editor와 project revision 연계.

## 제한

제품/API 버전, 브라우저, 서버 설정, 라이선스에 따라 기능 차이가 있으므로 runtime probe가 실패하면 desktop/direct route로 fallback하거나 명시 실패한다.
