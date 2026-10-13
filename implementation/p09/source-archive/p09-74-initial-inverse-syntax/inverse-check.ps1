$ErrorActionPreference='Stop'
$taskPaths=@('crates/hwpx-package/src/document_import/structure.rs','crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/fields.rs','crates/hwpx-package/src/document_import/fields/semantics.rs','crates/hwpx-package/src/note_hwpx.rs','crates/product-cli/src/form_stored_provider/actual_import.rs','crates/product-cli/src/form_value_operation/full_document.rs','crates/product-cli/tests/form_stored_provider/actual_import.rs')
$taskChecks=@()
foreach($taskPath in $taskPaths){
 $taskArchive='implementation/p09/source-archive/p09-74-pre-source-notes/'+$taskPath
 $taskText=[IO.File]::ReadAllText((Join-Path (Get-Location).Path $taskPath))
 $taskOriginal=[IO.File]::ReadAllText((Join-Path (Get-Location).Path $taskArchive))
 switch($taskPath){
 'crates/hwpx-package/src/document_import/structure.rs' {
  $taskText=[regex]::Replace($taskText,'pub mod notes;\r?\n','')
  foreach($taskPattern in @(
   '    notes: Vec<notes::ImportedNoteObservation>,\r?\n',
   '        notes::finish_notes\(&source, &mut draft, &mapper.note_observations\)\?;\r?\n',
   '        draft.notes = std::mem::take\(&mut mapper.notes\);\r?\n',
   '        let notes = std::mem::take\(&mut mapper.note_observations\);\r?\n',
   '            notes,\r?\n',
   '(?s)    #\[must_use\]\r?\n    pub fn notes\(&self\) -> &\[notes::ImportedNoteObservation\] \{.*?\r?\n    \}\r?\n\r?\n',
   '    notes: Vec<domain_ir::Note>,\r?\n',
   '    note_observations: Vec<notes::ImportedNoteObservation>,\r?\n',
   '            notes: Vec::new\(\),\r?\n',
   '            note_observations: Vec::new\(\),\r?\n',
   '(?s)        if self.note_wrapper\(part, index, depth, inlines, attached\)\? \{.*?\r?\n        \}\r?\n',
   '    #\[error\("structure import note source envelope rejected: \{code\}"\)\]\r?\n    Note \{ code: &''static str \},\r?\n'
  )){$taskText=[regex]::Replace($taskText,$taskPattern,'')}
 }
 'crates/hwpx-package/src/document_import/forms.rs' {
  $taskText=[regex]::Replace($taskText,'(?s)        for note in &mut draft.notes \{\r?\n            replace_forms\(.*?\r?\n        \}\r?\n','')
  $taskText=[regex]::Replace($taskText,'(?s)\r?\n    #\[must_use\]\r?\n    pub fn notes\(&self\) -> &\[super::structure::notes::ImportedNoteObservation\] \{.*?\r?\n    \}\r?\n,'')
 }
 'crates/hwpx-package/src/document_import/fields.rs' {
  $taskStart=$taskText.IndexOf('        let mut draft = forms.graph().clone().into_draft();')
  $taskEnd=$taskText.IndexOf('        let mut replacements = BTreeMap::new();',$taskStart)
  $taskOldStart=$taskOriginal.IndexOf('        let fields = collected.finish()?;')
  $taskOldEnd=$taskOriginal.IndexOf('        let mut replacements = BTreeMap::new();',$taskOldStart)
  $taskText=$taskText.Remove($taskStart,$taskEnd-$taskStart).Insert($taskStart,$taskOriginal.Substring($taskOldStart,$taskOldEnd-$taskOldStart))
  $taskText=[regex]::Replace($taskText,'(?s)        for note in &mut draft.notes \{\r?\n            replace_fields\(.*?\r?\n        \}\r?\n','')
 }
 'crates/hwpx-package/src/document_import/fields/semantics.rs' {
  $taskStart=$taskText.IndexOf('        let by_id:')
  $taskEnd=$taskText.IndexOf('            reference.properties.insert(',$taskStart)
  $taskOldStart=$taskOriginal.IndexOf('        for (reference, observation)')
  $taskOldEnd=$taskOriginal.IndexOf('            reference.properties.insert(',$taskOldStart)
  $taskText=$taskText.Remove($taskStart,$taskEnd-$taskStart).Insert($taskStart,$taskOriginal.Substring($taskOldStart,$taskOldEnd-$taskOldStart))
  $taskText=[regex]::Replace($taskText,'(?s)        for note in &mut draft.notes \{\r?\n            attach_meanings\(.*?\r?\n        \}\r?\n','')
 }
 'crates/hwpx-package/src/note_hwpx.rs' {
  $taskStart=$taskText.IndexOf('pub(crate) struct ImportedNoteEnvelope')
  $taskEnd=$taskText.IndexOf('fn note_projection(',$taskStart)
  if($taskStart-lt0-or$taskEnd-lt$taskStart){throw 'missing source-only note envelope'}
  $taskText=$taskText.Remove($taskStart,$taskEnd-$taskStart)
 }
 'crates/product-cli/src/form_stored_provider/actual_import.rs' {
  $taskText=[regex]::Replace($taskText,'(?s)    #\[must_use\]\r?\n    pub fn notes\(.*?\r?\n    \}\r?\n','')
 }
 'crates/product-cli/src/form_value_operation/full_document.rs' {
  $taskMarker=$taskText.IndexOf('"note_import_profile"')
  $taskStart=$taskText.LastIndexOf('        if draft.metadata',$taskMarker)
  $taskEnd=$taskText.IndexOf('        if draft.security_state.protected',$taskMarker)
  if($taskStart-lt0-or$taskEnd-lt$taskStart){throw 'missing additive note guard'}
  $taskText=$taskText.Remove($taskStart,$taskEnd-$taskStart)
 }
 'crates/product-cli/tests/form_stored_provider/actual_import.rs' {
  $taskText=[regex]::Replace($taskText,'#\[path = "actual_import/source_notes.rs"\]\r?\nmod source_notes;\r?\n','')
 }
 }
 $taskRaw=[Text.UTF8Encoding]::new($false).GetBytes($taskText)
 $taskSha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskRaw)).ToLowerInvariant()
 $taskOld=Get-Item -LiteralPath $taskArchive
 if($taskRaw.Length-ne$taskOld.Length-or$taskSha-ne(Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant()){throw "whole pre-change inverse differs: $taskPath"}
 $taskChecks+=[ordered]@{path=$taskPath;original_bytes=$taskOld.Length;original_sha256=$taskSha;whole_pre_change_inverse_exact=$true}
}
$taskChecks|ConvertTo-Json -Depth 5
