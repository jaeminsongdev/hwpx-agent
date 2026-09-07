# P17 current workspace source qualification v30

Date: 2026-09-07

Scope: P06-04 active-document binding and pre-save semantic guard successor only

Decision: **qualified source fix only; diagnostic attempt03, actual retry, P06-04/P06-05 card,
phase, production and product PASS remain false**

The v1-v29 contracts remain byte-for-byte unchanged. This v30 layer composes exact v29 contract
SHA-256 `bf18ccec5be200cda7a4c00cabe68741adf0e5c01a38d6977bb570fa88299876`
and advances the source view to clean commit
`7c49beffa8776e99f3eae9ada0c6f70a5ea2f0e3`.

Current-host source acceptance run `c293904577104418951d7370aa0ccbc1` passed all 11 checks. Its
canonical receipt SHA-256 is
`f40470ea4951d4b16dfeaa14aceb120d51914653f0bd25dbf2b8dfae17beb741`. The twenty-six cumulative
successors, locked/offline 25-member Cargo projection and all false runtime/production claims remain
exactly preserved.

Diagnostic source attempt03 successfully invoked table and style actions but saved a different,
blank `IXHwpDocument`; its exact HWPX had no table or markers and the run failed closed before PDF.
The five bound source files now call `SetActive_XHwpDocument()` immediately after creating the
target document and require all four markers from that active document before `SaveAs`. A trace
records the active binding and pre-save canonical text SHA without raw content. The same marker gate
runs after reopen.

The PowerShell readback static suite passes 17/17, the table-cell-style contract validator passes,
its negative tests pass 4/4 and the complete P06 Python suite passes 33/33. This source qualification
does not claim that corrected attempt04 has executed. That licensed Hangul 2020 run still requires
the user's visible file-access approval, followed by exact HWPX/PDF/trace inspection and the
product-generated style readback chain.
