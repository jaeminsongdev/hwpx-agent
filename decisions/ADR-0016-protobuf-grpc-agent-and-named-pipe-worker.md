# ADR-0016 — Protobuf/gRPC Control Plane, Named-pipe Local Worker

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 결정

Rust control plane과 Windows Agent는 versioned protobuf/gRPC 계약을 사용한다. Agent와 같은 host의 STA worker는 인증된 named pipe로 같은 protobuf message를 교환한다. binary 문서는 RPC body가 아니라 staged artifact reference로 전달한다.

## 이유

Rust/C# code generation, schema compatibility 검사, streaming job/event, 명확한 timeout/cancellation, 대형 파일 분리를 동시에 만족한다.

## 결과

- protocol breaking change는 Buf/compatibility gate를 통과해야 한다.
- worker는 public inbound endpoint를 열지 않는다.
- local Codex bridge도 가능한 한 같은 semantic protocol을 재사용한다.
