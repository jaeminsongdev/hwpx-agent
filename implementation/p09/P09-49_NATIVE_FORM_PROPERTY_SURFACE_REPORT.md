# P09-49 native form property surface — actual installed declarations, not runtime

Decision: `EXACT INSTALLED 2020 TYPELIB NAME/TAB GET+PUT DECLARATIONS VERIFIED /
PUBLICATION + INDEPENDENT FRESH VERIFICATION PASS / ACTUAL NATIVE WRITE NOT_RUN`.

## New evidence that changes the next action

The official archived HwpAutomation2504 manual47/48/54/57/58 exposes document-owned
edit/radio collections and name/tab properties. ParameterSetTable129 identifies
form parameter sets; ActionTable11 lists form creation actions, NOT executed here.
All three original PDF hashes match P00 source lock. Complete relevant pages were
read and visually reviewed through PDF skill; originals were never edited/exported.

Actual installed Hwp.exe11.0.0.9136/7f009613 and HwpAutomation.dll/edbc7140 are
unchanged before/after read-only inspection. Their standalone typelib loads both
return COMException/HRESULT-2147312566; these failures remain in the receipt, not
called broken native execution. Exact ProgID's read-only Registry32 TypeLib key
points to HwpObject.tlb in the same installed directory. Registered typelib read
SUCCEEDS:473120 bytes/SHAabd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9,
GUID7d2b6f3c-1d95-4e0c-bf5a-5ee564186fbc,1.0,SYS_WIN32,255 types. This is a NEW
observed installed identity, not a fabricated P00 predecessor hash.

Both IXHwpFormEdit and IXHwpFormRadioButton actually declare:

| Literal installed member | DISPID | GET result | PUT argument/result |
|---|---:|---|---|
| name | 3 | BSTR/VT8 | one FIN1 BSTR/VT8; VOID/VT24 |
| TabOrder | 8 | I4/VT3 | one FIN1 I4/VT3; VOID/VT24 |

The manual's Name label is capitalized; installed literal member is lowercase
name. Initial case-sensitive filter therefore missed it. Fixed only new reader
selection, retaining literal actual spelling. Document-owned XHwpDocuments,
IXHwpDocument.XHwpFormEdits/XHwpFormRadioButtons and collection Item/Count getter
declarations were actually verified. This does NOT prove index base/order or
mapping to source native IDs/physical anchors; never guess those from array index.

## Actual validation and receipts

- New PowerShell observer uses LoadTypeLibEx REGKIND_NONE: no typelib registration,
  COM server activation, Hwp.exe creation, document open/set/save or UI actions.
  Existing Hwp.exe PID set and all three binary hashes remain exact. No values,
  machine paths or full errors/logs emitted. No trust/registry/security changes.
- First new reader expansion used wrong C# TLIBATTR spelling; actual run exit2/
  Exception. Correct .NET TYPELIBATTR was verified locally and used; no original
  binary/source edits or dependency installation. EXE/DLL unavailable observations
  and initial missing lowercase selection remain explicitly recorded.
- New6 guards actually PASS/7.847s, using a fresh real installed read in setUpClass,
  exact getter/setter metadata and negative target/type/coercion/missing getter/
  nonwritable/claim/path substitutions. No mocks replace actual native metadata.
- Publication/session61494 TERMINATED exit0/PASS. Receipt:
  `evidence/p09-49-native-form-property-surface.v1.json`,25833 bytes/SHA
  ebd8e94b8826525752f4ce7b0d57ff7a289fa8772bc02e43534b1f3e3d385262,
  9 source pins. Actual installed read+another read in all6 guards, preserved P48
  23 sources/1551 inputs/native originals and raw PDF identities checked before/after.
- Independent fresh COMPLETE --verify/session20853 TERMINATED exit0/PASS,
 25833 bytes/ebd8e94b again, rereading actual typelib/all6 guards and every preserved
 input. Entire canonical result equals publication, not selected field matching.
 All9 source pins now immutable for this receipt; extend via a preserved successor.
- P48 full color successor418689/d68d07c0 publication25529 and independent fresh
  COMPLETE verify17862 actually completed PASS. This observer checks those exact
  source/receipt identities; it does NOT rerun full P48 workflow or replace it.

## Next exact implementation boundary

Build a bounded private native form property application/verification using the
actual declared name and TabOrder setters, after unambiguous document/source native
control identity binding. Protect full other properties/styles/payloads/anchors and
document state; source names and global tab order remain exact requested values.
Do not strip Unicode/metacharacters, relax name/tab uniqueness, substitute Item
index for native identity, fabricate defaults or drop opaque metadata to make PASS.

The actual stored typelib inventory includes IDHwpCtrlCode, while IHwpObject
declares HeadCtrl/LastCtrl/CurSelectedCtrl/ParentCtrl/GetPos/GetPosBySet/FindCtrl.
Those declarations locate the next bounded source investigation; they do NOT yet
prove an anchor/instance-ID getter, runtime position mapping or actual form binding.
Investigate IDHwpCtrlCode and its returned typed metadata before choosing native
selectors. Do not assume CharShapeID is a native object ID or infer index base.

Keep this source surface distinct from an actually applied fix. Combine genuinely
changed ready color/name/tab dependencies into one complete native permission
batch, user-owned clicks only, with save/reopen/semantic/render/differential proof.
No new native session or permission dialog was started here. Signed form route,
manifest/publication/CAS/idempotency/CLI/full import and P09 Gate stay open.
P10 held; goal ACTIVE.
