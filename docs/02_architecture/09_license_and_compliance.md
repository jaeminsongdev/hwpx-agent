# 라이선스·법적·배포 준수

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 한/글 오토메이션

한컴 공식 개발자 안내는 비상업적 개인 이용과 상업적 솔루션 이용을 구분하며, 상업 목적에는 별도 승인을 요구한다. 따라서 다음은 P00/production hard gate다.

- 사용 목적과 배포 형태를 한컴에 확인.
- 서버/VM/동시 사용자/워커 수/클라우드 배포 권한을 계약서에 명시.
- 한/글 프로그램 및 폰트 라이선스 수량 관리.
- WebHWP 사용 시 별도 제품/API 라이선스와 지원 범위 확인.
- 공식 보안 승인 모듈 사용 조건과 배포 권한 확인.

## 문서·fixture

- 실제 학교/기관 양식은 비공개 fixture vault에 저장하고 공개 repo에 포함하지 않는다.
- 개인정보가 있는 문서는 synthetic replacement 후 golden corpus로 승격한다.
- 폰트 파일과 유료 이미지·클립아트는 artifact에 재배포하지 않는다.

## OpenAI plugin

privacy policy, terms, support contact, auth disclosure, data retention, deletion request, tool annotations, public endpoint security를 release checklist에 포함한다.
