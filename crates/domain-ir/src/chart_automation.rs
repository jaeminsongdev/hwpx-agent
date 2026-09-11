use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, DeserializeSeed, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization;

use crate::{FormulaDecimal, LogicalId};

pub const CHART_AUTOMATION_SCHEMA_VERSION: &str = "hwpx-agent.chart-automation/v1";

const REQUIRED_CAPABILITIES: [&str; 9] = [
    "obj.chart_axis",
    "obj.chart_data",
    "obj.chart_insert",
    "obj.chart_labels",
    "obj.chart_legend",
    "obj.chart_series",
    "obj.chart_style",
    "obj.chart_title",
    "obj.chart_type",
];
const COUNT_LIMIT_CEILING: usize = 1_000_000;
const BYTE_LIMIT_CEILING: usize = 256 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ChartAutomationLimitConfig {
    pub input_bytes: usize,
    pub serialized_bytes: usize,
    pub charts: usize,
    pub rows: usize,
    pub columns: usize,
    pub series: usize,
    pub axes: usize,
    pub type_bindings: usize,
    pub style_bindings: usize,
    pub identifier_bytes: usize,
    pub text_bytes: usize,
    pub opaque_bytes: u64,
    pub export_bytes: u64,
    pub decimal_scale: u8,
}

impl Default for ChartAutomationLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 4 * 1024 * 1024,
            serialized_bytes: 32 * 1024 * 1024,
            charts: 16_384,
            rows: 65_536,
            columns: 16_384,
            series: 16_384,
            axes: 4,
            type_bindings: 512,
            style_bindings: 4_096,
            identifier_bytes: 512,
            text_bytes: 64 * 1024,
            opaque_bytes: 256 * 1024 * 1024,
            export_bytes: 256 * 1024 * 1024,
            decimal_scale: 18,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ChartAutomationLimits(ChartAutomationLimitConfig);

