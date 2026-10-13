# r03 raw-byte diagnostic verification correction

Preserve original r02 receipt48539d43.../15627 and every pinned r02 source unchanged.
r02 fresh CLI verification failed TypeError: raw bytes were passed to JSON exact()
which accepts JSON-serializable values. That is a verifier implementation error,
not native/old source authority/evidence PASS. Demonstrate and retain this failure.

r03 separately reruns ENTIRE frozen r02 preflight, compares whole canonical raw
bytes with the original receipt, rechecks every old pin and pins three new sources
before/after. Fresh --verify reruns all work and uses strict bytes-only equality;
missing/extra/type/changed bytes reject. Never suppress a failure, refresh old pins,
weaken original native binder checks or treat hash/local checks as full proof.

Native binding reuses unchanged r02 full15-case binder/current admission and all
original strict lifecycle/artifact/public reader/projection checks. All r02 limits,
diagnostic-only scope, human-click-only rule, whole sequential batch, preservation
and non-green/full-source/Gate boundaries remain binding. Fixed separate r03 files
are written exclusively; no original overwrite, trust change, automated permission
click, process kill or unrelated change. No P10 before authoritative P09 Gate.
