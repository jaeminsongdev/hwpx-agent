# 라이선스·법무 체크리스트

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


- [ ] 한/글 desktop 제품의 설치/동시 실행/VM/서버 사용 조건 확인.
- [ ] HWP Automation 상업 이용 승인·별도 라이선스 문서 확보.
- [ ] WebHWP SDK/API 계약과 사용자/서버 수량, 도메인, 재배포 조건.
- [ ] 공식 manual/XSD/PDF를 내부 build pipeline에 저장·파싱할 권리.
- [ ] font 설치·서버 렌더·embedding 권리.
- [ ] template/fixture/source document 저작권과 개인정보.
- [ ] PDF/DOCX/DAISY/점자/전자서명 등 외부 component/provider license.
- [ ] OpenAI plugin 제출용 privacy/terms/support/domain ownership.
- [ ] 사용자 문서 처리 목적, retention, 삭제, data residency.
- [ ] telemetry에 문서 내용·파일명·암호가 남지 않는지.
- [ ] third-party open-source SBOM/notice/copyleft 의무.

법무 상태는 `approved|restricted|pending|denied`로 registry에 넣고 `pending/denied` backend는 production route에서 제외한다.
