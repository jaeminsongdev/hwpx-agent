//! First insertion with typed parameters observed in the immutable010 corpus.
//! Captured-format compatibility is NOT Native evaluation or service authority.
use super::*;

pub const PARAMETER_PROFILE: &str = "hwpx-agent.bookmark-crossref-envelope/captured010-v1";
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SourceBookmarkCreationReceipt {
    pub profile: &'static str,
    pub parameter_profile: &'static str,
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub source_run_sha256: [u8; 32],
    pub command_sha256: [u8; 32],
    pub original_fields: usize,
    pub inserted_fields: usize,
    pub requires_existing_crossref_envelope: bool,
    pub inserted_parameter_envelope_readback_verified: bool,
    pub outside_insertions_exact: bool,
    pub original_selected_run_exact: bool,
    pub existing_display_text_is_not_evaluated_or_refreshed: bool,
    pub native_currentness_execution_or_publication_qualified: bool,
}
pub struct SourceBookmarkCreationCandidate {
    artifact: PackageArtifact,
    receipt: SourceBookmarkCreationReceipt,
}
impl fmt::Debug for SourceBookmarkCreationCandidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceBookmarkCreationCandidate(<redacted>; inert)")
    }
}
impl SourceBookmarkCreationCandidate {
    #[must_use]
    pub const fn receipt(&self) -> &SourceBookmarkCreationReceipt {
        &self.receipt
    }
    /// # Errors
    /// Integrity of an inert candidate, not authorization to store or execute.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}
impl ImportedDocumentFields<'_> {
    /// A NEW range without requiring an existing CROSSREF in the document.
    /// The actual source target and selected run are still required. Existing
    /// text is preserved, not falsely labeled a computed/Native field result.
    /// # Errors
    /// All original whole-source/protection/ID/preservation/readback guards and
    /// finite limits remain; unsupported target/display combinations reject.
    pub fn create_bookmark_reference(
        &self,
        proof: &VerifiedFormReconstruction<'_>,
        request: SourceBookmarkInsertion<'_>,
        limits: ReferenceAuxiliaryLimits,
        writer: WriterLimits,
    ) -> Result<SourceBookmarkCreationCandidate, E> {
        let out = self.lower_bookmark_reference(
            proof,
            request,
            limits,
            writer,
            EnvelopePolicy::Generated,
        )?;
        if out.source_envelope_sha256.is_some() {
            return Err(E::Source);
        }
        let receipt = SourceBookmarkCreationReceipt {
            profile: "hwpx-agent.source-bookmark-first-insertion/captured-parameters-v1",
            parameter_profile: PARAMETER_PROFILE,
            source_package_sha256: out.source_package_sha256,
            output_package_sha256: out.artifact.sha256(),
            source_run_sha256: out.source_run_sha256,
            command_sha256: out.command_sha256,
            original_fields: out.original_fields,
            inserted_fields: 1,
            requires_existing_crossref_envelope: false,
            inserted_parameter_envelope_readback_verified: true,
            outside_insertions_exact: true,
            original_selected_run_exact: true,
            existing_display_text_is_not_evaluated_or_refreshed: true,
            native_currentness_execution_or_publication_qualified: false,
        };
        let _ = super::super::semantics::source_index::bounded_digest(
            &receipt,
            limits.config().output_bytes,
        )
        .map_err(|_| E::Limit)?;
        Ok(SourceBookmarkCreationCandidate {
            artifact: out.artifact,
            receipt,
        })
    }
}
fn content_type(display: SdkCrossReferenceDisplay) -> Result<&'static str, E> {
    match display {
        SdkCrossReferenceDisplay::Page => Ok("OBJECT_TYPE_PAGE"),
        SdkCrossReferenceDisplay::BookmarkName => Ok("OBJECT_TYPE_NUMBER"),
        SdkCrossReferenceDisplay::Content => Ok("OBJECT_TYPE_CONTENTS"),
        SdkCrossReferenceDisplay::RelativePosition => Ok("OBJECT_TYPE_UPDOWNPOS"),
        SdkCrossReferenceDisplay::ObjectNumber => Err(E::Target),
    }
}
fn parameters<'a>(
    command: &'a str,
    display: SdkCrossReferenceDisplay,
    hyperlink: bool,
) -> Result<Vec<(&'static str, &'static str, std::borrow::Cow<'a, str>)>, E> {
    use std::borrow::Cow;
    // Only private callers supply the source-bound SDK candidate. Keep syntax
    // checks too so a future refactor cannot turn this into raw Command input.
    let (payload, suffix) = command.split_once(';').ok_or(E::Target)?;
    if !payload.starts_with('?')
        || payload.len() < 2
        || suffix
            != format!(
                "6;{};{};0",
                match display {
                    SdkCrossReferenceDisplay::Page => 0,
                    SdkCrossReferenceDisplay::BookmarkName => 1,
                    SdkCrossReferenceDisplay::Content => 2,
                    SdkCrossReferenceDisplay::RelativePosition => 3,
                    _ => return Err(E::Target),
                },
                u8::from(hyperlink)
            )
    {
        return Err(E::Target);
    }
    Ok(vec![
        ("booleanParam", "Fiexde", Cow::Borrowed("1")),
        ("integerParam", "Prop", Cow::Borrowed("0")),
        ("stringParam", "Command", Cow::Borrowed(command)),
        ("stringParam", "RefPath", Cow::Owned(format!("{payload};"))),
        ("stringParam", "RefType", Cow::Borrowed("TARGET_BOOKMARK")),
        (
            "stringParam",
            "RefContentType",
            Cow::Borrowed(content_type(display)?),
        ),
        (
            "booleanParam",
            "RefHyperLink",
            Cow::Borrowed(if hyperlink { "true" } else { "false" }),
        ),
        (
            "stringParam",
            "RefOpenType",
            Cow::Borrowed("HWPHYPERLINK_JUMP_CURRENTTAB"),
        ),
    ])
}
pub(super) fn render(
    command: &str,
    display: SdkCrossReferenceDisplay,
    hyperlink: bool,
    id: u32,
    fieldid: u32,
    maximum: usize,
) -> Result<(String, String), E> {
    if command.len() > maximum {
        return Err(E::Limit);
    }
    let mut begin = format!(
        "<hp:fieldBegin id=\"{id}\" type=\"CROSSREF\" name=\"\" editable=\"0\" dirty=\"1\" zorder=\"-1\" fieldid=\"{fieldid}\"><hp:parameters cnt=\"8\" name=\"\">"
    );
    for (tag, name, value) in parameters(command, display, hyperlink)? {
        let value = quick_xml::escape::escape(value.as_ref());
        let needed = begin
            .len()
            .checked_add(value.len())
            .and_then(|n| n.checked_add(tag.len() * 2 + name.len() + 19))
            .ok_or(E::Limit)?;
        if needed > maximum {
            return Err(E::Limit);
        }
        use std::fmt::Write as _;
        write!(&mut begin, "<hp:{tag} name=\"{name}\">{value}</hp:{tag}>").map_err(|_| E::Limit)?;
    }
    begin.push_str("</hp:parameters></hp:fieldBegin>");
    let end = format!("<hp:fieldEnd beginIDRef=\"{id}\" fieldid=\"{fieldid}\"/>");
    if begin
        .len()
        .checked_add(end.len())
        .is_none_or(|n| n > maximum)
    {
        return Err(E::Limit);
    }
    Ok((begin, end))
}
/// Compare the complete generated eight-parameter envelope, not Command alone.
/// The test suite independently compares this relation to original saved and
/// reopened specimens; this readback is not used as its own Native oracle.
pub(super) fn verify_output(
    forms: &ImportedDocumentForms,
    field: &ImportedFieldRange,
    command: &str,
    display: SdkCrossReferenceDisplay,
    hyperlink: bool,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), E> {
    let source = forms.source();
    let resolved = source
        .resolve_anchor(field.parameter_anchor.as_ref().ok_or(E::Readback)?)
        .map_err(|_| E::Readback)?;
    let xml = resolved.part().xml().ok_or(E::Readback)?;
    let parent = resolved.element().ok_or(E::Readback)?;
    if number(parent, "cnt")? != 8 {
        return Err(E::Readback);
    }
    let expected = parameters(command, display, hyperlink)?;
    let mut at = parent.first_child();
    for (tag, name, value) in expected {
        let index = at.ok_or(E::Readback)?;
        let node = xml.elements().get(index).ok_or(E::Readback)?;
        if !named(node, tag)
            || node.first_child().is_some()
            || attr(node, "name").map(|a| a.semantic_value()) != Some(name)
        {
            return Err(E::Readback);
        }
        let text = xml
            .source_text(node.content_span().ok_or(E::Readback)?)
            .map_err(|_| E::Readback)?;
        if text.len() > limits.config().text_bytes
            || quick_xml::escape::unescape(text)
                .map_err(|_| E::Readback)?
                .as_ref()
                != value.as_ref()
        {
            return Err(E::Readback);
        }
        at = node.next_sibling();
    }
    if at.is_some() {
        return Err(E::Readback);
    }
    Ok(())
}