impl ChartAutomationLimits {
    /// Creates finite limits for untrusted target profiles, chart states and requests.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or process-hostile configurations.
    pub fn new(config: ChartAutomationLimitConfig) -> Result<Self, ChartAutomationError> {
        let counts = [
            config.charts,
            config.rows,
            config.columns,
            config.series,
            config.axes,
            config.type_bindings,
            config.style_bindings,
        ];
        if config.input_bytes == 0
            || config.serialized_bytes == 0
            || config.input_bytes > config.serialized_bytes
            || config.serialized_bytes > BYTE_LIMIT_CEILING
            || counts
                .into_iter()
                .any(|value| value == 0 || value > COUNT_LIMIT_CEILING)
            || config.axes > 4
            || config.identifier_bytes == 0
            || config.identifier_bytes > 4 * 1024 * 1024
            || config.text_bytes == 0
            || config.text_bytes > BYTE_LIMIT_CEILING
            || config.opaque_bytes == 0
            || config.opaque_bytes > BYTE_LIMIT_CEILING as u64
            || config.export_bytes == 0
            || config.export_bytes > BYTE_LIMIT_CEILING as u64
            || config.decimal_scale > 18
        {
            return Err(ChartAutomationError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ChartAutomationLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartFamily {
    HorizontalBar,
    VerticalBar,
    Line,
    Area,
    Pie,
    Doughnut,
    Scatter,
    Bubble,
    Stock,
    Radar,
    Surface,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartDimension {
    TwoDimensional,
    ThreeDimensional,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartStacking {
    None,
    Stacked,
    Percent,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ChartTypeBinding {
    pub binding_id: LogicalId,
    pub family: ChartFamily,
    pub dimension: ChartDimension,
    pub allowed_stacking: Vec<ChartStacking>,
    pub semantic_profile_sha256: String,
}

impl fmt::Debug for ChartTypeBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartTypeBinding")
            .field("family", &self.family)
            .field("dimension", &self.dimension)
            .field("allowed_stacking", &self.allowed_stacking)
            .field("binding_and_digest", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ChartStyleBinding {
    pub style_id: LogicalId,
    pub binding_id: LogicalId,
    pub semantic_profile_sha256: String,
}

impl fmt::Debug for ChartStyleBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartStyleBinding")
            .field("mapping", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ChartAutomationBinding {
    pub capability_id: String,
    pub binding_id: LogicalId,
    pub parameter_schema_sha256: String,
    pub readback_schema_sha256: String,
}

impl fmt::Debug for ChartAutomationBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationBinding")
            .field("capability_id", &self.capability_id)
            .field("binding_and_schemas", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ChartAutomationProfileDraft {
    pub schema_version: String,
    pub profile_id: LogicalId,
    pub product: String,
    pub version: String,
    pub architecture: String,
    pub locale: String,
    pub executable_sha256: String,
    pub catalog_sha256: String,
    pub readback_adapter_sha256: String,
    pub type_bindings: Vec<ChartTypeBinding>,
    pub style_bindings: Vec<ChartStyleBinding>,
    pub automation_bindings: Vec<ChartAutomationBinding>,
}

impl fmt::Debug for ChartAutomationProfileDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationProfileDraft")
            .field("type_bindings", &self.type_bindings.len())
            .field("style_bindings", &self.style_bindings.len())
            .field("automation_bindings", &self.automation_bindings.len())
            .field("target_and_digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ChartAutomationProfile {
    schema_version: &'static str,
    profile_id: LogicalId,
    product: String,
    version: String,
    architecture: String,
    locale: String,
    executable_sha256: String,
    catalog_sha256: String,
    readback_adapter_sha256: String,
    type_bindings: Vec<ChartTypeBinding>,
    style_bindings: Vec<ChartStyleBinding>,
    automation_bindings: Vec<ChartAutomationBinding>,
}

impl ChartAutomationProfile {
    /// Admits one complete installed-target chart automation profile.
    ///
    /// # Errors
    ///
    /// Rejects missing capabilities, duplicate mappings, malformed digests or noncanonical text.
    pub fn from_draft(
        draft: ChartAutomationProfileDraft,
        limits: ChartAutomationLimits,
    ) -> Result<Self, ChartAutomationError> {
        if draft.schema_version != CHART_AUTOMATION_SCHEMA_VERSION {
            return Err(ChartAutomationError::UnsupportedVersion);
        }
        validate_id(&draft.profile_id, limits)?;
        for text in [
            &draft.product,
            &draft.version,
            &draft.architecture,
            &draft.locale,
        ] {
            validate_text(text, limits, false)?;
        }
        for digest in [
            &draft.executable_sha256,
            &draft.catalog_sha256,
            &draft.readback_adapter_sha256,
        ] {
            require_digest(digest)?;
        }
        if draft.type_bindings.is_empty()
            || draft.type_bindings.len() > limits.0.type_bindings
            || draft.style_bindings.is_empty()
            || draft.style_bindings.len() > limits.0.style_bindings
            || draft.automation_bindings.len() != REQUIRED_CAPABILITIES.len()
        {
            return Err(ChartAutomationError::InvalidProfile);
        }
        let mut type_keys = BTreeSet::new();
        let mut binding_ids = BTreeSet::new();
        for binding in &draft.type_bindings {
            validate_id(&binding.binding_id, limits)?;
            require_digest(&binding.semantic_profile_sha256)?;
            if binding.allowed_stacking.is_empty()
                || !strictly_sorted_unique(&binding.allowed_stacking)
                || !binding_ids.insert(binding.binding_id.clone())
                || !type_keys.insert((binding.family, binding.dimension))
            {
                return Err(ChartAutomationError::InvalidProfile);
            }
        }
        if !strictly_sorted_by(&draft.type_bindings, |value| {
            (value.family, value.dimension)
        }) {
            return Err(ChartAutomationError::InvalidProfile);
        }
        let mut style_ids = BTreeSet::new();
        for binding in &draft.style_bindings {
            validate_id(&binding.style_id, limits)?;
            validate_id(&binding.binding_id, limits)?;
            require_digest(&binding.semantic_profile_sha256)?;
            if !style_ids.insert(binding.style_id.clone())
                || !binding_ids.insert(binding.binding_id.clone())
            {
                return Err(ChartAutomationError::InvalidProfile);
            }
        }
        if !strictly_sorted_by(&draft.style_bindings, |value| value.style_id.clone()) {
            return Err(ChartAutomationError::InvalidProfile);
        }
        let mut actual_capabilities = Vec::with_capacity(REQUIRED_CAPABILITIES.len());
        for binding in &draft.automation_bindings {
            validate_text(&binding.capability_id, limits, false)?;
            validate_id(&binding.binding_id, limits)?;
            require_digest(&binding.parameter_schema_sha256)?;
            require_digest(&binding.readback_schema_sha256)?;
            if !binding_ids.insert(binding.binding_id.clone()) {
                return Err(ChartAutomationError::InvalidProfile);
            }
            actual_capabilities.push(binding.capability_id.as_str());
        }
        if actual_capabilities.as_slice() != REQUIRED_CAPABILITIES {
            return Err(ChartAutomationError::InvalidProfile);
        }
        let profile = Self {
            schema_version: CHART_AUTOMATION_SCHEMA_VERSION,
            profile_id: draft.profile_id,
            product: draft.product,
            version: draft.version,
            architecture: draft.architecture,
            locale: draft.locale,
            executable_sha256: draft.executable_sha256,
            catalog_sha256: draft.catalog_sha256,
            readback_adapter_sha256: draft.readback_adapter_sha256,
            type_bindings: draft.type_bindings,
            style_bindings: draft.style_bindings,
            automation_bindings: draft.automation_bindings,
        };
        let _ = profile.canonical_json(limits)?;
        Ok(profile)
    }

    /// Parses bounded duplicate-key-free strict JSON into a target profile.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized or incomplete profiles.
    pub fn from_json(
        bytes: &[u8],
        limits: ChartAutomationLimits,
    ) -> Result<Self, ChartAutomationError> {
        validate_input(bytes, limits)?;
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| ChartAutomationError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub const fn profile_id(&self) -> &LogicalId {
        &self.profile_id
    }

    fn automation_binding(
        &self,
        capability_id: &str,
    ) -> Result<&ChartAutomationBinding, ChartAutomationError> {
        self.automation_bindings
            .iter()
            .find(|value| value.capability_id == capability_id)
            .ok_or(ChartAutomationError::InvalidProfile)
    }

    fn type_binding(
        &self,
        selection: &ChartTypeSelection,
    ) -> Result<&ChartTypeBinding, ChartAutomationError> {
        let binding = self
            .type_bindings
            .iter()
            .find(|value| {
                value.binding_id == selection.binding_id
                    && value.family == selection.family
                    && value.dimension == selection.dimension
            })
            .ok_or(ChartAutomationError::UnsupportedChartType)?;
        if !binding.allowed_stacking.contains(&selection.stacking) {
            return Err(ChartAutomationError::UnsupportedChartType);
        }
        Ok(binding)
    }

    fn style_binding(
        &self,
        style_id: &LogicalId,
        binding_id: &LogicalId,
    ) -> Result<&ChartStyleBinding, ChartAutomationError> {
        self.style_bindings
            .iter()
            .find(|value| value.style_id == *style_id && value.binding_id == *binding_id)
            .ok_or(ChartAutomationError::UnsupportedStyle)
    }

    /// Emits bounded compact deterministic JSON for profile identity binding.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ChartAutomationLimits,
    ) -> Result<Vec<u8>, ChartAutomationError> {
        serialize_bounded(self, limits)
    }

    /// Computes the exact canonical profile digest.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_sha256(
        &self,
        limits: ChartAutomationLimits,
    ) -> Result<String, ChartAutomationError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for ChartAutomationProfile {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationProfile")
            .field("type_bindings", &self.type_bindings.len())
            .field("style_bindings", &self.style_bindings.len())
            .field("automation_bindings", &self.automation_bindings.len())
            .field("target", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartDataOrientation {
    SeriesByRows,
    SeriesByColumns,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ChartDataProvenance {
    Embedded {
        resource_id: LogicalId,
    },
    LinkedTable {
        table_id: LogicalId,
        table_state_sha256: String,
        range_sha256: String,
    },
    AutomationEditor {
        resource_id: LogicalId,
    },
}

impl fmt::Debug for ChartDataProvenance {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartDataProvenance")
            .field(
                "kind",
                &match self {
                    Self::Embedded { .. } => "embedded",
                    Self::LinkedTable { .. } => "linked_table",
                    Self::AutomationEditor { .. } => "automation_editor",
                },
            )
            .field("binding", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", content = "value", rename_all = "snake_case")]
pub enum ChartValue {
    Number(FormulaDecimal),
    Blank,
}

impl fmt::Debug for ChartValue {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Number(_) => formatter.write_str("Number(<redacted>)"),
            Self::Blank => formatter.write_str("Blank"),
        }
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ChartDataState {
    pub orientation: ChartDataOrientation,
    pub row_labels: Vec<String>,
    pub column_labels: Vec<String>,
    pub values: Vec<ChartValue>,
    pub provenance: ChartDataProvenance,
}

impl fmt::Debug for ChartDataState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartDataState")
            .field("orientation", &self.orientation)
            .field("rows", &self.row_labels.len())
            .field("columns", &self.column_labels.len())
            .field("values", &self.values.len())
            .field("provenance", &self.provenance)
            .field("labels_and_values", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ChartTypeSelection {
    pub binding_id: LogicalId,
    pub family: ChartFamily,
    pub dimension: ChartDimension,
    pub stacking: ChartStacking,
}

impl fmt::Debug for ChartTypeSelection {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartTypeSelection")
            .field("family", &self.family)
            .field("dimension", &self.dimension)
            .field("stacking", &self.stacking)
            .field("binding", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartSeriesAxis {
    Primary,
    Secondary,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartMarkerKind {
    None,
    Automatic,
    Circle,
    Square,
    Diamond,
    Triangle,
    Cross,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)] // Independent native series properties are not one state machine.
pub struct ChartSeriesState {
    pub order: u32,
    pub label: String,
    pub hidden: bool,
    pub excluded: bool,
    pub axis: ChartSeriesAxis,
    pub stacked_with_previous: bool,
    pub line_visible: bool,
    pub marker: ChartMarkerKind,
    pub style_sha256: String,
}

impl fmt::Debug for ChartSeriesState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartSeriesState")
            .field("order", &self.order)
            .field("hidden", &self.hidden)
            .field("excluded", &self.excluded)
            .field("axis", &self.axis)
            .field("stacked_with_previous", &self.stacked_with_previous)
            .field("line_visible", &self.line_visible)
            .field("marker", &self.marker)
            .field("content", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartAxisKind {
    CategoryX,
    ValueY,
    SecondaryValueY,
    DepthZ,
}

#[derive(Clone, Copy, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ChartAxisScale {
    Automatic,
    Manual {
        minimum: FormulaDecimal,
        maximum: FormulaDecimal,
        major_unit: FormulaDecimal,
        minor_unit: FormulaDecimal,
    },
}

impl fmt::Debug for ChartAxisScale {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Automatic => formatter.write_str("Automatic"),
            Self::Manual { .. } => formatter.write_str("Manual(<redacted>)"),
        }
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)] // Native axis switches are independently readable properties.
pub struct ChartAxisState {
    pub kind: ChartAxisKind,
    pub visible: bool,
    pub reverse_order: bool,
    pub logarithmic: bool,
    pub scale: ChartAxisScale,
    pub title: Option<String>,
    pub number_format: String,
    pub major_gridlines: bool,
    pub minor_gridlines: bool,
    pub style_sha256: String,
}

impl fmt::Debug for ChartAxisState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAxisState")
            .field("kind", &self.kind)
            .field("visible", &self.visible)
            .field("reverse_order", &self.reverse_order)
            .field("logarithmic", &self.logarithmic)
            .field("scale", &"<redacted>")
            .field("title", &self.title.as_ref().map(|_| "<redacted>"))
            .field("gridlines", &(self.major_gridlines, self.minor_gridlines))
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartLegendPosition {
    Top,
    Bottom,
    LeftCenter,
    RightCenter,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ChartLegendState {
    pub visible: bool,
    pub position: ChartLegendPosition,
    pub overlay: bool,
    pub style_sha256: String,
}

impl fmt::Debug for ChartLegendState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartLegendState")
            .field("visible", &self.visible)
            .field("position", &self.position)
            .field("overlay", &self.overlay)
            .field("style", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartLabelPosition {
    Automatic,
    Center,
    InsideEnd,
    InsideBase,
    OutsideEnd,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)] // Each data-label visibility flag has separate semantics.
pub struct ChartLabelsState {
    pub visible: bool,
    pub show_series_name: bool,
    pub show_category_name: bool,
    pub show_value: bool,
    pub show_percentage: bool,
    pub position: ChartLabelPosition,
    pub number_format: String,
    pub style_sha256: String,
}

impl fmt::Debug for ChartLabelsState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartLabelsState")
            .field("visible", &self.visible)
            .field("show_series_name", &self.show_series_name)
            .field("show_category_name", &self.show_category_name)
            .field("show_value", &self.show_value)
            .field("show_percentage", &self.show_percentage)
            .field("position", &self.position)
            .field("format_and_style", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChartTitlePosition {
    Above,
    CenterOverlay,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ChartTitleState {
    pub visible: bool,
    pub position: ChartTitlePosition,
    pub text: Option<String>,
    pub style_sha256: String,
}

impl fmt::Debug for ChartTitleState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartTitleState")
            .field("visible", &self.visible)
            .field("position", &self.position)
            .field("has_text", &self.text.is_some())
            .field("content_and_style", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ChartIdentity {
    pub chart_id: LogicalId,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub data_resource_id: LogicalId,
    pub chart_part_id: LogicalId,
}

impl fmt::Debug for ChartIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartIdentity")
            .field("identity", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ChartState {
    pub identity: ChartIdentity,
    pub chart_type: ChartTypeSelection,
    pub data: ChartDataState,
    pub series: Vec<ChartSeriesState>,
    pub axes: Vec<ChartAxisState>,
    pub legend: ChartLegendState,
    pub labels: ChartLabelsState,
    pub title: ChartTitleState,
    pub style_id: LogicalId,
    pub style_binding_id: LogicalId,
    pub geometry_sha256: String,
    pub composition_sha256: String,
    pub appearance_sha256: String,
    pub opaque_semantics_sha256: String,
    pub opaque_semantics_bytes: u64,
}

impl fmt::Debug for ChartState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartState")
            .field("chart_type", &self.chart_type)
            .field("data", &self.data)
            .field("series", &self.series.len())
            .field("axes", &self.axes.len())
            .field("legend_visible", &self.legend.visible)
            .field("labels_visible", &self.labels.visible)
            .field("title_visible", &self.title.visible)
            .field("identity_and_content", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ChartDocumentStateDraft {
    pub schema_version: String,
    pub target_profile_id: LogicalId,
    pub external_object_inventory_sha256: String,
    pub charts: Vec<ChartState>,
}

impl fmt::Debug for ChartDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartDocumentStateDraft")
            .field("charts", &self.charts.len())
            .field("profile_and_inventory", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ChartDocumentState {
    schema_version: &'static str,
    target_profile_id: LogicalId,
    external_object_inventory_sha256: String,
    charts: Vec<ChartState>,
}

impl ChartDocumentState {
    /// Admits a complete chart-state projection bound to one target automation profile.
    ///
    /// # Errors
    ///
    /// Rejects incomplete, conflicting, noncanonical or unsupported chart state.
    pub fn from_draft(
        draft: ChartDocumentStateDraft,
        profile: &ChartAutomationProfile,
        limits: ChartAutomationLimits,
    ) -> Result<Self, ChartAutomationError> {
        if draft.schema_version != CHART_AUTOMATION_SCHEMA_VERSION {
            return Err(ChartAutomationError::UnsupportedVersion);
        }
        if draft.target_profile_id != *profile.profile_id() {
            return Err(ChartAutomationError::ProfileDrift);
        }
        require_digest(&draft.external_object_inventory_sha256)?;
        if draft.charts.len() > limits.0.charts {
            return Err(ChartAutomationError::InputLimit);
        }
        if !strictly_sorted_by(&draft.charts, |chart| chart.identity.chart_id.clone()) {
            return Err(ChartAutomationError::InvalidIdentity);
        }
        let mut logical = BTreeSet::new();
        let mut native_objects = BTreeSet::new();
        let mut native_instances = BTreeSet::new();
        for chart in &draft.charts {
            validate_chart(chart, profile, limits)?;
            for id in [
                &chart.identity.chart_id,
                &chart.identity.data_resource_id,
                &chart.identity.chart_part_id,
            ] {
                if !logical.insert(id.clone()) {
                    return Err(ChartAutomationError::InvalidIdentity);
                }
            }
            if !native_objects.insert(chart.identity.native_object_id)
                || !native_instances.insert(chart.identity.native_instance_id)
            {
                return Err(ChartAutomationError::InvalidIdentity);
            }
        }
        for chart in &draft.charts {
            if let ChartDataProvenance::LinkedTable { table_id, .. } = &chart.data.provenance
                && logical.contains(table_id)
            {
                return Err(ChartAutomationError::InvalidIdentity);
            }
        }
        let state = Self {
            schema_version: CHART_AUTOMATION_SCHEMA_VERSION,
            target_profile_id: draft.target_profile_id,
            external_object_inventory_sha256: draft.external_object_inventory_sha256,
            charts: draft.charts,
        };
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    /// Parses bounded duplicate-key-free strict JSON against the exact target profile.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized or invalid state.
    pub fn from_json(
        bytes: &[u8],
        profile: &ChartAutomationProfile,
        limits: ChartAutomationLimits,
    ) -> Result<Self, ChartAutomationError> {
        validate_input(bytes, limits)?;
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| ChartAutomationError::InvalidJson)?;
        Self::from_draft(draft, profile, limits)
    }

    #[must_use]
    pub fn charts(&self) -> &[ChartState] {
        &self.charts
    }

    #[must_use]
    pub fn chart(&self, id: &LogicalId) -> Option<&ChartState> {
        self.charts
            .binary_search_by(|chart| chart.identity.chart_id.cmp(id))
            .ok()
            .map(|index| &self.charts[index])
    }

    /// Emits bounded compact deterministic JSON.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ChartAutomationLimits,
    ) -> Result<Vec<u8>, ChartAutomationError> {
        serialize_bounded(self, limits)
    }

    /// Computes the exact canonical state digest.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_sha256(
        &self,
        limits: ChartAutomationLimits,
    ) -> Result<String, ChartAutomationError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }

    fn apply(
        &self,
        operation: &ChartOperation,
        profile: &ChartAutomationProfile,
        limits: ChartAutomationLimits,
    ) -> Result<Self, ChartAutomationError> {
        let mut target = self.clone();
        match operation {
            ChartOperation::Insert { chart, reservation } => {
                validate_reservation(reservation, chart, self, limits)?;
                if self.chart(&chart.identity.chart_id).is_some() {
                    return Err(ChartAutomationError::InvalidIdentity);
                }
                target.charts.push((**chart).clone());
                target
                    .charts
                    .sort_by(|left, right| left.identity.chart_id.cmp(&right.identity.chart_id));
                target
                    .external_object_inventory_sha256
                    .clone_from(&reservation.after_external_object_inventory_sha256);
            }
            ChartOperation::SetType {
                chart_id,
                chart_type,
            } => {
                chart_mut(&mut target.charts, chart_id)?.chart_type = chart_type.clone();
            }
            ChartOperation::ReplaceData {
                chart_id,
                data,
                series,
            } => {
                let chart = chart_mut(&mut target.charts, chart_id)?;
                chart.data = data.clone();
                chart.series.clone_from(series);
            }
            ChartOperation::UpdateSeries { chart_id, series } => {
                let chart = chart_mut(&mut target.charts, chart_id)?;
                let index = usize::try_from(series.order)
                    .map_err(|_| ChartAutomationError::InvalidSeries)?;
                if index >= chart.series.len() {
                    return Err(ChartAutomationError::InvalidSeries);
                }
                chart.series[index] = series.clone();
            }
            ChartOperation::UpdateAxis { chart_id, axis } => {
                let chart = chart_mut(&mut target.charts, chart_id)?;
                match chart
                    .axes
                    .binary_search_by_key(&axis.kind, |value| value.kind)
                {
                    Ok(index) => chart.axes[index] = axis.clone(),
                    Err(index) => chart.axes.insert(index, axis.clone()),
                }
            }
            ChartOperation::SetLegend { chart_id, legend } => {
                chart_mut(&mut target.charts, chart_id)?.legend = legend.clone();
            }
            ChartOperation::SetLabels { chart_id, labels } => {
                chart_mut(&mut target.charts, chart_id)?.labels = labels.clone();
            }
            ChartOperation::SetTitle { chart_id, title } => {
                chart_mut(&mut target.charts, chart_id)?.title = title.clone();
            }
            ChartOperation::SetStyle {
                chart_id,
                style_id,
                style_binding_id,
                appearance_sha256,
            } => {
                let chart = chart_mut(&mut target.charts, chart_id)?;
                chart.style_id = style_id.clone();
                chart.style_binding_id = style_binding_id.clone();
                chart.appearance_sha256.clone_from(appearance_sha256);
            }
        }
        let validated = Self::from_draft(
            ChartDocumentStateDraft {
                schema_version: CHART_AUTOMATION_SCHEMA_VERSION.to_owned(),
                target_profile_id: target.target_profile_id,
                external_object_inventory_sha256: target.external_object_inventory_sha256,
                charts: target.charts,
            },
            profile,
            limits,
        )?;
        if validated == *self {
            return Err(ChartAutomationError::NoChange);
        }
        Ok(validated)
    }
}

impl fmt::Debug for ChartDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartDocumentState")
            .field("charts", &self.charts.len())
            .field("profile_and_state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ChartIdentityReservation {
    pub chart_id: LogicalId,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub data_resource_id: LogicalId,
    pub chart_part_id: LogicalId,
    pub before_external_object_inventory_sha256: String,
    pub after_external_object_inventory_sha256: String,
    pub allocator_proof_sha256: String,
}

impl fmt::Debug for ChartIdentityReservation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartIdentityReservation")
            .field("reservation", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ChartOperation {
    Insert {
        chart: Box<ChartState>,
        reservation: ChartIdentityReservation,
    },
    SetType {
        chart_id: LogicalId,
        chart_type: ChartTypeSelection,
    },
    ReplaceData {
        chart_id: LogicalId,
        data: ChartDataState,
        series: Vec<ChartSeriesState>,
    },
    UpdateSeries {
        chart_id: LogicalId,
        series: ChartSeriesState,
    },
    UpdateAxis {
        chart_id: LogicalId,
        axis: ChartAxisState,
    },
    SetLegend {
        chart_id: LogicalId,
        legend: ChartLegendState,
    },
    SetLabels {
        chart_id: LogicalId,
        labels: ChartLabelsState,
    },
    SetTitle {
        chart_id: LogicalId,
        title: ChartTitleState,
    },
    SetStyle {
        chart_id: LogicalId,
        style_id: LogicalId,
        style_binding_id: LogicalId,
        appearance_sha256: String,
    },
}

impl ChartOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::Insert { .. } => "obj.chart_insert",
            Self::SetType { .. } => "obj.chart_type",
            Self::ReplaceData { .. } => "obj.chart_data",
            Self::UpdateSeries { .. } => "obj.chart_series",
            Self::UpdateAxis { .. } => "obj.chart_axis",
            Self::SetLegend { .. } => "obj.chart_legend",
            Self::SetLabels { .. } => "obj.chart_labels",
            Self::SetTitle { .. } => "obj.chart_title",
            Self::SetStyle { .. } => "obj.chart_style",
        }
    }

    fn target_chart_id(&self) -> &LogicalId {
        match self {
            Self::Insert { chart, .. } => &chart.identity.chart_id,
            Self::SetType { chart_id, .. }
            | Self::ReplaceData { chart_id, .. }
            | Self::UpdateSeries { chart_id, .. }
            | Self::UpdateAxis { chart_id, .. }
            | Self::SetLegend { chart_id, .. }
            | Self::SetLabels { chart_id, .. }
            | Self::SetTitle { chart_id, .. }
            | Self::SetStyle { chart_id, .. } => chart_id,
        }
    }
}

impl fmt::Debug for ChartOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartOperation")
            .field("capability_id", &self.capability_id())
            .field("target_and_payload", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ChartAutomationRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_profile_sha256: String,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: ChartOperation,
}

impl fmt::Debug for ChartAutomationRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationRequestDraft")
            .field("capability_id", &self.operation.capability_id())
            .field("identity_and_bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ChartAutomationRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_profile_sha256: String,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ChartOperation,
}

impl ChartAutomationRequest {
    /// Admits one exact profile/state/flow-bound automation transition.
    ///
    /// # Errors
    ///
    /// Rejects invalid bindings, unavailable mappings, drift or invalid/no-op transitions.
    pub fn from_draft(
        draft: ChartAutomationRequestDraft,
        profile: &ChartAutomationProfile,
        source: &ChartDocumentState,
        current_document_flow_sha256: &str,
        limits: ChartAutomationLimits,
    ) -> Result<Self, ChartAutomationError> {
        if draft.schema_version != CHART_AUTOMATION_SCHEMA_VERSION {
            return Err(ChartAutomationError::UnsupportedVersion);
        }
        validate_id(&draft.request_id, limits)?;
        for digest in [
            &draft.expected_profile_sha256,
            &draft.expected_source_state_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        if profile.canonical_sha256(limits)? != draft.expected_profile_sha256 {
            return Err(ChartAutomationError::ProfileDrift);
        }
        if source.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(ChartAutomationError::SourceStateDrift);
        }
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(ChartAutomationError::DocumentFlowDrift);
        }
        let _ = profile.automation_binding(draft.operation.capability_id())?;
        validate_id(draft.operation.target_chart_id(), limits)?;
        let _ = source.apply(&draft.operation, profile, limits)?;
        let request = Self {
            schema_version: CHART_AUTOMATION_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_profile_sha256: draft.expected_profile_sha256,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses bounded duplicate-key-free strict JSON and validates the exact source/profile.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized, invalid or stale requests.
    pub fn from_json(
        bytes: &[u8],
        profile: &ChartAutomationProfile,
        source: &ChartDocumentState,
        current_document_flow_sha256: &str,
        limits: ChartAutomationLimits,
    ) -> Result<Self, ChartAutomationError> {
        validate_input(bytes, limits)?;
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| ChartAutomationError::InvalidJson)?;
        Self::from_draft(draft, profile, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn operation(&self) -> &ChartOperation {
        &self.operation
    }

    /// Emits bounded compact deterministic JSON.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ChartAutomationLimits,
    ) -> Result<Vec<u8>, ChartAutomationError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ChartAutomationRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("identity_and_bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ChartAutomationPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    target_chart_id: LogicalId,
    profile_sha256: String,
    binding_id: LogicalId,
    parameter_schema_sha256: String,
    readback_schema_sha256: String,
    source_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ChartOperation,
    target_state: ChartDocumentState,
    target_state_sha256: String,
    request_sha256: String,
    plan_sha256: String,
}

impl ChartAutomationPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn target_state(&self) -> &ChartDocumentState {
        &self.target_state
    }

    #[must_use]
    pub fn target_state_sha256(&self) -> &str {
        &self.target_state_sha256
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    #[must_use]
    pub const fn target_chart_id(&self) -> &LogicalId {
        &self.target_chart_id
    }

    #[must_use]
    pub const fn binding_id(&self) -> &LogicalId {
        &self.binding_id
    }

    #[must_use]
    pub fn parameter_schema_sha256(&self) -> &str {
        &self.parameter_schema_sha256
    }

    #[must_use]
    pub fn readback_schema_sha256(&self) -> &str {
        &self.readback_schema_sha256
    }

    #[must_use]
    pub const fn operation(&self) -> &ChartOperation {
        &self.operation
    }

    /// Emits the complete sealed plan as bounded compact deterministic JSON.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ChartAutomationLimits,
    ) -> Result<Vec<u8>, ChartAutomationError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ChartAutomationPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationPlan")
            .field("capability_id", &self.capability_id)
            .field("charts", &self.target_state.charts.len())
            .field("identity_and_bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ChartAutomationReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    profile_sha256: String,
    binding_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl ChartAutomationReceipt {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub fn target_state_sha256(&self) -> &str {
        &self.target_state_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Emits the bounded deterministic internal build receipt.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ChartAutomationLimits,
    ) -> Result<Vec<u8>, ChartAutomationError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ChartAutomationReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ChartAutomationResult {
    pub state: ChartDocumentState,
    pub receipt: ChartAutomationReceipt,
}

impl fmt::Debug for ChartAutomationResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationResult")
            .field("charts", &self.state.charts.len())
            .field("receipt", &self.receipt)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct ChartAutomationBuilder;

impl ChartAutomationBuilder {
    /// Produces the exact target state and seals its target-specific automation binding.
    ///
    /// # Errors
    ///
    /// Rejects profile/state/flow drift, unavailable bindings and invalid transitions.
    pub fn plan(
        profile: &ChartAutomationProfile,
        source: &ChartDocumentState,
        request: &ChartAutomationRequest,
        current_document_flow_sha256: &str,
        limits: ChartAutomationLimits,
    ) -> Result<ChartAutomationPlan, ChartAutomationError> {
        require_digest(current_document_flow_sha256)?;
        let profile_sha256 = profile.canonical_sha256(limits)?;
        if profile_sha256 != request.expected_profile_sha256 {
            return Err(ChartAutomationError::ProfileDrift);
        }
        let source_state_sha256 = source.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(ChartAutomationError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(ChartAutomationError::DocumentFlowDrift);
        }
        let binding = profile.automation_binding(request.operation.capability_id())?;
        let target_state = source.apply(&request.operation, profile, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let request_sha256 = hex(Sha256::digest(request.canonical_json(limits)?).into());
        let mut plan = ChartAutomationPlan {
            schema_version: CHART_AUTOMATION_SCHEMA_VERSION,
            capability_id: request.operation.capability_id(),
            request_id: request.request_id.clone(),
            target_chart_id: request.operation.target_chart_id().clone(),
            profile_sha256,
            binding_id: binding.binding_id.clone(),
            parameter_schema_sha256: binding.parameter_schema_sha256.clone(),
            readback_schema_sha256: binding.readback_schema_sha256.clone(),
            source_state_sha256,
            source_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation: request.operation.clone(),
            target_state,
            target_state_sha256,
            request_sha256,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_digest(&plan, limits)?;
        let _ = serialize_bounded(&plan, limits)?;
        Ok(plan)
    }

    /// Revalidates profile, current state/flow, target recomputation and the sealed plan.
    ///
    /// # Errors
    ///
    /// Rejects any drift, plan tampering, binding mismatch or non-reproducible target.
    pub fn build(
        plan: &ChartAutomationPlan,
        profile: &ChartAutomationProfile,
        current: &ChartDocumentState,
        current_document_flow_sha256: &str,
        limits: ChartAutomationLimits,
    ) -> Result<ChartAutomationResult, ChartAutomationError> {
        require_digest(current_document_flow_sha256)?;
        if profile.canonical_sha256(limits)? != plan.profile_sha256 {
            return Err(ChartAutomationError::ProfileDrift);
        }
        let binding = profile.automation_binding(plan.capability_id)?;
        if plan.schema_version != CHART_AUTOMATION_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan.target_chart_id != *plan.operation.target_chart_id()
            || binding.binding_id != plan.binding_id
            || binding.parameter_schema_sha256 != plan.parameter_schema_sha256
            || binding.readback_schema_sha256 != plan.readback_schema_sha256
            || !sealed_plan_intact(plan, limits)?
        {
            return Err(ChartAutomationError::PlanTampered);
        }
        let source_state_sha256 = current.canonical_sha256(limits)?;
        if source_state_sha256 != plan.source_state_sha256 {
            return Err(ChartAutomationError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(ChartAutomationError::DocumentFlowDrift);
        }
        let rebuilt = current.apply(&plan.operation, profile, limits)?;
        let rebuilt_sha256 = rebuilt.canonical_sha256(limits)?;
        if rebuilt != plan.target_state || rebuilt_sha256 != plan.target_state_sha256 {
            return Err(ChartAutomationError::PlanTampered);
        }
        Ok(ChartAutomationResult {
            state: rebuilt,
            receipt: ChartAutomationReceipt {
                schema_version: CHART_AUTOMATION_SCHEMA_VERSION,
                capability_id: plan.capability_id,
                profile_sha256: plan.profile_sha256.clone(),
                binding_id: plan.binding_id.clone(),
                source_state_sha256,
                target_state_sha256: rebuilt_sha256,
                source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                plan_sha256: plan.plan_sha256.clone(),
            },
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)] // Each lifecycle/readback checkpoint is independently required.
pub struct ChartAutomationObservationDraft {
    pub schema_version: String,
    pub plan_sha256: String,
    pub profile_sha256: String,
    pub capability_id: String,
    pub binding_id: LogicalId,
    pub parameter_schema_sha256: String,
    pub readback_schema_sha256: String,
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub source_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub execution_attempts: u32,
    pub opened: bool,
    pub saved: bool,
    pub reopened: bool,
    pub full_property_readback: bool,
    pub reopened_state_sha256: String,
    pub export_sha256: String,
    pub export_byte_length: u64,
}

impl fmt::Debug for ChartAutomationObservationDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationObservationDraft")
            .field("capability_id", &self.capability_id)
            .field("execution_attempts", &self.execution_attempts)
            .field("opened", &self.opened)
            .field("saved", &self.saved)
            .field("reopened", &self.reopened)
            .field("full_property_readback", &self.full_property_readback)
            .field("export_byte_length", &self.export_byte_length)
            .field("bindings_and_digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ChartAutomationObservation {
    schema_version: &'static str,
    plan_sha256: String,
    profile_sha256: String,
    capability_id: String,
    binding_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    reopened_state_sha256: String,
    export_sha256: String,
    export_byte_length: u64,
}

impl ChartAutomationObservation {
    /// Admits a complete, exact execution observation for one sealed plan.
    ///
    /// This verifies internal receipt coherence only; provenance must independently establish that
    /// the values came from the licensed target and not a synthetic fixture.
    ///
    /// # Errors
    ///
    /// Rejects partial, repeated, drifted, empty-export or tampered observations.
    pub fn from_draft(
        draft: ChartAutomationObservationDraft,
        plan: &ChartAutomationPlan,
        limits: ChartAutomationLimits,
    ) -> Result<Self, ChartAutomationError> {
        if draft.schema_version != CHART_AUTOMATION_SCHEMA_VERSION {
            return Err(ChartAutomationError::UnsupportedVersion);
        }
        for digest in [
            &draft.plan_sha256,
            &draft.profile_sha256,
            &draft.parameter_schema_sha256,
            &draft.readback_schema_sha256,
            &draft.source_state_sha256,
            &draft.target_state_sha256,
            &draft.source_document_flow_sha256,
            &draft.target_document_flow_sha256,
            &draft.reopened_state_sha256,
            &draft.export_sha256,
        ] {
            require_digest(digest)?;
        }
        validate_text(&draft.capability_id, limits, false)?;
        validate_id(&draft.binding_id, limits)?;
        if draft.plan_sha256 != plan.plan_sha256
            || draft.profile_sha256 != plan.profile_sha256
            || draft.capability_id != plan.capability_id
            || draft.binding_id != plan.binding_id
            || draft.parameter_schema_sha256 != plan.parameter_schema_sha256
            || draft.readback_schema_sha256 != plan.readback_schema_sha256
            || draft.source_state_sha256 != plan.source_state_sha256
            || draft.target_state_sha256 != plan.target_state_sha256
            || draft.source_document_flow_sha256 != plan.source_document_flow_sha256
            || draft.target_document_flow_sha256 != plan.target_document_flow_sha256
            || draft.reopened_state_sha256 != plan.target_state_sha256
        {
            return Err(ChartAutomationError::ObservationDrift);
        }
        if draft.execution_attempts != 1
            || !draft.opened
            || !draft.saved
            || !draft.reopened
            || !draft.full_property_readback
            || draft.export_byte_length == 0
            || draft.export_byte_length > limits.0.export_bytes
        {
            return Err(ChartAutomationError::IncompleteObservation);
        }
        let observation = Self {
            schema_version: CHART_AUTOMATION_SCHEMA_VERSION,
            plan_sha256: draft.plan_sha256,
            profile_sha256: draft.profile_sha256,
            capability_id: draft.capability_id,
            binding_id: draft.binding_id,
            source_state_sha256: draft.source_state_sha256,
            target_state_sha256: draft.target_state_sha256,
            source_document_flow_sha256: draft.source_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            reopened_state_sha256: draft.reopened_state_sha256,
            export_sha256: draft.export_sha256,
            export_byte_length: draft.export_byte_length,
        };
        let _ = observation.canonical_json(limits)?;
        Ok(observation)
    }

    /// Parses a bounded duplicate-key-free strict execution observation.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized, incomplete or drifted observations.
    pub fn from_json(
        bytes: &[u8],
        plan: &ChartAutomationPlan,
        limits: ChartAutomationLimits,
    ) -> Result<Self, ChartAutomationError> {
        validate_input(bytes, limits)?;
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| ChartAutomationError::InvalidJson)?;
        Self::from_draft(draft, plan, limits)
    }

    /// Emits the bounded exact observation receipt.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ChartAutomationLimits,
    ) -> Result<Vec<u8>, ChartAutomationError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ChartAutomationObservation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ChartAutomationObservation")
            .field("capability", &self.capability_id)
            .field("export_byte_length", &self.export_byte_length)
            .field("evidence_bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ChartAutomationError {
    #[error("chart automation limits are invalid")]
    InvalidLimit,
    #[error("chart automation input exceeds a finite limit")]
    InputLimit,
    #[error("chart automation output exceeds a finite limit")]
    OutputLimit,
    #[error("chart automation JSON is malformed or not strict")]
    InvalidJson,
    #[error("chart automation schema version is unsupported")]
    UnsupportedVersion,
    #[error("chart automation digest is malformed")]
    InvalidDigest,
    #[error("chart automation target profile is incomplete or noncanonical")]
    InvalidProfile,
    #[error("chart automation target profile drifted")]
    ProfileDrift,
    #[error("chart automation identity is duplicated or invalid")]
    InvalidIdentity,
    #[error("chart automation chart was not found")]
    ChartNotFound,
    #[error("chart automation chart type is unsupported by the bound target")]
    UnsupportedChartType,
    #[error("chart automation style is unsupported by the bound target")]
    UnsupportedStyle,
    #[error("chart automation data grid is invalid")]
    InvalidData,
    #[error("chart automation series state is invalid")]
    InvalidSeries,
    #[error("chart automation axis state is invalid")]
    InvalidAxis,
    #[error("chart automation presentation state is invalid")]
    InvalidPresentation,
    #[error("chart automation preservation binding is invalid")]
    InvalidPreservation,
    #[error("chart automation identity reservation is invalid")]
    InvalidReservation,
    #[error("chart automation operation would not change state")]
    NoChange,
    #[error("chart automation source state drifted")]
    SourceStateDrift,
    #[error("chart automation document flow drifted")]
    DocumentFlowDrift,
    #[error("chart automation plan was tampered with")]
    PlanTampered,
    #[error("chart automation observation is incomplete")]
    IncompleteObservation,
    #[error("chart automation observation drifted from the sealed plan")]
    ObservationDrift,
    #[error("chart automation serialization failed")]
    Serialization,
}

impl ChartAutomationError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "chart_automation_invalid_limit",
            Self::InputLimit => "chart_automation_input_limit",
            Self::OutputLimit => "chart_automation_output_limit",
            Self::InvalidJson => "chart_automation_invalid_json",
            Self::UnsupportedVersion => "chart_automation_unsupported_version",
            Self::InvalidDigest => "chart_automation_invalid_digest",
            Self::InvalidProfile => "chart_automation_invalid_profile",
            Self::ProfileDrift => "chart_automation_profile_drift",
            Self::InvalidIdentity => "chart_automation_invalid_identity",
            Self::ChartNotFound => "chart_automation_chart_not_found",
            Self::UnsupportedChartType => "chart_automation_unsupported_chart_type",
            Self::UnsupportedStyle => "chart_automation_unsupported_style",
            Self::InvalidData => "chart_automation_invalid_data",
            Self::InvalidSeries => "chart_automation_invalid_series",
            Self::InvalidAxis => "chart_automation_invalid_axis",
            Self::InvalidPresentation => "chart_automation_invalid_presentation",
            Self::InvalidPreservation => "chart_automation_invalid_preservation",
            Self::InvalidReservation => "chart_automation_invalid_reservation",
            Self::NoChange => "chart_automation_no_change",
            Self::SourceStateDrift => "chart_automation_source_state_drift",
            Self::DocumentFlowDrift => "chart_automation_document_flow_drift",
            Self::PlanTampered => "chart_automation_plan_tampered",
            Self::IncompleteObservation => "chart_automation_incomplete_observation",
            Self::ObservationDrift => "chart_automation_observation_drift",
            Self::Serialization => "chart_automation_serialization",
        }
    }
}

fn validate_chart(
    chart: &ChartState,
    profile: &ChartAutomationProfile,
    limits: ChartAutomationLimits,
) -> Result<(), ChartAutomationError> {
    validate_identity(&chart.identity, limits)?;
    profile.type_binding(&chart.chart_type)?;
    profile.style_binding(&chart.style_id, &chart.style_binding_id)?;
    validate_data(&chart.data, &chart.identity.data_resource_id, limits)?;
    validate_series(&chart.series, &chart.data, limits)?;
    validate_axes(&chart.axes, &chart.series, limits)?;
    validate_presentation(chart, limits)?;
    for digest in [
        &chart.geometry_sha256,
        &chart.composition_sha256,
        &chart.appearance_sha256,
        &chart.opaque_semantics_sha256,
    ] {
        require_digest(digest)?;
    }
    if chart.opaque_semantics_bytes > limits.0.opaque_bytes {
        return Err(ChartAutomationError::InvalidPreservation);
    }
    Ok(())
}

fn validate_identity(
    identity: &ChartIdentity,
    limits: ChartAutomationLimits,
) -> Result<(), ChartAutomationError> {
    let ids = [
        &identity.chart_id,
        &identity.data_resource_id,
        &identity.chart_part_id,
    ];
    for id in ids {
        validate_id(id, limits)?;
    }
    if identity.native_object_id == 0
        || identity.native_instance_id == 0
        || ids[0] == ids[1]
        || ids[0] == ids[2]
        || ids[1] == ids[2]
    {
        return Err(ChartAutomationError::InvalidIdentity);
    }
    Ok(())
}

fn validate_data(
    data: &ChartDataState,
    expected_resource: &LogicalId,
    limits: ChartAutomationLimits,
) -> Result<(), ChartAutomationError> {
    if data.row_labels.is_empty()
        || data.column_labels.is_empty()
        || data.row_labels.len() > limits.0.rows
        || data.column_labels.len() > limits.0.columns
    {
        return Err(ChartAutomationError::InvalidData);
    }
    for label in data.row_labels.iter().chain(&data.column_labels) {
        validate_text(label, limits, false).map_err(|_| ChartAutomationError::InvalidData)?;
    }
    let cells = data
        .row_labels
        .len()
        .checked_mul(data.column_labels.len())
        .ok_or(ChartAutomationError::InputLimit)?;
    if data.values.len() != cells {
        return Err(ChartAutomationError::InvalidData);
    }
    for value in &data.values {
        if let ChartValue::Number(number) = value {
            validate_decimal(*number, limits).map_err(|_| ChartAutomationError::InvalidData)?;
        }
    }
    match &data.provenance {
        ChartDataProvenance::Embedded { resource_id }
        | ChartDataProvenance::AutomationEditor { resource_id } => {
            validate_id(resource_id, limits)?;
            if resource_id != expected_resource {
                return Err(ChartAutomationError::InvalidData);
            }
        }
        ChartDataProvenance::LinkedTable {
            table_id,
            table_state_sha256,
            range_sha256,
        } => {
            validate_id(table_id, limits)?;
            require_digest(table_state_sha256)?;
            require_digest(range_sha256)?;
        }
    }
    Ok(())
}

fn validate_series(
    series: &[ChartSeriesState],
    data: &ChartDataState,
    limits: ChartAutomationLimits,
) -> Result<(), ChartAutomationError> {
    let expected_labels = match data.orientation {
        ChartDataOrientation::SeriesByRows => &data.row_labels,
        ChartDataOrientation::SeriesByColumns => &data.column_labels,
    };
    if series.is_empty() || series.len() != expected_labels.len() || series.len() > limits.0.series
    {
        return Err(ChartAutomationError::InvalidSeries);
    }
    for (index, item) in series.iter().enumerate() {
        if usize::try_from(item.order).ok() != Some(index)
            || item.label != expected_labels[index]
            || (index == 0 && item.stacked_with_previous)
        {
            return Err(ChartAutomationError::InvalidSeries);
        }
        validate_text(&item.label, limits, false)
            .map_err(|_| ChartAutomationError::InvalidSeries)?;
        require_digest(&item.style_sha256).map_err(|_| ChartAutomationError::InvalidSeries)?;
        if item.stacked_with_previous && item.axis != series[index - 1].axis {
            return Err(ChartAutomationError::InvalidSeries);
        }
    }
    Ok(())
}

fn validate_axes(
    axes: &[ChartAxisState],
    series: &[ChartSeriesState],
    limits: ChartAutomationLimits,
) -> Result<(), ChartAutomationError> {
    if axes.len() < 2
        || axes.len() > limits.0.axes
        || !strictly_sorted_by(axes, |axis| axis.kind)
        || !axes
            .iter()
            .any(|axis| axis.kind == ChartAxisKind::CategoryX)
        || !axes.iter().any(|axis| axis.kind == ChartAxisKind::ValueY)
    {
        return Err(ChartAutomationError::InvalidAxis);
    }
    let needs_secondary = series
        .iter()
        .any(|item| item.axis == ChartSeriesAxis::Secondary);
    let has_secondary = axes
        .iter()
        .any(|axis| axis.kind == ChartAxisKind::SecondaryValueY);
    if needs_secondary && !has_secondary {
        return Err(ChartAutomationError::InvalidAxis);
    }
    for axis in axes {
        if let Some(title) = &axis.title {
            validate_text(title, limits, false).map_err(|_| ChartAutomationError::InvalidAxis)?;
        }
        validate_text(&axis.number_format, limits, true)
            .map_err(|_| ChartAutomationError::InvalidAxis)?;
        require_digest(&axis.style_sha256).map_err(|_| ChartAutomationError::InvalidAxis)?;
        if let ChartAxisScale::Manual {
            minimum,
            maximum,
            major_unit,
            minor_unit,
        } = axis.scale
        {
            for number in [minimum, maximum, major_unit, minor_unit] {
                validate_decimal(number, limits).map_err(|_| ChartAutomationError::InvalidAxis)?;
            }
            if decimal_cmp(minimum, maximum) != std::cmp::Ordering::Less
                || major_unit.coefficient() <= 0
                || minor_unit.coefficient() <= 0
            {
                return Err(ChartAutomationError::InvalidAxis);
            }
        }
    }
    Ok(())
}

fn validate_presentation(
    chart: &ChartState,
    limits: ChartAutomationLimits,
) -> Result<(), ChartAutomationError> {
    require_digest(&chart.legend.style_sha256)
        .map_err(|_| ChartAutomationError::InvalidPresentation)?;
    require_digest(&chart.labels.style_sha256)
        .map_err(|_| ChartAutomationError::InvalidPresentation)?;
    require_digest(&chart.title.style_sha256)
        .map_err(|_| ChartAutomationError::InvalidPresentation)?;
    validate_text(&chart.labels.number_format, limits, true)
        .map_err(|_| ChartAutomationError::InvalidPresentation)?;
    if !chart.labels.visible
        && (chart.labels.show_series_name
            || chart.labels.show_category_name
            || chart.labels.show_value
            || chart.labels.show_percentage)
    {
        return Err(ChartAutomationError::InvalidPresentation);
    }
    match (&chart.title.visible, &chart.title.text) {
        (true, Some(text)) => validate_text(text, limits, false)
            .map_err(|_| ChartAutomationError::InvalidPresentation)?,
        (false, None) => {}
        _ => return Err(ChartAutomationError::InvalidPresentation),
    }
    Ok(())
}

fn validate_reservation(
    reservation: &ChartIdentityReservation,
    chart: &ChartState,
    source: &ChartDocumentState,
    limits: ChartAutomationLimits,
) -> Result<(), ChartAutomationError> {
    for id in [
        &reservation.chart_id,
        &reservation.data_resource_id,
        &reservation.chart_part_id,
    ] {
        validate_id(id, limits)?;
    }
    for digest in [
        &reservation.before_external_object_inventory_sha256,
        &reservation.after_external_object_inventory_sha256,
        &reservation.allocator_proof_sha256,
    ] {
        require_digest(digest)?;
    }
    if reservation.chart_id != chart.identity.chart_id
        || reservation.native_object_id != chart.identity.native_object_id
        || reservation.native_instance_id != chart.identity.native_instance_id
        || reservation.data_resource_id != chart.identity.data_resource_id
        || reservation.chart_part_id != chart.identity.chart_part_id
        || reservation.before_external_object_inventory_sha256
            != source.external_object_inventory_sha256
        || reservation.after_external_object_inventory_sha256
            == reservation.before_external_object_inventory_sha256
    {
        return Err(ChartAutomationError::InvalidReservation);
    }
    Ok(())
}

fn chart_mut<'a>(
    charts: &'a mut [ChartState],
    id: &LogicalId,
) -> Result<&'a mut ChartState, ChartAutomationError> {
    charts
        .binary_search_by(|chart| chart.identity.chart_id.cmp(id))
        .ok()
        .map(|index| &mut charts[index])
        .ok_or(ChartAutomationError::ChartNotFound)
}

fn validate_decimal(
    value: FormulaDecimal,
    limits: ChartAutomationLimits,
) -> Result<(), ChartAutomationError> {
    if value.scale() > limits.0.decimal_scale
        || (value.scale() > 0 && value.coefficient() % 10 == 0)
    {
        return Err(ChartAutomationError::InvalidData);
    }
    Ok(())
}

fn decimal_cmp(left: FormulaDecimal, right: FormulaDecimal) -> std::cmp::Ordering {
    let scale = left.scale().max(right.scale());
    let left_multiplier = 10_i128.pow(u32::from(scale - left.scale()));
    let right_multiplier = 10_i128.pow(u32::from(scale - right.scale()));
    (i128::from(left.coefficient()) * left_multiplier)
        .cmp(&(i128::from(right.coefficient()) * right_multiplier))
}

fn validate_id(id: &LogicalId, limits: ChartAutomationLimits) -> Result<(), ChartAutomationError> {
    if id.as_str().is_empty() || id.as_str().len() > limits.0.identifier_bytes {
        return Err(ChartAutomationError::InvalidIdentity);
    }
    Ok(())
}

fn validate_text(
    text: &str,
    limits: ChartAutomationLimits,
    allow_empty: bool,
) -> Result<(), ChartAutomationError> {
    if (!allow_empty && text.is_empty())
        || text.len() > limits.0.text_bytes
        || text.chars().any(char::is_control)
        || text.nfc().ne(text.chars())
    {
        return Err(ChartAutomationError::InvalidProfile);
    }
    Ok(())
}

fn strictly_sorted_unique<T: Ord>(values: &[T]) -> bool {
    values.windows(2).all(|pair| pair[0] < pair[1])
}

fn strictly_sorted_by<T, K: Ord, F>(values: &[T], key: F) -> bool
where
    F: Fn(&T) -> K,
{
    values.windows(2).all(|pair| key(&pair[0]) < key(&pair[1]))
}

fn plan_digest(
    plan: &ChartAutomationPlan,
    limits: ChartAutomationLimits,
) -> Result<String, ChartAutomationError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        target_chart_id: &'a LogicalId,
        profile_sha256: &'a str,
        resolved_binding_id: &'a LogicalId,
        parameter_schema_sha256: &'a str,
        readback_schema_sha256: &'a str,
        source_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a ChartOperation,
        target_state_sha256: &'a str,
        request_sha256: &'a str,
    }
    let binding = Binding {
        schema_version: CHART_AUTOMATION_SCHEMA_VERSION,
        capability_id: plan.capability_id,
        request_id: &plan.request_id,
        target_chart_id: &plan.target_chart_id,
        profile_sha256: &plan.profile_sha256,
        resolved_binding_id: &plan.binding_id,
        parameter_schema_sha256: &plan.parameter_schema_sha256,
        readback_schema_sha256: &plan.readback_schema_sha256,
        source_state_sha256: &plan.source_state_sha256,
        source_document_flow_sha256: &plan.source_document_flow_sha256,
        target_document_flow_sha256: &plan.target_document_flow_sha256,
        operation: &plan.operation,
        target_state_sha256: &plan.target_state_sha256,
        request_sha256: &plan.request_sha256,
    };
    Ok(hex(
        Sha256::digest(serialize_bounded(&binding, limits)?).into()
    ))
}

fn sealed_plan_intact(
    plan: &ChartAutomationPlan,
    limits: ChartAutomationLimits,
) -> Result<bool, ChartAutomationError> {
    Ok(plan_digest(plan, limits)? == plan.plan_sha256)
}

fn require_digest(value: &str) -> Result<(), ChartAutomationError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !matches!(byte, b'0'..=b'9' | b'a'..=b'f'))
    {
        return Err(ChartAutomationError::InvalidDigest);
    }
    Ok(())
}

fn validate_input(bytes: &[u8], limits: ChartAutomationLimits) -> Result<(), ChartAutomationError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(ChartAutomationError::InputLimit);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ChartAutomationLimits,
) -> Result<Vec<u8>, ChartAutomationError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ChartAutomationError::Serialization)?;
    if bytes.len() > limits.0.serialized_bytes {
        return Err(ChartAutomationError::OutputLimit);
    }
    Ok(bytes)
}

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

#[allow(clippy::too_many_lines)]
fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), ChartAutomationError> {
    struct RootVisitor;
    struct AnyVisitor;
    struct Seed;

    impl<'de> DeserializeSeed<'de> for Seed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(AnyVisitor)
        }
    }

    fn visit_map<'de, A>(mut map: A) -> Result<(), A::Error>
    where
        A: MapAccess<'de>,
    {
        let mut keys = BTreeSet::new();
        while let Some(key) = map.next_key::<String>()? {
            if !keys.insert(key) {
                return Err(de::Error::custom("duplicate key"));
            }
            map.next_value_seed(Seed)?;
        }
        Ok(())
    }

    impl<'de> Visitor<'de> for RootVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON object without duplicate keys")
        }

        fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
        where
            A: MapAccess<'de>,
        {
            visit_map(map)
        }
    }

    impl<'de> Visitor<'de> for AnyVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("any JSON value")
        }

        fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
        where
            A: MapAccess<'de>,
        {
            visit_map(map)
        }

        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: SeqAccess<'de>,
        {
            while sequence.next_element_seed(Seed)?.is_some() {}
            Ok(())
        }

        fn visit_bool<E>(self, _value: bool) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_i64<E>(self, _value: i64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_u64<E>(self, _value: u64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_f64<E>(self, _value: f64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_str<E>(self, _value: &str) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_none<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_unit<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
    }

    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    serde::Deserializer::deserialize_map(&mut deserializer, RootVisitor)
        .map_err(|_| ChartAutomationError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| ChartAutomationError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Test setup uses expectations only to isolate private-plan tampering.
mod tests {
    use super::*;

    #[test]
    fn private_plan_tampering_is_rejected_by_the_seal() {
        let limits =
            ChartAutomationLimits::new(ChartAutomationLimitConfig::default()).expect("limits");
        let target = ChartDocumentState {
            schema_version: CHART_AUTOMATION_SCHEMA_VERSION,
            target_profile_id: LogicalId::parse("profile").expect("profile"),
            external_object_inventory_sha256: "1".repeat(64),
            charts: Vec::new(),
        };
        let mut plan = ChartAutomationPlan {
            schema_version: CHART_AUTOMATION_SCHEMA_VERSION,
            capability_id: "obj.chart_title",
            request_id: LogicalId::parse("request").expect("request"),
            target_chart_id: LogicalId::parse("chart").expect("chart"),
            profile_sha256: "2".repeat(64),
            binding_id: LogicalId::parse("binding").expect("binding"),
            parameter_schema_sha256: "3".repeat(64),
            readback_schema_sha256: "4".repeat(64),
            source_state_sha256: "5".repeat(64),
            source_document_flow_sha256: "6".repeat(64),
            target_document_flow_sha256: "7".repeat(64),
            operation: ChartOperation::SetTitle {
                chart_id: LogicalId::parse("chart").expect("chart"),
                title: ChartTitleState {
                    visible: false,
                    position: ChartTitlePosition::Above,
                    text: None,
                    style_sha256: "8".repeat(64),
                },
            },
            target_state: target,
            target_state_sha256: "9".repeat(64),
            request_sha256: "a".repeat(64),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_digest(&plan, limits).expect("seal");
        assert!(sealed_plan_intact(&plan, limits).expect("verify"));
        plan.target_state_sha256 = "f".repeat(64);
        assert!(!sealed_plan_intact(&plan, limits).expect("verify"));
    }
}
