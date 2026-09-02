# P03-01 Bounded ZIP policy

P03-01은 HWPX package를 추출하지 않고 `Read + Seek` source에서 읽는 fail-closed 경계다. 사용자 문서나 source artifact를 수정하지 않으며, entry bytes는 metadata·streamed size·decompression·CRC·nested-package 검사가 모두 끝난 뒤에만 `Vec<u8>`로 반환한다.

## Supported profile

| 항목 | 정책 |
|---|---|
| ZIP layout | classic single-disk ZIP only; offset 0부터 local records, contiguous central directory, EOCD가 source 끝이어야 함 |
| Compression | Stored(0), Deflate(8)만 허용 |
| Encoding | entry name의 raw bytes가 strict UTF-8이어야 함 |
| Encryption | traditional/AES/strong encryption 모두 거부 |
| Extensions | ZIP64, data descriptor, multi-disk, symlink/special file, preamble/trailing/unknown records 거부 |
| Integrity | central/local name·flags·method·CRC·compressed/expanded size·offset 일치, range non-overlap, streamed length와 CRC 확인 |
| Path | absolute, `.`/`..`, empty component, backslash, control/NUL, colon/ADS, trailing dot/space, Windows reserved name 거부 |
| Collision | NFC 정규화 후 Unicode default case folding, 다시 NFC 정규화한 key로 duplicate/collision 거부 |
| Nesting | archive/document extension과 ZIP/OLE signature를 거부 |
| Publication | filesystem extraction API 없음; 실패 중 읽은 partial bytes는 caller에게 반환하지 않음 |

ZIP64와 data descriptor는 해당 형식 자체가 무조건 위험해서가 아니라, current HWPX bounded profile에서 필요한 크기보다 넓고 local/central metadata의 사전 upper-bound 검증을 약화하기 때문에 명시적으로 지원하지 않는다. 지원 확대는 새 profile과 malicious regression corpus 없이는 허용하지 않는다.

## Finite limits

| Limit | Default | Hard ceiling |
|---|---:|---:|
| archive bytes | 512 MiB | 2 GiB |
| entries | 4,096 | 16,384 |
| name bytes | 1,024 | 4,096 |
| path depth | 64 | 256 |
| local/central extra bytes | 16 KiB | 65,535 |
| archive/entry comment bytes | 4 KiB | 65,535 |
| one expanded entry | 128 MiB | 512 MiB |
| total expanded bytes | 1 GiB | 4 GiB |
| compression ratio | 200:1 | 1,000:1 |

`PackageLimits::new`은 0, hard ceiling 초과, entry limit이 total limit보다 큰 설정을 거부한다. metadata의 checked arithmetic와 upper bound 검사가 allocation보다 먼저 수행되며, metadata와 output buffer는 fallible exact reservation을 사용한다.

## Dependency boundary

`zip = 8.6.0`을 exact pin하고 default features를 끈 뒤 `deflate-flate2-zlib-rs`만 활성화한다. `zip` crate는 central directory parsing, Deflate와 CRC primitive에만 사용한다. product policy와 local/central cross-check는 `hwpx-package`가 소유하며, `zip::ZipArchive::extract*`는 사용하거나 노출하지 않는다.

## Negative evidence contract

`PackageError::code()`는 untrusted entry name이나 local path를 포함하지 않는 stable code를 제공한다. Synthetic corpus는 archive/entry/size/ratio limits, unsafe path, UTF-8, normalization/casefold collision, encryption/method/flags, ZIP64/multi-disk/descriptor, preamble/trailing, overlap/header mismatch, CRC, nesting, symlink, directory/index와 반복 rejection을 포함한다.
