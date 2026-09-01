# P01 codegen·breaking Gate 결정

## 결정

- protobuf compiler는 `protoc-bin-vendored 3.2.0`, Rust generator는 `prost/prost-build 0.14.4`, C# runtime은 `Google.Protobuf 3.36.1`로 lock한다.
- JSON Schema는 Draft 2020-12 compile validation 후 deterministic TypeScript interface/catalog로 생성한다.
- `cargo run --locked -p xtask -- generate --check`는 generated drift와 `protocol/baseline/contracts.lock.json`의 v1 descriptor/schema-catalog hash를 함께 검사한다.
- v1 source를 고치는 방식의 계약 변경은 실패한다. 새 version, migration note와 negative test를 추가해야 baseline review를 열 수 있다.

## Windows 한글 경로

Windows `protoc`가 `D:\개발` 같은 비 ASCII 경로를 손상시키는 현상을 재현했다. repository를 이동하지 않고 ASCII user temp에서 native codegen을 수행하고 Rust filesystem API로 generated output만 게시한다. temp 경로가 ASCII가 아니거나 쓸 수 없으면 fail-closed한다.

## Buf 범위

P01의 단일 foundation proto는 immutable v1 hash Gate가 breaking change를 더 엄격하게 차단한다. 여러 protocol module/version이 생기는 phase에서 Buf rule 기반 source compatibility를 추가할 수 있지만, 그 전에도 현재 Gate를 약화하거나 baseline hash를 자동 갱신하지 않는다.
