# 보안·퍼징 테스트

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 공격면

- ZIP bomb, deep nesting, duplicate names, path traversal, symlink.
- XML entity/DTD, quadratic expansion, namespace tricks.
- broken relationships, huge IDs, cyclic references.
- malformed image/OLE/media/chart data.
- script/macro and external URL.
- password/protection/signature edge cases.
- automation action injection and modal dialog DoS.
- signed URL leakage, tenant confusion, stale ACL.

## fuzz targets

- package indexer.
- XML parser and preserving token layer.
- relationship graph.
- style/numbering/table/equation parsers.
- selector and operation validator.
- action/parameter binding decoder.
- export filename and temp path.

## limits

uncompressed size, compression ratio, part count, XML depth, attribute count, text length, image pixels, table dimensions, equation depth, pages/render time에 hard limit을 둔다. tenant별 override는 admin policy로만 가능.

## automation isolation

- disposable worker session/VM.
- no ambient user profile documents.
- outbound network default deny.
- allowlisted file path module/registry controlled image.
- unexpected modal detector and kill/recycle.
- crash dump secret redaction.

## release gate

critical path traversal/RCE/tenant leakage/credential logging은 0건. unresolved high severity는 release 금지.
