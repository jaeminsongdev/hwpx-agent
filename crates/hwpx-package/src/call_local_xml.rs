//! Private parse reuse inside one preserving patch call, never authority/read caching.
use std::collections::{BTreeMap, btree_map::Entry};

use crate::{PreservingXmlDocument, PreservingXmlError};

pub(crate) struct CallLocalXmlDocuments {
    documents: BTreeMap<String, PreservingXmlDocument>,
    scratch: Option<PreservingXmlDocument>,
    retained_source_bytes: usize,
    maximum_retained_source_bytes: usize,
}

impl Default for CallLocalXmlDocuments {
    fn default() -> Self {
        Self {
            documents: BTreeMap::new(),
            scratch: None,
            retained_source_bytes: 0,
            // Optimization-only budget, NOT a product/host admission limit.
            // Beyond it use the original parser afresh instead of rejecting input.
            maximum_retained_source_bytes: 8 * 1024 * 1024,
        }
    }
}

impl CallLocalXmlDocuments {
    // The caller still performs its original fresh bounded read, CRC/size,
    // digest, graph/profile, round-trip and ID checks. Reuse ONLY when every
    // fresh byte equals this private immutable model's complete source bytes.
    pub(crate) fn document(
        &mut self,
        key: &str,
        fresh: &[u8],
    ) -> Result<&PreservingXmlDocument, PreservingXmlError> {
        let document = match self.documents.entry(key.to_owned()) {
            Entry::Vacant(entry) => {
                let next = self.retained_source_bytes.checked_add(fresh.len());
                if next.is_none_or(|n| n > self.maximum_retained_source_bytes) {
                    return Ok(self.scratch.insert(PreservingXmlDocument::parse(fresh)?));
                }
                let parsed = PreservingXmlDocument::parse(fresh)?;
                self.retained_source_bytes += fresh.len();
                entry.insert(parsed)
            }
            Entry::Occupied(mut entry) => {
                if !entry.get().with_source_bytes(|source| source == fresh) {
                    // Changed bytes are reparsed, preserving original parse
                    // error precedence; later caller digest checks still run.
                    let old_len = entry.get().with_source_bytes(<[u8]>::len);
                    let next = (self.retained_source_bytes - old_len).checked_add(fresh.len());
                    if next.is_none_or(|n| n > self.maximum_retained_source_bytes) {
                        return Ok(self.scratch.insert(PreservingXmlDocument::parse(fresh)?));
                    }
                    let parsed = PreservingXmlDocument::parse(fresh)?;
                    self.retained_source_bytes = self.retained_source_bytes - old_len + fresh.len();
                    *entry.get_mut() = parsed;
                }
                entry.into_mut()
            }
        };
        Ok(document)
    }

    pub(crate) fn take_document(
        &mut self,
        key: &str,
        fresh: &[u8],
    ) -> Result<PreservingXmlDocument, PreservingXmlError> {
        let removed = self.documents.remove(key);
        if let Some(document) = &removed {
            self.retained_source_bytes -= document.with_source_bytes(<[u8]>::len);
        }
        self.scratch = None;
        match removed {
            Some(document) if document.with_source_bytes(|source| source == fresh) => Ok(document),
            _ => PreservingXmlDocument::parse(fresh),
        }
    }
}

#[cfg(test)]
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod inputs;

#[cfg(test)]
mod tests {
    use super::*;
    use std::{
        cell::RefCell,
        io::{Cursor, Read, Seek, SeekFrom},
        rc::Rc,
    };

