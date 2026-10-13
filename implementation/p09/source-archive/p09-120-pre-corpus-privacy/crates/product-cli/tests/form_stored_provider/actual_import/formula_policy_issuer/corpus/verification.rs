//! Independent expanded inventory/outside-result-leaf comparator; exact original importer/evaluator, no XML normalization.
use super::*;
use hwpx_package::{
    PreservingXmlDocument, WriterLimits,
    document_import::fields::{
        ImportedDocumentFields,
        semantics::{
            ImportedDocumentFieldSemantics,
            evaluation::{ImportedSourceFormulaEvaluation, output::FormulaResultOutputError},
        },
    },
};

pub(super) struct Expected {
    pub bytes: Vec<u8>,
    pub targets: usize,
    pub cells: usize,
    pub changed: bool,
}
pub(super) fn expected(bytes: &[u8]) -> AnyResult<Expected> {
    let forms = super::super::super::field_ranges::fixture::forms(bytes, "actual-form-document")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let eval = ImportedSourceFormulaEvaluation::import(&meanings)?;
    let lowered = eval.lower_results(bytes, WriterLimits::default());
    let (candidate, changed) = match lowered {
        Ok(result) => (result.with_verified_bytes(<[u8]>::to_vec)?, true),
        Err(FormulaResultOutputError::NoChange) if !eval.values().is_empty() => {
            (bytes.to_vec(), false)
        }
        Err(FormulaResultOutputError::NoTargets) if eval.values().is_empty() => {
            (bytes.to_vec(), false)
        }
        Err(error) => return Err(error.into()),
    };
    Ok(Expected {
        bytes: candidate,
        targets: eval.values().len(),
        cells: eval.source_bindings().len(),
        changed,
    })
}

pub(super) fn verify_package(original: &[u8], candidate: &[u8]) -> TestResult {
    let forms =
        super::super::super::field_ranges::fixture::forms(original, "actual-form-document")?;
    let sections: BTreeSet<_> = forms
        .source()
        .parts()
        .iter()
        .filter(|p| {
            p.role() == hwpx_package::PartRole::SpineDocument
                && p.xml()
                    .and_then(|xml| xml.elements().first())
                    .is_some_and(|root| {
                        root.name().local_name() == "sec"
                            && root.name().namespace()
                                == Some("http://www.hancom.co.kr/hwpml/2011/section")
                    })
        })
        .map(|p| p.path().as_str())
        .collect();
    let old = fixture::entries(original)?;
    let next = fixture::entries(candidate)?;
    assert_eq!(
        old.keys().collect::<Vec<_>>(),
        next.keys().collect::<Vec<_>>()
    );
    for (part, bytes) in &old {
        let new = next.get(part).ok_or("missing part")?;
        if bytes == new {
            continue;
        }
        assert!(sections.contains(part.as_str()));
        verify_section(bytes, new)?;
    }
    Ok(())
}
fn attribute<'a>(
    xml: &'a [u8],
    node: &hwpx_package::XmlElementToken,
    name: &str,
) -> Option<&'a [u8]> {
    let a = node
        .attributes()
        .iter()
        .find(|a| a.name().local_name() == name)?;
    Some(&xml[a.value_span().start()..a.value_span().end()])
}
fn verify_section(original: &[u8], candidate: &[u8]) -> TestResult {
    let old = PreservingXmlDocument::parse(original)?;
    let next = PreservingXmlDocument::parse(candidate)?;
    assert_eq!(old.elements().len(), next.elements().len());
    let mut indices = BTreeSet::new();
    for (index, node) in old.elements().iter().enumerate() {
        let new = &next.elements()[index];
        assert_eq!(node.name(), new.name());
        assert_eq!(node.parent(), new.parent());
        assert_eq!(node.attributes().len(), new.attributes().len());
        for (a, b) in node.attributes().iter().zip(new.attributes()) {
            assert_eq!(a.name(), b.name());
            assert_eq!(
                &original[a.value_span().start()..a.value_span().end()],
                &candidate[b.value_span().start()..b.value_span().end()]
            );
        }
        if node.name().local_name() != "fieldBegin"
            || attribute(original, node, "type") != Some(b"FORMULA")
        {
            continue;
        }
        let params = old
            .elements()
            .iter()
            .position(|e| e.parent() == Some(index) && e.name().local_name() == "parameters")
            .ok_or("formula parameters")?;
        for name in [b"Command".as_slice(), b"LastResult".as_slice()] {
            let targets: Vec<_> = old
                .elements()
                .iter()
                .enumerate()
                .filter(|(_, e)| {
                    e.parent() == Some(params) && attribute(original, e, "name") == Some(name)
                })
                .map(|(i, _)| i)
                .collect();
            assert_eq!(targets.len(), 1);
            indices.insert(targets[0]);
        }
        let ctrl = node.parent().ok_or("ctrl")?;
        let run = old.elements()[ctrl].parent().ok_or("run")?;
        let children: Vec<_> = old
            .elements()
            .iter()
            .enumerate()
            .filter(|(_, e)| e.parent() == Some(run))
            .map(|(i, _)| i)
            .collect();
        assert_eq!(children.len(), 4);
        assert_eq!(children[0], ctrl);
        assert_eq!(old.elements()[children[1]].name().local_name(), "t");
        indices.insert(children[1]);
    }
    assert!(!indices.is_empty());
    let mut edits = Vec::new();
    for index in indices {
        let a = &old.elements()[index];
        let b = &next.elements()[index];
        assert!(a.first_child().is_none() && b.first_child().is_none());
        let start = if a.is_empty() {
            a.outer_span()
        } else {
            a.content_span()
        }
        .ok_or("old leaf")?;
        let end = if a.is_empty() {
            b.outer_span()
        } else {
            b.content_span()
        }
        .ok_or("new leaf")?;
        edits.push((
            start.start(),
            start.end(),
            candidate[end.start()..end.end()].to_vec(),
        ));
    }
    edits.sort_by_key(|e| e.0);
    assert!(edits.windows(2).all(|w| w[0].1 <= w[1].0));
    let mut reconstructed = original.to_vec();
    for (start, end, value) in edits.into_iter().rev() {
        reconstructed.splice(start..end, value);
    }
    assert_eq!(reconstructed, candidate);
    Ok(())
}
