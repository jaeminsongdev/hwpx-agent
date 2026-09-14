# P08 object hyperlink target route v0 to v1

There is no accepted v0 target-route policy. P08-16 introduces the first exact current-PC policy
for `obj.object_hyperlink`.

The v1 route admits the existing preserving direct-HWPX adapter only for picture, basic shape,
text box, drawing canvas and embedded object. Chart returns
`CAPABILITY_UNAVAILABLE_FOR_TARGET`; form object and paragraph band are outside this capability's
catalogued IR. A rejected direct preflight fails closed and never widens to the dialog-mediated
desktop surface. No failure path emits a partial output or executes a fallback.

The exact target identity is Hangul 2020 build `11.0.0.9136`, x86, ko-KR and the pinned executable
digest. Other builds, architectures, locales and executable digests fail before routing.