    #[derive(Default, Debug, Eq, PartialEq)]
    struct Reads {
        calls: usize,
        bytes: usize,
        seeks: usize,
    }
    struct ObservedCursor<'a> {
        inner: Cursor<&'a [u8]>,
        reads: Rc<RefCell<Reads>>,
    }
    impl Read for ObservedCursor<'_> {
        fn read(&mut self, buffer: &mut [u8]) -> std::io::Result<usize> {
            let count = self.inner.read(buffer)?;
            let mut reads = self.reads.borrow_mut();
            reads.calls += 1;
            reads.bytes += count;
            Ok(count)
        }
    }
    impl Seek for ObservedCursor<'_> {
        fn seek(&mut self, position: SeekFrom) -> std::io::Result<u64> {
            self.reads.borrow_mut().seeks += 1;
            self.inner.seek(position)
        }
    }

    #[test]
    fn full36_preservation_profiles_id_results_and_fresh_read_counts_match_original()
    -> Result<(), Box<dyn std::error::Error>> {
        use crate::{
            BoundedZipReader, IdIndex, IdIndexLimits, IdRuleProfile, PackageGraph,
            PackageGraphLimits, PackageLimits, PreservationReport, PreservationRuleProfile,
        };
        let mut packages = 0;
        for bytes in super::inputs::actual_corpus()? {
            let mut graph_reader =
                BoundedZipReader::open(Cursor::new(bytes.as_slice()), PackageLimits::default())?;
            let graph = PackageGraph::build(&mut graph_reader, PackageGraphLimits::default())?;
            let mut models = CallLocalXmlDocuments::default();
            for profile in [
                PreservationRuleProfile::CoreV1,
                PreservationRuleProfile::Hangul2020PreviewTextV2,
            ] {
                let plain_reads = Rc::new(RefCell::new(Reads::default()));
                let shared_reads = Rc::new(RefCell::new(Reads::default()));
                let mut plain = BoundedZipReader::open(
                    ObservedCursor {
                        inner: Cursor::new(bytes.as_slice()),
                        reads: plain_reads.clone(),
                    },
                    PackageLimits::default(),
                )?;
                let mut shared = BoundedZipReader::open(
                    ObservedCursor {
                        inner: Cursor::new(bytes.as_slice()),
                        reads: shared_reads.clone(),
                    },
                    PackageLimits::default(),
                )?;
                let expected = PreservationReport::build_with_graph_limits_and_profile(
                    &mut plain,
                    &graph,
                    PackageGraphLimits::default(),
                    profile,
                )?;
                let actual = PreservationReport::build_with_call_local_xml(
                    &mut shared,
                    &graph,
                    PackageGraphLimits::default(),
                    profile,
                    &mut models,
                )?;
                assert!(actual == expected, "whole preservation evidence differs");
                assert_eq!(*plain_reads.borrow(), *shared_reads.borrow());
            }
            let plain_reads = Rc::new(RefCell::new(Reads::default()));
            let shared_reads = Rc::new(RefCell::new(Reads::default()));
            let mut plain = BoundedZipReader::open(
                ObservedCursor {
                    inner: Cursor::new(bytes.as_slice()),
                    reads: plain_reads.clone(),
                },
                PackageLimits::default(),
            )?;
            let mut shared = BoundedZipReader::open(
                ObservedCursor {
                    inner: Cursor::new(bytes.as_slice()),
                    reads: shared_reads.clone(),
                },
                PackageLimits::default(),
            )?;
            let expected = IdIndex::build_with_graph_limits(
                &mut plain,
                &graph,
                PackageGraphLimits::default(),
                IdRuleProfile::current_hancom_2020_formula_v3(),
                IdIndexLimits::default(),
            );
            let actual = IdIndex::build_with_call_local_xml(
                &mut shared,
                &graph,
                PackageGraphLimits::default(),
                IdRuleProfile::current_hancom_2020_formula_v3(),
                IdIndexLimits::default(),
                &mut models,
            );
            match (expected, actual) {
                (Ok(expected), Ok(actual)) => {
                    assert!(expected == actual, "whole typed ID index differs")
                }
                (Err(expected), Err(actual)) => {
                    assert_eq!(actual.code(), expected.code());
                    assert!(
                        actual.validation() == expected.validation(),
                        "whole ID denial report differs"
                    );
                }
                _ => return Err("ID acceptance/denial differs".into()),
            }
            assert_eq!(*plain_reads.borrow(), *shared_reads.borrow());
            packages += 1;
        }
        assert_eq!(packages, 36);
        Ok(())
    }

    #[test]
    fn exact_fresh_bytes_reuse_one_immutable_model_and_full_round_trip() {
        let bytes = b"<r xmlns='urn:test'><n>123&amp;4</n></r>";
        let mut models = CallLocalXmlDocuments::default();
        let first = models.document("part", bytes).unwrap();
        first.verify_untouched_round_trip().unwrap();
        let pointer = first as *const PreservingXmlDocument;
        let second = models.document("part", bytes).unwrap();
        assert_eq!(pointer, second as *const PreservingXmlDocument);
        second.verify_untouched_round_trip().unwrap();
        assert_eq!(second, &PreservingXmlDocument::parse(bytes).unwrap());
    }

    #[test]
    fn same_length_changed_bytes_replace_model_instead_of_hash_only_replay() {
        let mut models = CallLocalXmlDocuments::default();
        let original = b"<r><n>123</n></r>";
        let changed = b"<r><n>999</n></r>";
        let old_hash = models.document("part", original).unwrap().original_sha256();
        let next = models.document("part", changed).unwrap();
        assert_ne!(next.original_sha256(), old_hash);
        assert!(next.with_source_bytes(|raw| raw == changed));
        assert_eq!(next, &PreservingXmlDocument::parse(changed).unwrap());
        next.verify_untouched_round_trip().unwrap();
    }

    #[test]
    fn malformed_new_bytes_keep_original_parser_errors_not_cached_acceptance() {
        let mut models = CallLocalXmlDocuments::default();
        let original = b"<r><n>123</n></r>";
        models.document("part", original).unwrap();
        for invalid in [
            b"<r>".as_slice(),
            b"<!DOCTYPE r><r/>",
            b"<r>&unknown;</r>",
            b"<r/><s/>",
        ] {
            let expected = PreservingXmlDocument::parse(invalid).unwrap_err();
            assert_eq!(models.document("part", invalid).unwrap_err(), expected);
            assert_eq!(models.take_document("part", invalid).unwrap_err(), expected);
            models.document("part", original).unwrap();
        }
    }

    #[test]
    fn transfer_moves_only_exact_local_model_and_scopes_do_not_share_state() {
        let bytes = b"<r>123</r>";
        let mut models = CallLocalXmlDocuments::default();
        models.document("first", bytes).unwrap();
        models.document("second", bytes).unwrap();
        assert_eq!(models.documents.len(), 2);
        let original_pointer = models
            .document("first", bytes)
            .unwrap()
            .with_source_bytes(|raw| raw.as_ptr());
        let moved = models.take_document("first", bytes).unwrap();
        assert_eq!(
            moved.with_source_bytes(|raw| raw.as_ptr()),
            original_pointer
        );
        assert!(!models.documents.contains_key("first"));
        assert_eq!(models.documents.len(), 1);
        assert!(CallLocalXmlDocuments::default().documents.is_empty());
        assert_eq!(
            models.take_document("missing", bytes).unwrap(),
            PreservingXmlDocument::parse(bytes).unwrap()
        );
    }

    #[test]
    fn optimization_budget_falls_back_to_full_fresh_parse_without_rejecting_input() {
        let first = b"<r>123</r>";
        let second = b"<r>999</r>";
        let mut models = CallLocalXmlDocuments {
            maximum_retained_source_bytes: first.len(),
            ..Default::default()
        };
        models.document("first", first).unwrap();
        assert_eq!(models.retained_source_bytes, first.len());
        let fallback = models.document("second", second).unwrap();
        assert_eq!(fallback, &PreservingXmlDocument::parse(second).unwrap());
        assert_eq!(models.retained_source_bytes, first.len());
        assert_eq!(models.documents.len(), 1);
        assert_eq!(
            models.take_document("second", second).unwrap(),
            PreservingXmlDocument::parse(second).unwrap()
        );
        assert!(models.scratch.is_none());
        let oversized = b"<r>99999999999999</r>";
        assert_eq!(
            models.document("first", oversized).unwrap(),
            &PreservingXmlDocument::parse(oversized).unwrap()
        );
        assert_eq!(models.retained_source_bytes, first.len());
        models.take_document("first", oversized).unwrap();
        assert_eq!(models.retained_source_bytes, 0);
        let mut uncached = CallLocalXmlDocuments {
            maximum_retained_source_bytes: 0,
            ..Default::default()
        };
        assert_eq!(
            uncached.document("first", first).unwrap(),
            &PreservingXmlDocument::parse(first).unwrap()
        );
        assert!(uncached.documents.is_empty());
        assert_eq!(
            uncached.document("first", b"<r>").unwrap_err(),
            PreservingXmlDocument::parse(b"<r>").unwrap_err()
        );
    }

    #[test]
    fn all36_originals_every_modeled_xml_part_match_independent_fresh_parses()
    -> Result<(), Box<dyn std::error::Error>> {
        use crate::document_import::{ImportedSourcePackage, SourceImportLimits};
        use domain_ir::DocumentId;
        use sha2::{Digest as _, Sha256};
        let mut packages = 0;
        let mut parts = 0;
        for bytes in super::inputs::actual_corpus()? {
            let source = ImportedSourcePackage::import(
                &bytes,
                DocumentId::parse("call-local-xml-corpus")?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
            )?;
            let mut models = CallLocalXmlDocuments::default();
            for part in source.parts() {
                if let Some(original) = part.xml() {
                    let fresh = original.with_source_bytes(<[u8]>::to_vec);
                    let oracle = PreservingXmlDocument::parse(&fresh)?;
                    for _ in 0..4 {
                        let reused = models.document(part.path().collision_key(), &fresh)?;
                        assert_eq!(reused, &oracle);
                        reused.verify_untouched_round_trip()?;
                    }
                    assert_eq!(
                        models.take_document(part.path().collision_key(), &fresh)?,
                        oracle
                    );
                    parts += 1;
                }
            }
            assert!(models.documents.is_empty());
            packages += 1;
        }
        assert_eq!(packages, 36);
        assert!(parts >= packages);
        Ok(())
    }
}
