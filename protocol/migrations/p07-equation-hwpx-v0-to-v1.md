# P07 native equation HWPX v0 to v1

There is no stored v0 native-equation request to rewrite. New callers MUST construct
`hwpx-agent.equation-hwpx/v1` from typed `MathAst`, exact package/source/flow bindings, an explicit
noncolliding object ID, typed style and a provisional extent marked `render_required`.

Migration MUST NOT import raw XML, a raw EqEdit string, HAction/COM names, paths, image fallback or
unbound layout constants. Old native equation bytes stay opaque outside the admitted exact reader
profile. P07-07 estimator receipts and licensed target save/reopen remain separate P07 Gates.
