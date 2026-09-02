use std::collections::BTreeMap;
use std::fmt;
use std::io::{Read, Seek};

use thiserror::Error;

use crate::{
    BoundedZipReader, GraphError, IdIndex, IdIndexError, IdIndexLimits, IdRuleProfile,
    MetadataDisposition, NormalizedWriter, PackageError, PackageGraph, PackageGraphLimits,
    PackageLimits, PatchError, PatchPartDisposition, PatchResult, PreservationError,
    PreservationReport, PreservingPatchEngine, PreservingWriter, WriterError, WriterLimits,
};

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct RoundTripLimits {
    pub package: PackageLimits,
    pub graph: PackageGraphLimits,
    pub ids: IdIndexLimits,
    pub writer: WriterLimits,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RoundTripEvidence {
    source_parts: usize,
    declarations: usize,
    references: usize,
    writer_entries: usize,
    untouched_policy_violations: usize,
    preserving_sha256: [u8; 32],
    normalized_sha256: [u8; 32],
    preserving_deterministic: bool,
    normalized_deterministic: bool,
}

impl RoundTripEvidence {
    #[must_use]
    pub const fn source_parts(&self) -> usize {
        self.source_parts
    }

    #[must_use]
    pub const fn declarations(&self) -> usize {
        self.declarations
    }

    #[must_use]
    pub const fn references(&self) -> usize {
        self.references
    }

    #[must_use]
    pub const fn writer_entries(&self) -> usize {
        self.writer_entries
    }

    #[must_use]
    pub const fn untouched_policy_violations(&self) -> usize {
        self.untouched_policy_violations
    }

    #[must_use]
    pub const fn preserving_sha256(&self) -> [u8; 32] {
        self.preserving_sha256
    }

    #[must_use]
    pub const fn normalized_sha256(&self) -> [u8; 32] {
        self.normalized_sha256
    }

    #[must_use]
    pub const fn preserving_deterministic(&self) -> bool {
        self.preserving_deterministic
    }

    #[must_use]
    pub const fn normalized_deterministic(&self) -> bool {
        self.normalized_deterministic
    }
}

#[derive(Debug)]
pub struct RoundTripVerifier;

impl RoundTripVerifier {
    /// Reopens an explicit source, applies a no-op preserving transaction, and verifies both writer
    /// modes without exposing input or output bytes.
    ///
    /// # Errors
    ///
    /// Fails closed at the first bounded archive, graph, preservation, ID, patch or writer error.
    pub fn verify<R: Read + Seek>(
        source: R,
        limits: RoundTripLimits,
    ) -> Result<RoundTripEvidence, RoundTripError> {
        let mut reader = BoundedZipReader::open(source, limits.package)?;
        let graph = PackageGraph::build(&mut reader, limits.graph)?;
        let preservation =
            PreservationReport::build_with_graph_limits(&mut reader, &graph, limits.graph)?;
        if !preservation.direct_preserve_ready() {
            return Err(RoundTripError::SourceNotPreservable);
        }
        let index = IdIndex::build_with_graph_limits(
            &mut reader,
            &graph,
            limits.graph,
            IdRuleProfile::current_hancom_2020_core_v1(),
            limits.ids,
        )?;
        let patch = PreservingPatchEngine::apply(&mut reader, &graph, &[])?;
        let evidence = Self::verify_patch(&patch, limits)?;
        if evidence.source_parts != preservation.parts().len()
            || evidence.declarations != index.declarations().len()
            || evidence.references != index.references().len()
        {
            return Err(RoundTripError::EvidenceMismatch);
        }
        Ok(evidence)
    }

    /// Verifies preserving and normalized writer behavior for one already validated patch result.
    ///
    /// # Errors
    ///
    /// Returns no evidence if artifact integrity, determinism, metadata or untouched policy drifts.
    pub fn verify_patch(
        patch: &PatchResult,
        limits: RoundTripLimits,
    ) -> Result<RoundTripEvidence, RoundTripError> {
        patch.verify_artifact_integrity()?;
        let preserving = PreservingWriter::build(
            patch,
            limits.package,
            limits.graph,
            limits.ids,
            limits.writer,
        )?;
        let preserving_again = PreservingWriter::build(
            patch,
            limits.package,
            limits.graph,
            limits.ids,
            limits.writer,
        )?;
        let normalized = NormalizedWriter::build(
            patch,
            limits.package,
            limits.graph,
            limits.ids,
            limits.writer,
        )?;
        let normalized_again = NormalizedWriter::build(
            patch,
            limits.package,
            limits.graph,
            limits.ids,
            limits.writer,
        )?;
        preserving.verify()?;
        normalized.verify()?;

        let preserving_deterministic = preserving.sha256() == preserving_again.sha256();
        let normalized_deterministic = normalized.sha256() == normalized_again.sha256();
        if !preserving_deterministic || !normalized_deterministic {
            return Err(RoundTripError::NondeterministicWriter);
        }
        if preserving.report().order() != MetadataDisposition::PreservedAvailable
            || preserving.report().compression_method() != MetadataDisposition::PreservedAvailable
            || preserving.report().raw_compressed_stream()
                != MetadataDisposition::NotPreservedUnavailable
            || normalized.report().order() != MetadataDisposition::Normalized
            || normalized.report().compression_method() != MetadataDisposition::Normalized
        {
            return Err(RoundTripError::EvidenceMismatch);
        }

        let records = patch
            .parts()
            .iter()
            .map(|record| (record.path(), record))
            .collect::<BTreeMap<_, _>>();
        let mut untouched_policy_violations = 0_usize;
        for entry in preserving.report().entries() {
            let Some(record) = records.get(entry.path()) else {
                return Err(RoundTripError::EvidenceMismatch);
            };
            if record.disposition() == PatchPartDisposition::Untouched
                && (record.source_sha256() != Some(record.output_sha256())
                    || entry.expanded_sha256() != record.output_sha256())
            {
                untouched_policy_violations = untouched_policy_violations
                    .checked_add(1)
                    .ok_or(RoundTripError::EvidenceMismatch)?;
            }
        }
        if untouched_policy_violations != 0
            || preserving.report().entries().len() != patch.parts().len()
            || normalized.report().entries().len() != patch.parts().len()
        {
            return Err(RoundTripError::UntouchedPolicyViolation);
        }

        Ok(RoundTripEvidence {
            source_parts: patch.parts().len(),
            declarations: patch.declaration_count(),
            references: patch.reference_count(),
            writer_entries: preserving.report().entries().len(),
            untouched_policy_violations,
            preserving_sha256: preserving.sha256(),
            normalized_sha256: normalized.sha256(),
            preserving_deterministic,
            normalized_deterministic,
        })
    }
}

#[derive(Debug, Error)]
pub enum RoundTripError {
    #[error("bounded archive admission failed")]
    Package(#[from] PackageError),
    #[error("package graph admission failed")]
    Graph(#[from] GraphError),
    #[error("preservation admission failed")]
    Preservation(#[from] PreservationError),
    #[error("ID/reference admission failed")]
    IdIndex(#[from] IdIndexError),
    #[error("patch transaction failed")]
    Patch(#[from] PatchError),
    #[error("package writer failed")]
    Writer(#[from] WriterError),
    #[error("source package is not directly preservable")]
    SourceNotPreservable,
    #[error("round-trip evidence differs across validation layers")]
    EvidenceMismatch,
    #[error("writer output is not deterministic")]
    NondeterministicWriter,
    #[error("untouched part policy was violated")]
    UntouchedPolicyViolation,
}

impl RoundTripError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::Package(error) => error.code(),
            Self::Graph(error) => error.code(),
            Self::Preservation(error) => error.code(),
            Self::IdIndex(error) => error.code(),
            Self::Patch(error) => error.code(),
            Self::Writer(error) => error.code(),
            Self::SourceNotPreservable => "roundtrip_source_not_preservable",
            Self::EvidenceMismatch => "roundtrip_evidence_mismatch",
            Self::NondeterministicWriter => "roundtrip_writer_nondeterministic",
            Self::UntouchedPolicyViolation => "roundtrip_untouched_policy_violation",
        }
    }

    #[must_use]
    pub fn diagnostic(&self) -> RepairDiagnostic {
        RepairDiagnostic::from_error(self)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DiagnosticLayer {
    Archive,
    PackageGraph,
    Preservation,
    IdReference,
    Patch,
    Publication,
    InternalEvidence,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Repairability {
    SafeRetry,
    RegenerateFromValidatedSource,
    NotRepairableAutomatically,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RecommendedAction {
    UseNewDestination,
    ReviewFiniteLimits,
    RetryFromValidatedSource,
    InspectPublishedArtifact,
    ReplaceOrRestoreSource,
    StopAndReport,
}

#[derive(Clone, Copy, Eq, PartialEq)]
pub struct RepairDiagnostic {
    code: &'static str,
    layer: DiagnosticLayer,
    repairability: Repairability,
    action: RecommendedAction,
}

impl fmt::Debug for RepairDiagnostic {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RepairDiagnostic")
            .field("code", &self.code)
            .field("layer", &self.layer)
            .field("repairability", &self.repairability)
            .field("action", &self.action)
            .finish()
    }
}

impl RepairDiagnostic {
    fn from_error(error: &RoundTripError) -> Self {
        let code = error.code();
        let layer = match error {
            RoundTripError::Package(_) => DiagnosticLayer::Archive,
            RoundTripError::Graph(_) => DiagnosticLayer::PackageGraph,
            RoundTripError::Preservation(_) | RoundTripError::SourceNotPreservable => {
                DiagnosticLayer::Preservation
            }
            RoundTripError::IdIndex(_) => DiagnosticLayer::IdReference,
            RoundTripError::Patch(_) => DiagnosticLayer::Patch,
            RoundTripError::Writer(_) => DiagnosticLayer::Publication,
            RoundTripError::EvidenceMismatch
            | RoundTripError::NondeterministicWriter
            | RoundTripError::UntouchedPolicyViolation => DiagnosticLayer::InternalEvidence,
        };
        let (repairability, action) = match code {
            "writer_output_exists" => (
                Repairability::SafeRetry,
                RecommendedAction::UseNewDestination,
            ),
            "writer_output_limit_exceeded"
            | "writer_invalid_limit"
            | "invalid_limit"
            | "invalid_limit_relation"
            | "invalid_graph_limit"
            | "id_index_invalid_limit" => (
                Repairability::SafeRetry,
                RecommendedAction::ReviewFiniteLimits,
            ),
            "writer_workspace_failed" | "writer_staging_cleanup_failed" => (
                Repairability::RegenerateFromValidatedSource,
                RecommendedAction::RetryFromValidatedSource,
            ),
            "writer_published_incomplete" | "writer_published_readback_failed" => (
                Repairability::NotRepairableAutomatically,
                RecommendedAction::InspectPublishedArtifact,
            ),
            "roundtrip_evidence_mismatch"
            | "roundtrip_writer_nondeterministic"
            | "roundtrip_untouched_policy_violation" => (
                Repairability::NotRepairableAutomatically,
                RecommendedAction::StopAndReport,
            ),
            _ => (
                Repairability::NotRepairableAutomatically,
                RecommendedAction::ReplaceOrRestoreSource,
            ),
        };
        Self {
            code,
            layer,
            repairability,
            action,
        }
    }

    #[must_use]
    pub const fn code(&self) -> &'static str {
        self.code
    }

    #[must_use]
    pub const fn layer(&self) -> DiagnosticLayer {
        self.layer
    }

    #[must_use]
    pub const fn repairability(&self) -> Repairability {
        self.repairability
    }

    #[must_use]
    pub const fn action(&self) -> RecommendedAction {
        self.action
    }
}
