use std::cmp;
use std::fmt;

use domain_ir::{
    MathAlignedLine, MathAst, MathAstDraft, MathAstLimits, MathCase, MathDerivativeVariable,
    MathExpression, MathFunction, MathNode,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const EQUATION_LAYOUT_SCHEMA_VERSION: &str = "hwpx-agent.equation-layout/v1";
pub const EQUATION_LAYOUT_PROFILE_VERSION: &str =
    "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1";
pub const EQUATION_LAYOUT_QUALIFICATION_SCHEMA_VERSION: &str =
    "hwpx-agent.equation-layout-qualification/v1";

const EXACT_BUILD: &str = "11.0.0.9136";
const EXACT_FONT: &str = "HancomEQN";
const MAX_BASELINE_ERROR_HWPUNIT: u32 = 50;
const MAX_EXTENT_ERROR_HWPUNIT: u32 = 150;
const MIN_INLINE_SAMPLES: usize = 4;
const MIN_DISPLAY_SAMPLES: usize = 4;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EquationLayoutLimitConfig {
    pub qualification_bytes: usize,
    pub samples: usize,
    pub base_unit: u32,
    pub extent_hwpunit: u32,
    pub metric_units: u32,
    pub page_pixels: u32,
    pub serialized_bytes: usize,
}

impl Default for EquationLayoutLimitConfig {
    fn default() -> Self {
        Self {
            qualification_bytes: 4 * 1024 * 1024,
            samples: 4_096,
            base_unit: 100_000,
            extent_hwpunit: 10_000_000,
            metric_units: 1_000_000,
            page_pixels: 100_000,
            serialized_bytes: 4 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct EquationLayoutLimits(EquationLayoutLimitConfig);

impl EquationLayoutLimits {
    pub const HARD_MAX_QUALIFICATION_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_SAMPLES: usize = 65_536;
    pub const HARD_MAX_BASE_UNIT: u32 = 1_000_000;
    pub const HARD_MAX_EXTENT_HWPUNIT: u32 = 100_000_000;
    pub const HARD_MAX_METRIC_UNITS: u32 = 10_000_000;
    pub const HARD_MAX_PAGE_PIXELS: u32 = 1_000_000;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;

    /// Creates finite P07-07 layout limits.
    ///
    /// # Errors
    ///
    /// Rejects zero, hard-ceiling, or internally inconsistent limits.
    pub fn new(config: EquationLayoutLimitConfig) -> Result<Self, EquationLayoutError> {
        if config.qualification_bytes == 0
            || config.qualification_bytes > Self::HARD_MAX_QUALIFICATION_BYTES
            || config.samples < MIN_INLINE_SAMPLES + MIN_DISPLAY_SAMPLES
            || config.samples > Self::HARD_MAX_SAMPLES
            || config.base_unit == 0
            || config.base_unit > Self::HARD_MAX_BASE_UNIT
            || config.extent_hwpunit == 0
            || config.extent_hwpunit > Self::HARD_MAX_EXTENT_HWPUNIT
            || config.metric_units == 0
            || config.metric_units > Self::HARD_MAX_METRIC_UNITS
            || config.page_pixels == 0
            || config.page_pixels > Self::HARD_MAX_PAGE_PIXELS
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(EquationLayoutError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> EquationLayoutLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EquationLayoutMode {
    Inline,
    Display,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EquationLayoutSource {
    TargetReadback,
    VerifiedEstimator,
    Provisional,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EquationLayoutEstimate {
    schema_version: &'static str,
    profile_version: &'static str,
    semantic_sha256: String,
    layout: EquationLayoutMode,
    base_unit: u32,
    width_hwpunit: u32,
    height_hwpunit: u32,
    baseline_percent: u8,
    source: EquationLayoutSource,
    source_evidence_sha256: Option<String>,
    render_required: bool,
}

impl EquationLayoutEstimate {
    #[must_use]
    pub const fn profile_version(&self) -> &'static str {
        self.profile_version
    }

    #[must_use]
    pub fn semantic_sha256(&self) -> &str {
        &self.semantic_sha256
    }

    #[must_use]
    pub const fn layout(&self) -> EquationLayoutMode {
        self.layout
    }

    #[must_use]
    pub const fn base_unit(&self) -> u32 {
        self.base_unit
    }

    #[must_use]
    pub const fn width_hwpunit(&self) -> u32 {
        self.width_hwpunit
    }

    #[must_use]
    pub const fn height_hwpunit(&self) -> u32 {
        self.height_hwpunit
    }

    #[must_use]
    pub const fn baseline_percent(&self) -> u8 {
        self.baseline_percent
    }

    #[must_use]
    pub const fn source(&self) -> EquationLayoutSource {
        self.source
    }

    #[must_use]
    pub fn source_evidence_sha256(&self) -> Option<&str> {
        self.source_evidence_sha256.as_deref()
    }

    #[must_use]
    pub const fn render_required(&self) -> bool {
        self.render_required
    }

    /// Serializes a deterministic bounded estimate receipt.
    ///
    /// # Errors
    ///
    /// Returns an error when the receipt exceeds its configured bound.
    pub fn canonical_json(
        &self,
        limits: EquationLayoutLimits,
    ) -> Result<Vec<u8>, EquationLayoutError> {
        let bytes = serde_json::to_vec(self).map_err(|_| EquationLayoutError::Serialization)?;
        if bytes.len() > limits.0.serialized_bytes {
            return Err(EquationLayoutError::OutputLimit);
        }
        Ok(bytes)
    }
}

impl fmt::Debug for EquationLayoutEstimate {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationLayoutEstimate")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("semantic_sha256", &"<redacted>")
            .field("layout", &self.layout)
            .field("base_unit", &"<redacted>")
            .field("extent", &"<redacted>")
            .field("source", &self.source)
            .field("source_evidence_sha256", &"<redacted>")
            .field("render_required", &self.render_required)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct QualificationDraft {
    schema_version: String,
    profile_version: String,
    target: QualificationTarget,
    evidence_sha256: String,
    font_metrics_sha256: String,
    corpus_semantic_sha256: String,
    model: LayoutModel,
    envelope: LayoutEnvelope,
    validation: LayoutValidation,
    exact_samples: Vec<ExactSample>,
}

impl fmt::Debug for QualificationDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("QualificationDraft(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct QualificationTarget {
    build: String,
    architecture: String,
    locale: String,
    font_name: String,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct LayoutModel {
    width_per_advance_milli: u32,
    horizontal_padding_milli: u32,
    line_height_milli: u32,
    vertical_level_milli: u32,
    inline_baseline_percent: u8,
    display_baseline_percent: u8,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_field_names)]
struct LayoutEnvelope {
    maximum_nodes: u32,
    maximum_depth: u32,
    maximum_advance_units: u32,
    maximum_vertical_levels: u32,
    maximum_matrix_rows: u32,
    maximum_matrix_columns: u32,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct LayoutValidation {
    sample_count: usize,
    inline_sample_count: usize,
    display_sample_count: usize,
    extent_max_error_hwpunit: u32,
    baseline_max_error_hwpunit: u32,
    ink_box_overflow_count: usize,
    clipping_count: usize,
    overlap_count: usize,
    silent_fallback_count: usize,
    all_pages_inspected: bool,
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct ExactSample {
    semantic_sha256: String,
    layout: EquationLayoutMode,
    base_unit: u32,
    width_hwpunit: u32,
    height_hwpunit: u32,
    baseline_percent: u8,
    native_readback_sha256: String,
    render_evidence_sha256: String,
    metrics: SampleMetrics,
    ink_box: InkBox,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct SampleMetrics {
    advance_units: u32,
    above_levels: u32,
    below_levels: u32,
    nodes: u32,
    depth: u32,
    matrix_rows: u32,
    matrix_columns: u32,
}

impl From<SampleMetrics> for EquationLayoutMetrics {
    fn from(value: SampleMetrics) -> Self {
        Self {
            advance_units: value.advance_units,
            above_levels: value.above_levels,
            below_levels: value.below_levels,
            nodes: value.nodes,
            depth: value.depth,
            matrix_rows: value.matrix_rows,
            matrix_columns: value.matrix_columns,
        }
    }
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct InkBox {
    page_width_pixels: u32,
    page_height_pixels: u32,
    left: u32,
    top: u32,
    width: u32,
    height: u32,
    dpi: u16,
}

#[derive(Clone)]
struct QualifiedLayout {
    evidence_sha256: String,
    model: LayoutModel,
    envelope: LayoutEnvelope,
    exact_samples: Vec<ExactSample>,
}

impl fmt::Debug for QualifiedLayout {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("QualifiedLayout(<redacted>)")
    }
}

#[derive(Clone, Debug)]
pub struct EquationLayoutEstimator {
    limits: EquationLayoutLimits,
    math_limits: MathAstLimits,
    qualification: Option<QualifiedLayout>,
}

impl EquationLayoutEstimator {
    /// Creates a conservative estimator with no qualified target model.
    #[must_use]
    pub const fn provisional(limits: EquationLayoutLimits, math_limits: MathAstLimits) -> Self {
        Self {
            limits,
            math_limits,
            qualification: None,
        }
    }

    /// Measures the exact structural inputs used by provisional and qualified models.
    ///
    /// # Errors
    ///
    /// Rejects invalid ASTs, depth/node/unit overflows, and metric-limit violations.
    pub fn measure(
        &self,
        draft: MathAstDraft,
    ) -> Result<EquationLayoutMetrics, EquationLayoutError> {
        let ast = MathAst::from_draft(draft, self.math_limits)
            .map_err(|_| EquationLayoutError::MathAst)?;
        measure_node(ast.root(), self.limits, 1)
    }

    /// Creates an estimator from an exact hash-pinned target qualification.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicated, unknown, oversized, untrusted, incomplete, out-of-bound, or
    /// visually failing qualification records.
    pub fn from_qualification_json(
        limits: EquationLayoutLimits,
        math_limits: MathAstLimits,
        bytes: &[u8],
        trusted_sha256: &str,
    ) -> Result<Self, EquationLayoutError> {
        if bytes.is_empty() || bytes.len() > limits.0.qualification_bytes {
            return Err(EquationLayoutError::QualificationLimit);
        }
        require_digest(trusted_sha256)?;
        if hex::encode(Sha256::digest(bytes)) != trusted_sha256 {
            return Err(EquationLayoutError::UntrustedQualification);
        }
        let draft: QualificationDraft =
            serde_json::from_slice(bytes).map_err(|_| EquationLayoutError::InvalidQualification)?;
        let qualification = validate_qualification(draft, limits)?;
        Ok(Self {
            limits,
            math_limits,
            qualification: Some(qualification),
        })
    }

    /// Estimates native equation extent and baseline without silently promoting provisional data.
    ///
    /// # Errors
    ///
    /// Rejects invalid AST, base unit, metric arithmetic, or output bounds.
    pub fn estimate(
        &self,
        draft: MathAstDraft,
        layout: EquationLayoutMode,
        base_unit: u32,
    ) -> Result<EquationLayoutEstimate, EquationLayoutError> {
        if base_unit == 0 || base_unit > self.limits.0.base_unit {
            return Err(EquationLayoutError::InvalidBaseUnit);
        }
        let ast = MathAst::from_draft(draft, self.math_limits)
            .map_err(|_| EquationLayoutError::MathAst)?;
        let semantic_sha256 = hex::encode(
            ast.semantic_sha256(self.math_limits)
                .map_err(|_| EquationLayoutError::MathAst)?,
        );
        let metrics = measure_node(ast.root(), self.limits, 1)?;
        if let Some(qualification) = &self.qualification {
            if let Some(sample) = qualification.exact_samples.iter().find(|sample| {
                sample.semantic_sha256 == semantic_sha256
                    && sample.layout == layout
                    && sample.base_unit == base_unit
            }) {
                return self.finish(
                    semantic_sha256,
                    layout,
                    base_unit,
                    sample.width_hwpunit,
                    sample.height_hwpunit,
                    sample.baseline_percent,
                    EquationLayoutSource::TargetReadback,
                    Some(qualification.evidence_sha256.clone()),
                    false,
                );
            }
            if qualification.envelope.admits(metrics) {
                let (width, height, baseline) =
                    estimate_from_model(metrics, base_unit, layout, qualification.model)?;
                return self.finish(
                    semantic_sha256,
                    layout,
                    base_unit,
                    width,
                    height,
                    baseline,
                    EquationLayoutSource::VerifiedEstimator,
                    Some(qualification.evidence_sha256.clone()),
                    false,
                );
            }
        }
        let model = LayoutModel {
            width_per_advance_milli: 700,
            horizontal_padding_milli: 1_000,
            line_height_milli: 1_600,
            vertical_level_milli: 900,
            inline_baseline_percent: 85,
            display_baseline_percent: 85,
        };
        let (width, height, baseline) = estimate_from_model(metrics, base_unit, layout, model)?;
        self.finish(
            semantic_sha256,
            layout,
            base_unit,
            width,
            height,
            baseline,
            EquationLayoutSource::Provisional,
            None,
            true,
        )
    }

    #[allow(clippy::too_many_arguments)]
    fn finish(
        &self,
        semantic_sha256: String,
        layout: EquationLayoutMode,
        base_unit: u32,
        width_hwpunit: u32,
        height_hwpunit: u32,
        baseline_percent: u8,
        source: EquationLayoutSource,
        source_evidence_sha256: Option<String>,
        render_required: bool,
    ) -> Result<EquationLayoutEstimate, EquationLayoutError> {
        if width_hwpunit == 0
            || height_hwpunit == 0
            || width_hwpunit > self.limits.0.extent_hwpunit
            || height_hwpunit > self.limits.0.extent_hwpunit
            || !(1..=100).contains(&baseline_percent)
            || (source == EquationLayoutSource::Provisional)
                != (source_evidence_sha256.is_none() && render_required)
        {
            return Err(EquationLayoutError::OutputLimit);
        }
        Ok(EquationLayoutEstimate {
            schema_version: EQUATION_LAYOUT_SCHEMA_VERSION,
            profile_version: EQUATION_LAYOUT_PROFILE_VERSION,
            semantic_sha256,
            layout,
            base_unit,
            width_hwpunit,
            height_hwpunit,
            baseline_percent,
            source,
            source_evidence_sha256,
            render_required,
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct EquationLayoutMetrics {
    advance_units: u32,
    above_levels: u32,
    below_levels: u32,
    nodes: u32,
    depth: u32,
    matrix_rows: u32,
    matrix_columns: u32,
}

impl EquationLayoutMetrics {
    #[must_use]
    pub const fn advance_units(self) -> u32 {
        self.advance_units
    }

    #[must_use]
    pub const fn above_levels(self) -> u32 {
        self.above_levels
    }

    #[must_use]
    pub const fn below_levels(self) -> u32 {
        self.below_levels
    }

    #[must_use]
    pub const fn nodes(self) -> u32 {
        self.nodes
    }

    #[must_use]
    pub const fn depth(self) -> u32 {
        self.depth
    }

    #[must_use]
    pub const fn matrix_rows(self) -> u32 {
        self.matrix_rows
    }

    #[must_use]
    pub const fn matrix_columns(self) -> u32 {
        self.matrix_columns
    }

    fn leaf(advance_units: u32) -> Self {
        Self {
            advance_units: cmp::max(1, advance_units),
            above_levels: 0,
            below_levels: 0,
            nodes: 1,
            depth: 1,
            matrix_rows: 0,
            matrix_columns: 0,
        }
    }

    fn vertical_levels(self) -> Result<u32, EquationLayoutError> {
        checked_add(self.above_levels, self.below_levels)
    }
}

impl LayoutEnvelope {
    fn admits(self, metrics: EquationLayoutMetrics) -> bool {
        metrics.nodes <= self.maximum_nodes
            && metrics.depth <= self.maximum_depth
            && metrics.advance_units <= self.maximum_advance_units
            && metrics
                .vertical_levels()
                .is_ok_and(|value| value <= self.maximum_vertical_levels)
            && metrics.matrix_rows <= self.maximum_matrix_rows
            && metrics.matrix_columns <= self.maximum_matrix_columns
    }
}

fn validate_qualification(
    draft: QualificationDraft,
    limits: EquationLayoutLimits,
) -> Result<QualifiedLayout, EquationLayoutError> {
    if draft.schema_version != EQUATION_LAYOUT_QUALIFICATION_SCHEMA_VERSION
        || draft.profile_version != EQUATION_LAYOUT_PROFILE_VERSION
        || draft.target.build != EXACT_BUILD
        || draft.target.architecture != "x86"
        || draft.target.locale != "ko-KR"
        || draft.target.font_name != EXACT_FONT
    {
        return Err(EquationLayoutError::UnsupportedProfile);
    }
    for digest in [
        &draft.evidence_sha256,
        &draft.font_metrics_sha256,
        &draft.corpus_semantic_sha256,
    ] {
        require_digest(digest)?;
    }
    validate_model(draft.model)?;
    validate_envelope(draft.envelope, limits)?;
    let validation = draft.validation;
    if draft.exact_samples.len() > limits.0.samples
        || validation.sample_count != draft.exact_samples.len()
        || validation.inline_sample_count < MIN_INLINE_SAMPLES
        || validation.display_sample_count < MIN_DISPLAY_SAMPLES
        || validation.inline_sample_count + validation.display_sample_count
            != validation.sample_count
        || validation.extent_max_error_hwpunit > MAX_EXTENT_ERROR_HWPUNIT
        || validation.baseline_max_error_hwpunit > MAX_BASELINE_ERROR_HWPUNIT
        || validation.ink_box_overflow_count != 0
        || validation.clipping_count != 0
        || validation.overlap_count != 0
        || validation.silent_fallback_count != 0
        || !validation.all_pages_inspected
    {
        return Err(EquationLayoutError::FailedVisualQualification);
    }
    let mut keys = std::collections::HashSet::with_capacity(draft.exact_samples.len());
    let mut inline = 0;
    let mut display = 0;
    let mut extent_max_error = 0;
    let mut baseline_max_error = 0;
    for sample in &draft.exact_samples {
        require_digest(&sample.semantic_sha256)?;
        require_digest(&sample.native_readback_sha256)?;
        require_digest(&sample.render_evidence_sha256)?;
        validate_sample(sample, limits)?;
        let metrics = EquationLayoutMetrics::from(sample.metrics);
        if !draft.envelope.admits(metrics) {
            return Err(EquationLayoutError::InvalidQualification);
        }
        let (width, height, baseline) =
            estimate_from_model(metrics, sample.base_unit, sample.layout, draft.model)?;
        extent_max_error = cmp::max(
            extent_max_error,
            cmp::max(
                width.abs_diff(sample.width_hwpunit),
                height.abs_diff(sample.height_hwpunit),
            ),
        );
        let predicted_baseline = baseline_hwpunit(height, baseline)?;
        let observed_baseline = baseline_hwpunit(sample.height_hwpunit, sample.baseline_percent)?;
        baseline_max_error = cmp::max(
            baseline_max_error,
            predicted_baseline.abs_diff(observed_baseline),
        );
        if !keys.insert((
            sample.semantic_sha256.clone(),
            sample.layout,
            sample.base_unit,
        )) {
            return Err(EquationLayoutError::InvalidQualification);
        }
        match sample.layout {
            EquationLayoutMode::Inline => inline += 1,
            EquationLayoutMode::Display => display += 1,
        }
    }
    if inline != validation.inline_sample_count || display != validation.display_sample_count {
        return Err(EquationLayoutError::InvalidQualification);
    }
    if extent_max_error != validation.extent_max_error_hwpunit
        || baseline_max_error != validation.baseline_max_error_hwpunit
    {
        return Err(EquationLayoutError::InvalidQualification);
    }
    Ok(QualifiedLayout {
        evidence_sha256: draft.evidence_sha256,
        model: draft.model,
        envelope: draft.envelope,
        exact_samples: draft.exact_samples,
    })
}

fn validate_model(model: LayoutModel) -> Result<(), EquationLayoutError> {
    if model.width_per_advance_milli == 0
        || model.horizontal_padding_milli == 0
        || model.line_height_milli == 0
        || model.vertical_level_milli == 0
        || model.width_per_advance_milli > 10_000
        || model.horizontal_padding_milli > 100_000
        || model.line_height_milli > 100_000
        || model.vertical_level_milli > 100_000
        || !(1..=100).contains(&model.inline_baseline_percent)
        || !(1..=100).contains(&model.display_baseline_percent)
    {
        return Err(EquationLayoutError::InvalidQualification);
    }
    Ok(())
}

fn validate_envelope(
    envelope: LayoutEnvelope,
    limits: EquationLayoutLimits,
) -> Result<(), EquationLayoutError> {
    if envelope.maximum_nodes == 0
        || envelope.maximum_depth == 0
        || envelope.maximum_advance_units == 0
        || envelope.maximum_vertical_levels == 0
        || envelope.maximum_nodes > limits.0.metric_units
        || envelope.maximum_depth > limits.0.metric_units
        || envelope.maximum_advance_units > limits.0.metric_units
        || envelope.maximum_vertical_levels > limits.0.metric_units
        || envelope.maximum_matrix_rows > limits.0.metric_units
        || envelope.maximum_matrix_columns > limits.0.metric_units
    {
        return Err(EquationLayoutError::InvalidQualification);
    }
    Ok(())
}

fn validate_sample(
    sample: &ExactSample,
    limits: EquationLayoutLimits,
) -> Result<(), EquationLayoutError> {
    let ink = sample.ink_box;
    let right = checked_add(ink.left, ink.width)?;
    let bottom = checked_add(ink.top, ink.height)?;
    if sample.base_unit == 0
        || sample.base_unit > limits.0.base_unit
        || sample.width_hwpunit == 0
        || sample.width_hwpunit > limits.0.extent_hwpunit
        || sample.height_hwpunit == 0
        || sample.height_hwpunit > limits.0.extent_hwpunit
        || !(1..=100).contains(&sample.baseline_percent)
        || ink.page_width_pixels == 0
        || ink.page_width_pixels > limits.0.page_pixels
        || ink.page_height_pixels == 0
        || ink.page_height_pixels > limits.0.page_pixels
        || ink.width == 0
        || ink.height == 0
        || ink.dpi < 72
        || ink.dpi > 1_200
        || right >= ink.page_width_pixels
        || bottom >= ink.page_height_pixels
    {
        return Err(EquationLayoutError::InvalidQualification);
    }
    Ok(())
}

fn estimate_from_model(
    metrics: EquationLayoutMetrics,
    base_unit: u32,
    layout: EquationLayoutMode,
    model: LayoutModel,
) -> Result<(u32, u32, u8), EquationLayoutError> {
    let advance = u64::from(metrics.advance_units)
        .checked_mul(u64::from(model.width_per_advance_milli))
        .and_then(|value| value.checked_add(u64::from(model.horizontal_padding_milli)))
        .ok_or(EquationLayoutError::MetricOverflow)?;
    let levels = u64::from(metrics.vertical_levels()?);
    let vertical = levels
        .checked_mul(u64::from(model.vertical_level_milli))
        .and_then(|value| value.checked_add(u64::from(model.line_height_milli)))
        .ok_or(EquationLayoutError::MetricOverflow)?;
    let width = scale_milli(base_unit, advance)?;
    let height = scale_milli(base_unit, vertical)?;
    let baseline = match layout {
        EquationLayoutMode::Inline => model.inline_baseline_percent,
        EquationLayoutMode::Display => model.display_baseline_percent,
    };
    Ok((width, height, baseline))
}

fn scale_milli(base_unit: u32, milli: u64) -> Result<u32, EquationLayoutError> {
    let numerator = u64::from(base_unit)
        .checked_mul(milli)
        .and_then(|value| value.checked_add(999))
        .ok_or(EquationLayoutError::MetricOverflow)?;
    u32::try_from(numerator / 1_000).map_err(|_| EquationLayoutError::MetricOverflow)
}

fn baseline_hwpunit(height: u32, baseline_percent: u8) -> Result<u32, EquationLayoutError> {
    let value = u64::from(height)
        .checked_mul(u64::from(baseline_percent))
        .and_then(|value| value.checked_add(50))
        .ok_or(EquationLayoutError::MetricOverflow)?
        / 100;
    u32::try_from(value).map_err(|_| EquationLayoutError::MetricOverflow)
}

#[allow(clippy::too_many_lines)]
fn measure_node(
    node: &MathNode,
    limits: EquationLayoutLimits,
    depth: u32,
) -> Result<EquationLayoutMetrics, EquationLayoutError> {
    if depth > limits.0.metric_units {
        return Err(EquationLayoutError::MetricLimit);
    }
    let leaf = matches!(
        &node.expression,
        MathExpression::Number { .. }
            | MathExpression::Identifier { .. }
            | MathExpression::Text { .. }
            | MathExpression::Symbol { .. }
    );
    let mut metrics = match &node.expression {
        MathExpression::Number { value } | MathExpression::Text { value } => {
            EquationLayoutMetrics::leaf(character_units(value)?)
        }
        MathExpression::Identifier { name } => EquationLayoutMetrics::leaf(character_units(name)?),
        MathExpression::Symbol { .. } => EquationLayoutMetrics::leaf(1),
        MathExpression::Row { items } => combine_horizontal(items.iter(), limits, depth, 0)?,
        MathExpression::Apply { arguments, .. } => {
            combine_horizontal(arguments.iter(), limits, depth, 1)?
        }
        MathExpression::Function {
            function,
            arguments,
        } => {
            let prefix = match function {
                MathFunction::Named { name } => character_units(name)?,
                _ => 3,
            };
            combine_horizontal(arguments.iter(), limits, depth, checked_add(prefix, 2)?)?
        }
        MathExpression::Fraction {
            numerator,
            denominator,
        } => {
            let upper = measure_node(numerator, limits, checked_add(depth, 1)?)?;
            let lower = measure_node(denominator, limits, checked_add(depth, 1)?)?;
            let mut result = merge_metrics(upper, lower)?;
            result.advance_units =
                checked_add(cmp::max(upper.advance_units, lower.advance_units), 2)?;
            result.above_levels = checked_add(upper.vertical_levels()?, 1)?;
            result.below_levels = checked_add(lower.vertical_levels()?, 1)?;
            result
        }
        MathExpression::Script {
            base,
            subscript,
            superscript,
        } => {
            let base = measure_node(base, limits, checked_add(depth, 1)?)?;
            let sub = optional_metrics(subscript.as_deref(), limits, depth)?;
            let sup = optional_metrics(superscript.as_deref(), limits, depth)?;
            let mut result = merge_metrics(merge_metrics(base, sub)?, sup)?;
            let script_advance = cmp::max(sub.advance_units, sup.advance_units).div_ceil(2);
            result.advance_units = checked_add(base.advance_units, script_advance)?;
            result.above_levels = cmp::max(
                base.above_levels,
                checked_add(sup.vertical_levels()?, u32::from(sup.nodes > 0))?,
            );
            result.below_levels = cmp::max(
                base.below_levels,
                checked_add(sub.vertical_levels()?, u32::from(sub.nodes > 0))?,
            );
            result
        }
        MathExpression::Root { degree, radicand } => {
            let body = measure_node(radicand, limits, checked_add(depth, 1)?)?;
            let degree = optional_metrics(degree.as_deref(), limits, depth)?;
            let mut result = merge_metrics(body, degree)?;
            result.advance_units = checked_add(
                body.advance_units,
                checked_add(2, degree.advance_units.div_ceil(2))?,
            )?;
            result.above_levels =
                checked_add(cmp::max(body.above_levels, degree.vertical_levels()?), 1)?;
            result
        }
        MathExpression::Accent { base, .. } => {
            let mut result = measure_node(base, limits, checked_add(depth, 1)?)?;
            result.above_levels = checked_add(result.above_levels, 1)?;
            result
        }
        MathExpression::Annotated {
            base, annotation, ..
        } => {
            let base = measure_node(base, limits, checked_add(depth, 1)?)?;
            let annotation = optional_metrics(annotation.as_deref(), limits, depth)?;
            let mut result = merge_metrics(base, annotation)?;
            result.advance_units = cmp::max(base.advance_units, annotation.advance_units);
            result.above_levels = checked_add(
                base.above_levels,
                checked_add(annotation.vertical_levels()?, 1)?,
            )?;
            result
        }
        MathExpression::LargeOperator {
            body, lower, upper, ..
        } => {
            let body = measure_node(body, limits, checked_add(depth, 1)?)?;
            let lower = optional_metrics(lower.as_deref(), limits, depth)?;
            let upper = optional_metrics(upper.as_deref(), limits, depth)?;
            let mut result = merge_metrics(merge_metrics(body, lower)?, upper)?;
            result.advance_units = checked_add(body.advance_units, 2)?;
            result.above_levels = checked_add(body.above_levels, upper.vertical_levels()?)?;
            result.below_levels = checked_add(body.below_levels, lower.vertical_levels()?)?;
            result
        }
        MathExpression::Derivative {
            expression,
            variables,
            ..
        } => {
            let expression = measure_node(expression, limits, checked_add(depth, 1)?)?;
            let variables = combine_derivatives(variables, limits, depth)?;
            let mut result = merge_metrics(expression, variables)?;
            result.advance_units = checked_add(
                expression.advance_units,
                checked_add(variables.advance_units, 2)?,
            )?;
            result.above_levels = checked_add(result.above_levels, 1)?;
            result.below_levels = checked_add(result.below_levels, 1)?;
            result
        }
        MathExpression::Delimited { body, .. } => {
            let mut result = measure_node(body, limits, checked_add(depth, 1)?)?;
            result.advance_units = checked_add(result.advance_units, 2)?;
            result
        }
        MathExpression::Matrix { rows, .. } => measure_matrix(rows, limits, depth, 2)?,
        MathExpression::Cases { cases } => measure_cases(cases, limits, depth)?,
        MathExpression::Aligned { lines } => measure_aligned(lines, limits, depth)?,
        MathExpression::Combinatorial { upper, lower, .. } => {
            let upper = measure_node(upper, limits, checked_add(depth, 1)?)?;
            let lower = measure_node(lower, limits, checked_add(depth, 1)?)?;
            let mut result = merge_metrics(upper, lower)?;
            result.advance_units =
                checked_add(cmp::max(upper.advance_units, lower.advance_units), 2)?;
            result.above_levels = checked_add(upper.vertical_levels()?, 1)?;
            result.below_levels = checked_add(lower.vertical_levels()?, 1)?;
            result
        }
        MathExpression::SetBuilder { element, condition } => {
            let element = measure_node(element, limits, checked_add(depth, 1)?)?;
            let condition = measure_node(condition, limits, checked_add(depth, 1)?)?;
            let mut result = merge_metrics(element, condition)?;
            result.advance_units = checked_add(
                checked_add(element.advance_units, condition.advance_units)?,
                3,
            )?;
            result
        }
    };
    if !leaf {
        metrics.nodes = checked_add(metrics.nodes, 1)?;
        metrics.depth = checked_add(metrics.depth, 1)?;
    }
    if metrics.nodes > limits.0.metric_units
        || metrics.advance_units > limits.0.metric_units
        || metrics.vertical_levels()? > limits.0.metric_units
    {
        return Err(EquationLayoutError::MetricLimit);
    }
    Ok(metrics)
}

fn optional_metrics(
    node: Option<&MathNode>,
    limits: EquationLayoutLimits,
    depth: u32,
) -> Result<EquationLayoutMetrics, EquationLayoutError> {
    node.map_or_else(
        || {
            Ok(EquationLayoutMetrics {
                advance_units: 0,
                above_levels: 0,
                below_levels: 0,
                nodes: 0,
                depth: 0,
                matrix_rows: 0,
                matrix_columns: 0,
            })
        },
        |value| measure_node(value, limits, checked_add(depth, 1)?),
    )
}

fn combine_horizontal<'a>(
    nodes: impl Iterator<Item = &'a MathNode>,
    limits: EquationLayoutLimits,
    depth: u32,
    extra_advance: u32,
) -> Result<EquationLayoutMetrics, EquationLayoutError> {
    let mut result = zero_metrics();
    result.advance_units = extra_advance;
    for node in nodes {
        let child = measure_node(node, limits, checked_add(depth, 1)?)?;
        let advance = checked_add(result.advance_units, child.advance_units)?;
        result = merge_metrics(result, child)?;
        result.advance_units = advance;
    }
    result.advance_units = cmp::max(1, result.advance_units);
    Ok(result)
}

fn combine_derivatives(
    variables: &[MathDerivativeVariable],
    limits: EquationLayoutLimits,
    depth: u32,
) -> Result<EquationLayoutMetrics, EquationLayoutError> {
    combine_horizontal(
        variables.iter().map(|value| value.variable.as_ref()),
        limits,
        depth,
        u32::try_from(variables.len()).map_err(|_| EquationLayoutError::MetricOverflow)?,
    )
}

fn measure_matrix(
    rows: &[Vec<MathNode>],
    limits: EquationLayoutLimits,
    depth: u32,
    delimiter_advance: u32,
) -> Result<EquationLayoutMetrics, EquationLayoutError> {
    let mut result = zero_metrics();
    result.advance_units = delimiter_advance;
    let mut maximum_row = 0;
    let mut maximum_columns = 0;
    for row in rows {
        let measured = combine_horizontal(
            row.iter(),
            limits,
            depth,
            u32::try_from(row.len().saturating_sub(1))
                .map_err(|_| EquationLayoutError::MetricOverflow)?,
        )?;
        maximum_row = cmp::max(maximum_row, measured.advance_units);
        maximum_columns = cmp::max(
            maximum_columns,
            u32::try_from(row.len()).map_err(|_| EquationLayoutError::MetricOverflow)?,
        );
        result = merge_metrics(result, measured)?;
    }
    let row_count = u32::try_from(rows.len()).map_err(|_| EquationLayoutError::MetricOverflow)?;
    result.advance_units = checked_add(maximum_row, delimiter_advance)?;
    result.above_levels = checked_add(row_count.div_ceil(2), 1)?;
    result.below_levels = checked_add(row_count / 2, 1)?;
    result.matrix_rows = cmp::max(result.matrix_rows, row_count);
    result.matrix_columns = cmp::max(result.matrix_columns, maximum_columns);
    Ok(result)
}

const fn zero_metrics() -> EquationLayoutMetrics {
    EquationLayoutMetrics {
        advance_units: 0,
        above_levels: 0,
        below_levels: 0,
        nodes: 0,
        depth: 0,
        matrix_rows: 0,
        matrix_columns: 0,
    }
}

fn measure_cases(
    cases: &[MathCase],
    limits: EquationLayoutLimits,
    depth: u32,
) -> Result<EquationLayoutMetrics, EquationLayoutError> {
    let rows = cases
        .iter()
        .map(|case| {
            let mut row = vec![case.value.clone()];
            if let Some(condition) = &case.condition {
                row.push(condition.clone());
            }
            row
        })
        .collect::<Vec<_>>();
    measure_matrix(&rows, limits, depth, 1)
}

fn measure_aligned(
    lines: &[MathAlignedLine],
    limits: EquationLayoutLimits,
    depth: u32,
) -> Result<EquationLayoutMetrics, EquationLayoutError> {
    let rows = lines
        .iter()
        .map(|line| line.cells.clone())
        .collect::<Vec<_>>();
    measure_matrix(&rows, limits, depth, 0)
}

fn merge_metrics(
    left: EquationLayoutMetrics,
    right: EquationLayoutMetrics,
) -> Result<EquationLayoutMetrics, EquationLayoutError> {
    Ok(EquationLayoutMetrics {
        advance_units: cmp::max(left.advance_units, right.advance_units),
        above_levels: cmp::max(left.above_levels, right.above_levels),
        below_levels: cmp::max(left.below_levels, right.below_levels),
        nodes: checked_add(left.nodes, right.nodes)?,
        depth: cmp::max(left.depth, right.depth),
        matrix_rows: cmp::max(left.matrix_rows, right.matrix_rows),
        matrix_columns: cmp::max(left.matrix_columns, right.matrix_columns),
    })
}

fn character_units(value: &str) -> Result<u32, EquationLayoutError> {
    u32::try_from(value.chars().count()).map_err(|_| EquationLayoutError::MetricOverflow)
}

fn checked_add(left: u32, right: u32) -> Result<u32, EquationLayoutError> {
    left.checked_add(right)
        .ok_or(EquationLayoutError::MetricOverflow)
}

fn require_digest(value: &str) -> Result<(), EquationLayoutError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(EquationLayoutError::InvalidQualification);
    }
    Ok(())
}

#[derive(Debug, Error, Clone, Copy, Eq, PartialEq)]
pub enum EquationLayoutError {
    #[error("equation layout limit configuration is invalid")]
    InvalidLimit,
    #[error("equation layout qualification is empty or oversized")]
    QualificationLimit,
    #[error("equation layout qualification is malformed, duplicated or unknown")]
    InvalidQualification,
    #[error("equation layout qualification digest is not trusted")]
    UntrustedQualification,
    #[error("equation layout target profile is unsupported")]
    UnsupportedProfile,
    #[error("equation layout visual qualification failed")]
    FailedVisualQualification,
    #[error("equation layout base unit is invalid")]
    InvalidBaseUnit,
    #[error("equation layout MathAst admission failed")]
    MathAst,
    #[error("equation layout metric limit was exceeded")]
    MetricLimit,
    #[error("equation layout metric arithmetic overflowed")]
    MetricOverflow,
    #[error("equation layout estimate exceeds its output bound")]
    OutputLimit,
    #[error("equation layout serialization failed")]
    Serialization,
}

impl EquationLayoutError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "equation_layout_invalid_limit",
            Self::QualificationLimit => "equation_layout_qualification_limit",
            Self::InvalidQualification => "equation_layout_invalid_qualification",
            Self::UntrustedQualification => "equation_layout_untrusted_qualification",
            Self::UnsupportedProfile => "equation_layout_unsupported_profile",
            Self::FailedVisualQualification => "equation_layout_failed_visual_qualification",
            Self::InvalidBaseUnit => "equation_layout_invalid_base_unit",
            Self::MathAst => "equation_layout_math_ast",
            Self::MetricLimit => "equation_layout_metric_limit",
            Self::MetricOverflow => "equation_layout_metric_overflow",
            Self::OutputLimit => "equation_layout_output_limit",
            Self::Serialization => "equation_layout_serialization",
        }
    }
}
