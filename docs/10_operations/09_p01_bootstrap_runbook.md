# P01 개발 환경 부트스트랩

> 범위: 현재 PC 로컬 core 개발. 한글 UI·사용자 문서·다른 버전·production provider를 실행하지 않는다.

## 고정 도구

`toolchains.lock.json`이 Rust 1.96.0, .NET SDK 10.0.300, Node 24.16.0, pnpm 11.19.0, Python validator와 protobuf/security 도구 버전을 고정한다. `rust-toolchain.toml`, `global.json`, `package.json`, Python requirements가 실행기별 fail-closed lock이다.

## 단일 명령

Windows PowerShell에서 저장소 루트 기준으로 실행한다.

```powershell
.\tools\bootstrap.ps1
```

이 명령은 도구 버전, Rust core, protobuf/JSON Schema drift, C# Windows semantic worker, TypeScript widget, 설계/fixture/docs, SBOM/license/vulnerability/secret scan을 순서대로 검증한다. 한 단계라도 실패하면 종료 코드가 0이 아니다.

Linux에서는 Windows worker lane을 제외하고 다음을 실행한다.

```sh
./tools/bootstrap.sh
```

## 생성 계약

```powershell
cargo run --locked -p xtask -- generate
cargo run --locked -p xtask -- generate --check
```

source는 `protocol/proto`와 `protocol/json-schema`, generated output은 `protocol/generated`다. generated 파일을 직접 수정하지 않는다. breaking change는 source 계약·migration·negative test와 함께 제출한다.

## 보안·fixture 규칙

- `fixtures/synthetic`에는 재현 가능한 synthetic 파일만 커밋한다.
- `fixtures/licensed-private`와 `fixtures/target-build`의 실제 binary/user document는 Git에 넣지 않는다.
- 모든 fixture manifest에는 provenance, license, privacy, path, size, SHA-256이 필요하다.
- 작업 산출물은 secure workdir의 staging에서 checksum 확인 후 output 또는 quarantine으로 원자 이동한다.
- 로그에는 본문, password, token, signed URL, 이메일, 전화번호, 원본 binary를 기록하지 않는다.

## 실제 한글 lane

P01 core bootstrap은 한글 설치 여부와 독립적이다. 현재 PC exact 한글 2020 oracle 증거는 P00 bundle을 유지하며, P10 이전에는 P01 CI가 Automation/COM을 호출하지 않는다. 다른 버전과 production 상태는 계속 `unverified`/`disabled`다.
