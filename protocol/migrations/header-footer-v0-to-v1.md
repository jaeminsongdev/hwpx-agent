# Header/Footer Contract Migration v0 to v1

## Contract

- New contract ID: `hwpx-agent.header-footer/1`
- Previous typed contract: none (`v0` raw/unmodeled section controls)
- Owner: `crates/hwpx-package`

## Breaking boundary

`v1`은 raw XML 문자열이나 backend action 문자열을 입력으로 받지 않는다. 호출자는 다음 typed value를 제공해야 한다.

- `HeaderFooterDefinition`과 `HeaderFooterBody`
- `PageField`의 `PAGE | TOTAL_PAGE`
- `PageNumberRestart`, `FirstPageVisibility`, `PageNumberPlacement`
- `MasterPageDefinition`과 section의 ordered master-page references

알 수 없는 field, 잘못된 namespace, 중복 variant/ID, dangling master-page link는 보존 가능한 것으로 추측하지 않고 안정 오류코드로 실패한다.

## Upgrade procedure

1. 기존 package를 preservation reader와 `HeaderFooterReader`로 읽는다.
2. 모든 관련 control이 `v1` typed boundary에 들어오는지 확인한다.
3. master-page count, ordered references, provided parts의 exact closure를 검증한다.
4. `HeaderFooterLowerer`의 결과를 같은 reader로 다시 읽어 semantic equality를 확인한다.
5. actual Hancom target profile에서 save/reopen/render evidence를 별도로 기록한다.

## Rollback

승격이나 closure 검증이 실패하면 source package를 수정하지 않는다. 기존 byte는 preservation 경계에 그대로 남고, 호출자는 `header_footer_*` 안정 오류코드와 함께 작업을 중단한다. `v0` raw mutation으로 자동 fallback하지 않는다.
