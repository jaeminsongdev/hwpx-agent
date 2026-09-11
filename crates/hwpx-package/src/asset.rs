use std::collections::{BTreeMap, BTreeSet};
use std::fmt::{self, Debug};

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    AddedPart, PackageError, PackageGraph, PackageGraphLimits, PackageLimits, PackagePath,
    PartRole, PatchError, PatchIntent, PatchLimits, RelationshipAddition, RelationshipKind,
    RelationshipSpine,
};

pub const ASSET_PIPELINE_SCHEMA_VERSION: &str = "hwpx-agent.asset-pipeline/v1";
pub const ASSET_PIPELINE_PROFILE_ID: &str = "hwpx-agent.asset-pipeline.hwp-image-v1";

const MAX_ASSET_BYTES_CEILING: u64 = 256 * 1024 * 1024;
const MAX_EXISTING_ASSETS_CEILING: usize = 65_536;
const MAX_PLAN_JSON_BYTES_CEILING: usize = 64 * 1024;
const MAX_DIMENSION_CEILING: u32 = 1_000_000;
const MAX_PIXELS_CEILING: u64 = 1_000_000_000_000;
const CRC32_TABLE: [u32; 256] = crc32_table();

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AssetLimitConfig {
    pub max_asset_bytes: u64,
    pub max_existing_assets: usize,
    pub max_plan_json_bytes: usize,
    pub max_dimension_px: u32,
    pub max_pixels: u64,
}

impl Default for AssetLimitConfig {
    fn default() -> Self {
        Self {
            max_asset_bytes: 64 * 1024 * 1024,
            max_existing_assets: 4_096,
            max_plan_json_bytes: 16 * 1024,
            max_dimension_px: 100_000,
            max_pixels: 1_000_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct AssetLimits(AssetLimitConfig);

impl AssetLimits {
    /// Validates every finite asset-pipeline limit against a hard ceiling.
    ///
    /// # Errors
    ///
    /// Returns [`AssetError::InvalidLimit`] for zero or excessive values.
    pub fn new(config: AssetLimitConfig) -> Result<Self, AssetError> {
        check_limit(
            "max_asset_bytes",
            config.max_asset_bytes,
            MAX_ASSET_BYTES_CEILING,
        )?;
        check_limit(
            "max_existing_assets",
            config.max_existing_assets as u64,
            MAX_EXISTING_ASSETS_CEILING as u64,
        )?;
        check_limit(
            "max_plan_json_bytes",
            config.max_plan_json_bytes as u64,
            MAX_PLAN_JSON_BYTES_CEILING as u64,
        )?;
        check_limit(
            "max_dimension_px",
            u64::from(config.max_dimension_px),
            u64::from(MAX_DIMENSION_CEILING),
        )?;
        check_limit("max_pixels", config.max_pixels, MAX_PIXELS_CEILING)?;
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> AssetLimitConfig {
        self.0
    }
}

fn check_limit(field: &'static str, value: u64, ceiling: u64) -> Result<(), AssetError> {
    if value == 0 || value > ceiling {
        return Err(AssetError::InvalidLimit {
            field,
            value,
            ceiling,
        });
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AssetMedia {
    Png,
    Jpeg,
    Gif,
    Webp,
    Bmp,
}

impl AssetMedia {
    fn parse(value: &str) -> Result<Self, AssetError> {
        match value {
            "image/png" => Ok(Self::Png),
            "image/jpeg" => Ok(Self::Jpeg),
            "image/gif" => Ok(Self::Gif),
            "image/webp" => Ok(Self::Webp),
            "image/bmp" => Ok(Self::Bmp),
            _ => Err(AssetError::UnsupportedMedia),
        }
    }

    #[must_use]
    pub const fn media_type(self) -> &'static str {
        match self {
            Self::Png => "image/png",
            Self::Jpeg => "image/jpeg",
            Self::Gif => "image/gif",
            Self::Webp => "image/webp",
            Self::Bmp => "image/bmp",
        }
    }

    const fn extension(self) -> &'static str {
        match self {
            Self::Png => "png",
            Self::Jpeg => "jpg",
            Self::Gif => "gif",
            Self::Webp => "webp",
            Self::Bmp => "bmp",
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AssetDisposition {
    ReusedExisting,
    AddNew,
}

#[derive(Clone, Eq, PartialEq)]
pub struct AssetPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    source_graph_sha256: String,
    disposition: AssetDisposition,
    declared_media_type: String,
    media: AssetMedia,
    relationship_id: String,
    target_path: PackagePath,
    content_sha256: String,
    content_bytes: usize,
    width_px: u32,
    height_px: u32,
    plan_sha256: String,
    payload: Box<[u8]>,
}

impl Debug for AssetPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AssetPlan")
            .field("schema_version", &self.schema_version)
            .field("profile_id", &self.profile_id)
            .field("disposition", &self.disposition)
            .field("media", &self.media)
            .field("content_bytes", &self.content_bytes)
            .field("width_px", &self.width_px)
            .field("height_px", &self.height_px)
            .finish_non_exhaustive()
    }
}

impl AssetPlan {
    #[must_use]
    pub const fn disposition(&self) -> AssetDisposition {
        self.disposition
    }

    #[must_use]
    pub const fn media(&self) -> AssetMedia {
        self.media
    }

    #[must_use]
    pub fn relationship_id(&self) -> &str {
        &self.relationship_id
    }

    #[must_use]
    pub const fn target_path(&self) -> &PackagePath {
        &self.target_path
    }

    #[must_use]
    pub fn content_sha256(&self) -> &str {
        &self.content_sha256
    }

    #[must_use]
    pub const fn content_bytes(&self) -> usize {
        self.content_bytes
    }

    #[must_use]
    pub const fn width_px(&self) -> u32 {
        self.width_px
    }

    #[must_use]
    pub const fn height_px(&self) -> u32 {
        self.height_px
    }

    #[must_use]
    pub fn source_graph_sha256(&self) -> &str {
        &self.source_graph_sha256
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
}

#[derive(Debug, Default)]
pub struct AssetStoreAdapter {
    limits: AssetLimits,
    package_limits: PackageLimits,
    graph_limits: PackageGraphLimits,
    patch_limits: PatchLimits,
}

impl AssetStoreAdapter {
    #[must_use]
    pub const fn new(
        limits: AssetLimits,
        package_limits: PackageLimits,
        graph_limits: PackageGraphLimits,
        patch_limits: PatchLimits,
    ) -> Self {
        Self {
            limits,
            package_limits,
            graph_limits,
            patch_limits,
        }
    }

    /// Sniffs and structurally validates an image, binds the complete source package graph,
    /// and deterministically selects an existing relationship or a new content-addressed part.
    ///
    /// # Errors
    ///
    /// Returns a stable typed error for malformed/unsupported media, limits, graph ambiguity,
    /// relationship collisions, allocation failure, or invalid generated package paths.
    pub fn build(
        &self,
        declared_media_type: &str,
        payload: &[u8],
        source_graph: &PackageGraph,
    ) -> Result<AssetPlan, AssetError> {
        if payload.is_empty() {
            return Err(AssetError::EmptyAsset);
        }
        if payload.len() as u64 > self.limits.config().max_asset_bytes
            || payload.len() > self.patch_limits.config().max_added_part_bytes
        {
            return Err(AssetError::AssetTooLarge);
        }
        let declared = AssetMedia::parse(declared_media_type)?;
        let image = sniff_image(payload)?;
        if declared != image.media {
            return Err(AssetError::DeclaredMediaMismatch);
        }
        validate_dimensions(image.width, image.height, self.limits)?;
        let content_digest = <[u8; 32]>::from(Sha256::digest(payload));
        let content_sha256 = encode_hex(&content_digest);
        let source_graph_sha256 = encode_hex(&hash_graph(source_graph));
        let existing = inspect_existing_assets(source_graph, self.limits)?;
        let selected = existing.iter().find(|asset| {
            asset.raw_sha256 == content_digest
                && asset.expanded_size == payload.len() as u64
                && asset.media == image.media
        });
        if existing.iter().any(|asset| {
            asset.raw_sha256 == content_digest
                && asset.expanded_size == payload.len() as u64
                && asset.media != image.media
        }) {
            return Err(AssetError::ExistingAssetMediaMismatch);
        }
        let (disposition, relationship_id, target_path) = if let Some(asset) = selected {
            (
                AssetDisposition::ReusedExisting,
                asset.relationship_id.clone(),
                asset.path.clone(),
            )
        } else {
            let relationship_id = format!("p08-{content_sha256}");
            let target = format!("BinData/p08-{content_sha256}.{}", image.media.extension());
            if source_graph
                .relationships
                .iter()
                .any(|relationship| relationship.id == relationship_id)
            {
                return Err(AssetError::RelationshipIdCollision);
            }
            let target_path = PackagePath::parse(target.as_bytes(), 0, self.package_limits)?;
            if source_graph
                .parts
                .iter()
                .any(|part| part.path.collision_key() == target_path.collision_key())
            {
                return Err(AssetError::PartCollision);
            }
            (AssetDisposition::AddNew, relationship_id, target_path)
        };
        let seed = AssetPlanSeed {
            source_graph_sha256: &source_graph_sha256,
            disposition,
            declared_media_type,
            media: image.media,
            relationship_id: &relationship_id,
            target_path: target_path.as_str(),
            content_sha256: &content_sha256,
            content_bytes: payload.len(),
            width_px: image.width,
            height_px: image.height,
        };
        let plan_sha256 = encode_hex(&hash_plan_seed(&seed));
        let mut copied = Vec::new();
        copied
            .try_reserve_exact(payload.len())
            .map_err(|_| AssetError::AllocationFailed)?;
        copied.extend_from_slice(payload);
        Ok(AssetPlan {
            schema_version: ASSET_PIPELINE_SCHEMA_VERSION,
            profile_id: ASSET_PIPELINE_PROFILE_ID,
            source_graph_sha256,
            disposition,
            declared_media_type: declared_media_type.to_owned(),
            media: image.media,
            relationship_id,
            target_path,
            content_sha256,
            content_bytes: payload.len(),
            width_px: image.width,
            height_px: image.height,
            plan_sha256,
            payload: copied.into_boxed_slice(),
        })
    }

    /// Rechecks the complete graph and private payload immediately before producing atomic patch
    /// intents. A reused asset intentionally produces no part/relationship mutation.
    ///
    /// # Errors
    ///
    /// Returns no intents when any plan, payload, graph, path, media, or limit binding drifts.
    pub fn build_patch_intents(
        &self,
        plan: &AssetPlan,
        observed_graph: &PackageGraph,
    ) -> Result<Vec<PatchIntent>, AssetError> {
        if encode_hex(&hash_graph(observed_graph)) != plan.source_graph_sha256 {
            return Err(AssetError::SourceGraphDrift);
        }
        let rebuilt = self.build(&plan.declared_media_type, &plan.payload, observed_graph)?;
        if &rebuilt != plan {
            return Err(AssetError::PlanMismatch);
        }
        if plan.disposition == AssetDisposition::ReusedExisting {
            return Ok(Vec::new());
        }
        let part = AddedPart::opaque(
            plan.target_path.as_str(),
            plan.media.media_type(),
            &plan.payload,
            self.package_limits,
            self.graph_limits,
            self.patch_limits,
        )?;
        let relationship = RelationshipAddition::new(
            &plan.relationship_id,
            plan.target_path.as_str(),
            plan.media.media_type(),
            RelationshipSpine::NotInSpine,
            self.package_limits,
            self.graph_limits,
            self.patch_limits,
        )?;
        Ok(vec![
            PatchIntent::AddPart { part },
            PatchIntent::AddRelationship { relationship },
        ])
    }

    /// Serializes a bounded deterministic private plan without embedding media bytes.
    ///
    /// # Errors
    ///
    /// Returns an allocation/JSON/limit error. The returned JSON is not public evidence.
    pub fn to_private_plan_json(&self, plan: &AssetPlan) -> Result<Vec<u8>, AssetError> {
        let bytes = serde_json::to_vec(&AssetPlanDraft::from(plan))?;
        if bytes.len() > self.limits.config().max_plan_json_bytes {
            return Err(AssetError::PlanJsonTooLarge);
        }
        Ok(bytes)
    }

    /// Loads strict private plan JSON while recomputing its raw digest, source graph, media parser,
    /// content digest, dimensions, dedup choice, relationship/path, and semantic plan digest.
    ///
    /// # Errors
    ///
    /// Returns no plan for duplicate/unknown fields, stale graph or payload, bad versions, an
    /// untrusted raw plan digest, or any non-canonical stored value.
    pub fn load_private_plan_json(
        &self,
        bytes: &[u8],
        expected_raw_sha256: &str,
        payload: &[u8],
        observed_graph: &PackageGraph,
    ) -> Result<AssetPlan, AssetError> {
        if bytes.is_empty() || bytes.len() > self.limits.config().max_plan_json_bytes {
            return Err(AssetError::PlanJsonTooLarge);
        }
        validate_sha256(expected_raw_sha256)?;
        if encode_hex(&<[u8; 32]>::from(Sha256::digest(bytes))) != expected_raw_sha256 {
            return Err(AssetError::UntrustedPlan);
        }
        let draft: AssetPlanDraft = serde_json::from_slice(bytes)?;
        if draft.schema_version != ASSET_PIPELINE_SCHEMA_VERSION
            || draft.profile_id != ASSET_PIPELINE_PROFILE_ID
        {
            return Err(AssetError::UnsupportedVersion);
        }
        for digest in [
            &draft.source_graph_sha256,
            &draft.content_sha256,
            &draft.plan_sha256,
        ] {
            validate_sha256(digest)?;
        }
        let rebuilt = self.build(&draft.declared_media_type, payload, observed_graph)?;
        if AssetPlanDraft::from(&rebuilt) != draft {
            return Err(AssetError::PlanMismatch);
        }
        Ok(rebuilt)
    }
}

#[derive(Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct AssetPlanDraft {
    schema_version: String,
    profile_id: String,
    source_graph_sha256: String,
    disposition: AssetDisposition,
    declared_media_type: String,
    media: AssetMedia,
    relationship_id: String,
    target_path: String,
    content_sha256: String,
    content_bytes: usize,
    width_px: u32,
    height_px: u32,
    plan_sha256: String,
}

impl From<&AssetPlan> for AssetPlanDraft {
    fn from(plan: &AssetPlan) -> Self {
        Self {
            schema_version: plan.schema_version.to_owned(),
            profile_id: plan.profile_id.to_owned(),
            source_graph_sha256: plan.source_graph_sha256.clone(),
            disposition: plan.disposition,
            declared_media_type: plan.declared_media_type.clone(),
            media: plan.media,
            relationship_id: plan.relationship_id.clone(),
            target_path: plan.target_path.as_str().to_owned(),
            content_sha256: plan.content_sha256.clone(),
            content_bytes: plan.content_bytes,
            width_px: plan.width_px,
            height_px: plan.height_px,
            plan_sha256: plan.plan_sha256.clone(),
        }
    }
}

struct AssetPlanSeed<'a> {
    source_graph_sha256: &'a str,
    disposition: AssetDisposition,
    declared_media_type: &'a str,
    media: AssetMedia,
    relationship_id: &'a str,
    target_path: &'a str,
    content_sha256: &'a str,
    content_bytes: usize,
    width_px: u32,
    height_px: u32,
}

struct ExistingAsset {
    relationship_id: String,
    path: PackagePath,
    media: AssetMedia,
    expanded_size: u64,
    raw_sha256: [u8; 32],
}

fn inspect_existing_assets(
    graph: &PackageGraph,
    limits: AssetLimits,
) -> Result<Vec<ExistingAsset>, AssetError> {
    let mut relationship_ids = BTreeSet::new();
    for relationship in &graph.relationships {
        if relationship.kind == RelationshipKind::ManifestItem
            && !relationship_ids.insert(relationship.id.as_str())
        {
            return Err(AssetError::RelationshipBroken);
        }
    }
    let mut relationships_by_target = BTreeMap::<&str, Vec<_>>::new();
    for relationship in &graph.relationships {
        if relationship.kind == RelationshipKind::ManifestItem {
            relationships_by_target
                .entry(relationship.target.collision_key())
                .or_default()
                .push(relationship);
        }
    }
    let mut assets = Vec::new();
    for part in &graph.parts {
        if !part.path.as_str().starts_with("BinData/") {
            continue;
        }
        let Ok(media) = AssetMedia::parse(part.media_type.as_str()) else {
            continue;
        };
        if assets.len() >= limits.config().max_existing_assets {
            return Err(AssetError::ExistingAssetLimit);
        }
        let relationships = relationships_by_target
            .get(part.path.collision_key())
            .ok_or(AssetError::RelationshipBroken)?;
        if relationships.len() != 1
            || relationships[0].media_type != part.media_type
            || relationships[0].source != graph.package_document
            || part.role != PartRole::ManifestListed
        {
            return Err(AssetError::RelationshipBroken);
        }
        assets.push(ExistingAsset {
            relationship_id: relationships[0].id.clone(),
            path: part.path.clone(),
            media,
            expanded_size: part.expanded_size,
            raw_sha256: part.raw_sha256,
        });
    }
    assets.sort_unstable_by(|left, right| {
        (left.path.as_str(), left.relationship_id.as_str())
            .cmp(&(right.path.as_str(), right.relationship_id.as_str()))
    });
    Ok(assets)
}

fn hash_graph(graph: &PackageGraph) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.asset-pipeline.source-graph/v1\0");
    hash_text(&mut digest, graph.package_document.as_str());
    hash_usize(&mut digest, graph.parts.len());
    for part in &graph.parts {
        hash_text(&mut digest, part.path.as_str());
        hash_text(&mut digest, part.media_type.as_str());
        digest.update([match part.role {
            PartRole::Infrastructure => 0,
            PartRole::ManifestListed => 1,
            PartRole::SpineDocument => 2,
        }]);
        digest.update(part.expanded_size.to_be_bytes());
        digest.update(part.raw_sha256);
    }
    hash_usize(&mut digest, graph.relationships.len());
    for relationship in &graph.relationships {
        hash_text(&mut digest, &relationship.id);
        hash_text(&mut digest, relationship.source.as_str());
        hash_text(&mut digest, relationship.target.as_str());
        hash_text(&mut digest, relationship.media_type.as_str());
        digest.update([match relationship.kind {
            RelationshipKind::ManifestItem => 0,
            RelationshipKind::SpineItem => 1,
        }]);
        digest.update([u8::from(relationship.linear)]);
    }
    hash_usize(&mut digest, graph.spine.len());
    for path in &graph.spine {
        hash_text(&mut digest, path.as_str());
    }
    digest.finalize().into()
}

fn hash_plan_seed(seed: &AssetPlanSeed<'_>) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.asset-pipeline.plan/v1\0");
    hash_text(&mut digest, ASSET_PIPELINE_SCHEMA_VERSION);
    hash_text(&mut digest, ASSET_PIPELINE_PROFILE_ID);
    hash_text(&mut digest, seed.source_graph_sha256);
    digest.update([match seed.disposition {
        AssetDisposition::ReusedExisting => 0,
        AssetDisposition::AddNew => 1,
    }]);
    hash_text(&mut digest, seed.declared_media_type);
    hash_text(&mut digest, seed.media.media_type());
    hash_text(&mut digest, seed.relationship_id);
    hash_text(&mut digest, seed.target_path);
    hash_text(&mut digest, seed.content_sha256);
    digest.update((seed.content_bytes as u64).to_be_bytes());
    digest.update(seed.width_px.to_be_bytes());
    digest.update(seed.height_px.to_be_bytes());
    digest.finalize().into()
}

fn hash_text(digest: &mut Sha256, value: &str) {
    digest.update((value.len() as u64).to_be_bytes());
    digest.update(value.as_bytes());
}

fn hash_usize(digest: &mut Sha256, value: usize) {
    digest.update((value as u64).to_be_bytes());
}

fn encode_hex(bytes: &[u8; 32]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        output.push(char::from(HEX[usize::from(byte >> 4)]));
        output.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    output
}

fn validate_sha256(value: &str) -> Result<(), AssetError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
    {
        return Err(AssetError::UntrustedPlan);
    }
    Ok(())
}

#[derive(Clone, Copy)]
struct ImageInfo {
    media: AssetMedia,
    width: u32,
    height: u32,
}

fn sniff_image(bytes: &[u8]) -> Result<ImageInfo, AssetError> {
    if bytes.starts_with(b"\x89PNG\r\n\x1a\n") {
        return parse_png(bytes);
    }
    if bytes.starts_with(&[0xff, 0xd8]) {
        return parse_jpeg(bytes);
    }
    if bytes.starts_with(b"GIF87a") || bytes.starts_with(b"GIF89a") {
        return parse_gif(bytes);
    }
    if bytes.starts_with(b"RIFF") {
        return parse_webp(bytes);
    }
    if bytes.starts_with(b"BM") {
        return parse_bmp(bytes);
    }
    if b"\x89PNG".starts_with(bytes) || b"GIF87a".starts_with(bytes) || b"GIF89a".starts_with(bytes)
    {
        return Err(AssetError::MalformedMedia);
    }
    Err(AssetError::UnsupportedMedia)
}

fn parse_png(bytes: &[u8]) -> Result<ImageInfo, AssetError> {
    let mut offset = 8_usize;
    let mut dimensions = None;
    let mut saw_idat = false;
    while offset < bytes.len() {
        let header_end = offset.checked_add(8).ok_or(AssetError::MalformedMedia)?;
        if header_end > bytes.len() {
            return Err(AssetError::MalformedMedia);
        }
        let length =
            usize::try_from(be_u32(bytes, offset)?).map_err(|_| AssetError::MalformedMedia)?;
        let chunk_type = &bytes[offset + 4..offset + 8];
        if !chunk_type.iter().all(u8::is_ascii_alphabetic) {
            return Err(AssetError::MalformedMedia);
        }
        let data_start = header_end;
        let data_end = data_start
            .checked_add(length)
            .ok_or(AssetError::MalformedMedia)?;
        let chunk_end = data_end.checked_add(4).ok_or(AssetError::MalformedMedia)?;
        if chunk_end > bytes.len() {
            return Err(AssetError::MalformedMedia);
        }
        let expected_crc = be_u32(bytes, data_end)?;
        if crc32(&bytes[offset + 4..data_end]) != expected_crc {
            return Err(AssetError::MalformedMedia);
        }
        match chunk_type {
            b"IHDR" => {
                if offset != 8 || length != 13 || dimensions.is_some() {
                    return Err(AssetError::MalformedMedia);
                }
                let width = be_u32(bytes, data_start)?;
                let height = be_u32(bytes, data_start + 4)?;
                let bit_depth = bytes[data_start + 8];
                let color_type = bytes[data_start + 9];
                let valid_depth = matches!(
                    (color_type, bit_depth),
                    (0, 1 | 2 | 4 | 8 | 16) | (2 | 4 | 6, 8 | 16) | (3, 1 | 2 | 4 | 8)
                );
                if width == 0
                    || height == 0
                    || !valid_depth
                    || bytes[data_start + 10] != 0
                    || bytes[data_start + 11] != 0
                    || bytes[data_start + 12] > 1
                {
                    return Err(AssetError::MalformedMedia);
                }
                dimensions = Some((width, height));
            }
            b"IDAT" => {
                if dimensions.is_none() || length == 0 {
                    return Err(AssetError::MalformedMedia);
                }
                saw_idat = true;
            }
            b"IEND" => {
                if length != 0 || !saw_idat || chunk_end != bytes.len() {
                    return Err(AssetError::MalformedMedia);
                }
                let (width, height) = dimensions.ok_or(AssetError::MalformedMedia)?;
                return Ok(ImageInfo {
                    media: AssetMedia::Png,
                    width,
                    height,
                });
            }
            _ => {
                if dimensions.is_none() {
                    return Err(AssetError::MalformedMedia);
                }
            }
        }
        offset = chunk_end;
    }
    Err(AssetError::MalformedMedia)
}

fn parse_jpeg(bytes: &[u8]) -> Result<ImageInfo, AssetError> {
    let mut offset = 2_usize;
    let mut dimensions = None;
    let mut saw_scan = false;
    while offset < bytes.len() {
        if bytes[offset] != 0xff {
            return Err(AssetError::MalformedMedia);
        }
        while bytes.get(offset) == Some(&0xff) {
            offset += 1;
        }
        let marker = *bytes.get(offset).ok_or(AssetError::MalformedMedia)?;
        offset += 1;
        if marker == 0xd9 {
            if offset != bytes.len() || !saw_scan {
                return Err(AssetError::MalformedMedia);
            }
            let (width, height) = dimensions.ok_or(AssetError::MalformedMedia)?;
            return Ok(ImageInfo {
                media: AssetMedia::Jpeg,
                width,
                height,
            });
        }
        if marker == 0xd8 || marker == 0x00 {
            return Err(AssetError::MalformedMedia);
        }
        if marker == 0x01 || matches!(marker, 0xd0..=0xd7) {
            continue;
        }
        let segment_length = usize::from(be_u16(bytes, offset)?);
        if segment_length < 2 {
            return Err(AssetError::MalformedMedia);
        }
        let segment_end = offset
            .checked_add(segment_length)
            .ok_or(AssetError::MalformedMedia)?;
        if segment_end > bytes.len() {
            return Err(AssetError::MalformedMedia);
        }
        let data = offset + 2;
        if is_jpeg_sof(marker) {
            if segment_length < 8 || dimensions.is_some() {
                return Err(AssetError::MalformedMedia);
            }
            let height = u32::from(be_u16(bytes, data + 1)?);
            let width = u32::from(be_u16(bytes, data + 3)?);
            if width == 0 || height == 0 || bytes[data + 5] == 0 {
                return Err(AssetError::MalformedMedia);
            }
            dimensions = Some((width, height));
        }
        offset = segment_end;
        if marker == 0xda {
            if dimensions.is_none() {
                return Err(AssetError::MalformedMedia);
            }
            saw_scan = true;
            offset = jpeg_scan_to_marker(bytes, offset)?;
        }
    }
    Err(AssetError::MalformedMedia)
}

fn is_jpeg_sof(marker: u8) -> bool {
    matches!(marker, 0xc0..=0xcf) && !matches!(marker, 0xc4 | 0xc8 | 0xcc)
}

fn jpeg_scan_to_marker(bytes: &[u8], mut offset: usize) -> Result<usize, AssetError> {
    while offset < bytes.len() {
        if bytes[offset] != 0xff {
            offset += 1;
            continue;
        }
        let marker_start = offset;
        while bytes.get(offset) == Some(&0xff) {
            offset += 1;
        }
        let marker = *bytes.get(offset).ok_or(AssetError::MalformedMedia)?;
        if marker == 0x00 || matches!(marker, 0xd0..=0xd7) {
            offset += 1;
            continue;
        }
        return Ok(marker_start);
    }
    Err(AssetError::MalformedMedia)
}

fn parse_gif(bytes: &[u8]) -> Result<ImageInfo, AssetError> {
    if bytes.len() < 13 {
        return Err(AssetError::MalformedMedia);
    }
    let width = u32::from(le_u16(bytes, 6)?);
    let height = u32::from(le_u16(bytes, 8)?);
    if width == 0 || height == 0 {
        return Err(AssetError::MalformedMedia);
    }
    let mut offset = 13_usize;
    let has_global_color_table = bytes[10] & 0x80 != 0;
    if has_global_color_table {
        offset = skip_gif_color_table(bytes, offset, bytes[10] & 0x07)?;
    }
    let mut saw_image = false;
    loop {
        let marker = *bytes.get(offset).ok_or(AssetError::MalformedMedia)?;
        offset += 1;
        match marker {
            0x3b => {
                if !saw_image || offset != bytes.len() {
                    return Err(AssetError::MalformedMedia);
                }
                return Ok(ImageInfo {
                    media: AssetMedia::Gif,
                    width,
                    height,
                });
            }
            0x21 => {
                offset = offset.checked_add(1).ok_or(AssetError::MalformedMedia)?;
                if offset > bytes.len() {
                    return Err(AssetError::MalformedMedia);
                }
                offset = skip_gif_sub_blocks(bytes, offset)?;
            }
            0x2c => {
                let descriptor_end = offset.checked_add(9).ok_or(AssetError::MalformedMedia)?;
                if descriptor_end > bytes.len()
                    || le_u16(bytes, offset + 4)? == 0
                    || le_u16(bytes, offset + 6)? == 0
                {
                    return Err(AssetError::MalformedMedia);
                }
                let packed = bytes[offset + 8];
                offset = descriptor_end;
                let has_local_color_table = packed & 0x80 != 0;
                if has_local_color_table {
                    offset = skip_gif_color_table(bytes, offset, packed & 0x07)?;
                }
                if !has_global_color_table && !has_local_color_table {
                    return Err(AssetError::MalformedMedia);
                }
                let code_size = *bytes.get(offset).ok_or(AssetError::MalformedMedia)?;
                if !(2..=11).contains(&code_size) {
                    return Err(AssetError::MalformedMedia);
                }
                offset += 1;
                offset = skip_gif_sub_blocks(bytes, offset)?;
                saw_image = true;
            }
            _ => return Err(AssetError::MalformedMedia),
        }
    }
}

fn skip_gif_color_table(bytes: &[u8], offset: usize, size_bits: u8) -> Result<usize, AssetError> {
    let entries = 1_usize << (usize::from(size_bits) + 1);
    let end = offset
        .checked_add(entries.checked_mul(3).ok_or(AssetError::MalformedMedia)?)
        .ok_or(AssetError::MalformedMedia)?;
    if end > bytes.len() {
        return Err(AssetError::MalformedMedia);
    }
    Ok(end)
}

fn skip_gif_sub_blocks(bytes: &[u8], mut offset: usize) -> Result<usize, AssetError> {
    loop {
        let length = usize::from(*bytes.get(offset).ok_or(AssetError::MalformedMedia)?);
        offset += 1;
        if length == 0 {
            return Ok(offset);
        }
        offset = offset
            .checked_add(length)
            .ok_or(AssetError::MalformedMedia)?;
        if offset > bytes.len() {
            return Err(AssetError::MalformedMedia);
        }
    }
}

fn parse_webp(bytes: &[u8]) -> Result<ImageInfo, AssetError> {
    if bytes.len() < 12 || &bytes[8..12] != b"WEBP" {
        return Err(AssetError::MalformedMedia);
    }
    let declared_size =
        usize::try_from(le_u32(bytes, 4)?).map_err(|_| AssetError::MalformedMedia)?;
    if declared_size.checked_add(8) != Some(bytes.len()) {
        return Err(AssetError::MalformedMedia);
    }
    let mut offset = 12_usize;
    let mut extended_dimensions = None;
    let mut image_dimensions = None;
    while offset < bytes.len() {
        let header_end = offset.checked_add(8).ok_or(AssetError::MalformedMedia)?;
        if header_end > bytes.len() {
            return Err(AssetError::MalformedMedia);
        }
        let kind = &bytes[offset..offset + 4];
        let length =
            usize::try_from(le_u32(bytes, offset + 4)?).map_err(|_| AssetError::MalformedMedia)?;
        let data_end = header_end
            .checked_add(length)
            .ok_or(AssetError::MalformedMedia)?;
        if data_end > bytes.len() {
            return Err(AssetError::MalformedMedia);
        }
        let data = &bytes[header_end..data_end];
        match kind {
            b"VP8X" => {
                if data.len() != 10 || extended_dimensions.is_some() {
                    return Err(AssetError::MalformedMedia);
                }
                extended_dimensions = Some((le_u24(data, 4)? + 1, le_u24(data, 7)? + 1));
            }
            b"VP8 " => {
                if data.len() < 10
                    || image_dimensions.is_some()
                    || data.get(3..6) != Some(b"\x9d\x01\x2a")
                {
                    return Err(AssetError::MalformedMedia);
                }
                let width = u32::from(le_u16(data, 6)? & 0x3fff);
                let height = u32::from(le_u16(data, 8)? & 0x3fff);
                image_dimensions = Some((width, height));
            }
            b"VP8L" => {
                if data.len() < 5 || image_dimensions.is_some() || data[0] != 0x2f {
                    return Err(AssetError::MalformedMedia);
                }
                let bits = le_u32(data, 1)?;
                image_dimensions = Some(((bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1));
            }
            _ => {}
        }
        if length & 1 != 0 && bytes.get(data_end) != Some(&0) {
            return Err(AssetError::MalformedMedia);
        }
        offset = data_end + (length & 1);
        if offset > bytes.len() {
            return Err(AssetError::MalformedMedia);
        }
    }
    let (width, height) = image_dimensions.ok_or(AssetError::MalformedMedia)?;
    if width == 0
        || height == 0
        || extended_dimensions.is_some_and(|value| value != (width, height))
    {
        return Err(AssetError::MalformedMedia);
    }
    Ok(ImageInfo {
        media: AssetMedia::Webp,
        width,
        height,
    })
}

fn parse_bmp(bytes: &[u8]) -> Result<ImageInfo, AssetError> {
    if bytes.len() < 26 {
        return Err(AssetError::MalformedMedia);
    }
    let file_size = usize::try_from(le_u32(bytes, 2)?).map_err(|_| AssetError::MalformedMedia)?;
    let pixel_offset =
        usize::try_from(le_u32(bytes, 10)?).map_err(|_| AssetError::MalformedMedia)?;
    let dib_size = le_u32(bytes, 14)?;
    if file_size != bytes.len() || pixel_offset >= bytes.len() {
        return Err(AssetError::MalformedMedia);
    }
    let (width, height, planes, bits_per_pixel, compression, dib_end) = if dib_size == 12 {
        (
            u32::from(le_u16(bytes, 18)?),
            u32::from(le_u16(bytes, 20)?),
            le_u16(bytes, 22)?,
            le_u16(bytes, 24)?,
            0,
            26,
        )
    } else if dib_size >= 40 {
        let dib_end = 14_usize
            .checked_add(usize::try_from(dib_size).map_err(|_| AssetError::MalformedMedia)?)
            .ok_or(AssetError::MalformedMedia)?;
        if dib_end > bytes.len() {
            return Err(AssetError::MalformedMedia);
        }
        let signed_width = le_i32(bytes, 18)?;
        let signed_height = le_i32(bytes, 22)?;
        if signed_width <= 0 || signed_height == 0 || signed_height == i32::MIN {
            return Err(AssetError::MalformedMedia);
        }
        (
            signed_width.cast_unsigned(),
            signed_height.unsigned_abs(),
            le_u16(bytes, 26)?,
            le_u16(bytes, 28)?,
            le_u32(bytes, 30)?,
            dib_end,
        )
    } else {
        return Err(AssetError::MalformedMedia);
    };
    let valid_encoding = match compression {
        0 => matches!(bits_per_pixel, 1 | 4 | 8 | 16 | 24 | 32),
        1 => bits_per_pixel == 8,
        2 => bits_per_pixel == 4,
        3 | 6 => matches!(bits_per_pixel, 16 | 32),
        _ => false,
    };
    if width == 0
        || height == 0
        || planes != 1
        || !valid_encoding
        || pixel_offset < dib_end
        || bytes[6..10] != [0; 4]
    {
        return Err(AssetError::MalformedMedia);
    }
    if compression == 0 {
        let row_bits = u64::from(width)
            .checked_mul(u64::from(bits_per_pixel))
            .ok_or(AssetError::MalformedMedia)?;
        let row_bytes = row_bits.checked_add(31).ok_or(AssetError::MalformedMedia)? / 32 * 4;
        let pixel_bytes = row_bytes
            .checked_mul(u64::from(height))
            .ok_or(AssetError::MalformedMedia)?;
        if pixel_bytes > (bytes.len() - pixel_offset) as u64 {
            return Err(AssetError::MalformedMedia);
        }
    }
    Ok(ImageInfo {
        media: AssetMedia::Bmp,
        width,
        height,
    })
}

fn validate_dimensions(width: u32, height: u32, limits: AssetLimits) -> Result<(), AssetError> {
    if width > limits.config().max_dimension_px || height > limits.config().max_dimension_px {
        return Err(AssetError::DimensionLimit);
    }
    let pixels = u64::from(width)
        .checked_mul(u64::from(height))
        .ok_or(AssetError::DimensionLimit)?;
    if pixels > limits.config().max_pixels {
        return Err(AssetError::DimensionLimit);
    }
    Ok(())
}

fn be_u16(bytes: &[u8], offset: usize) -> Result<u16, AssetError> {
    let raw = bytes
        .get(offset..offset + 2)
        .ok_or(AssetError::MalformedMedia)?;
    Ok(u16::from_be_bytes([raw[0], raw[1]]))
}

fn be_u32(bytes: &[u8], offset: usize) -> Result<u32, AssetError> {
    let raw = bytes
        .get(offset..offset + 4)
        .ok_or(AssetError::MalformedMedia)?;
    Ok(u32::from_be_bytes([raw[0], raw[1], raw[2], raw[3]]))
}

fn le_u16(bytes: &[u8], offset: usize) -> Result<u16, AssetError> {
    let raw = bytes
        .get(offset..offset + 2)
        .ok_or(AssetError::MalformedMedia)?;
    Ok(u16::from_le_bytes([raw[0], raw[1]]))
}

fn le_u24(bytes: &[u8], offset: usize) -> Result<u32, AssetError> {
    let raw = bytes
        .get(offset..offset + 3)
        .ok_or(AssetError::MalformedMedia)?;
    Ok(u32::from(raw[0]) | (u32::from(raw[1]) << 8) | (u32::from(raw[2]) << 16))
}

fn le_u32(bytes: &[u8], offset: usize) -> Result<u32, AssetError> {
    let raw = bytes
        .get(offset..offset + 4)
        .ok_or(AssetError::MalformedMedia)?;
    Ok(u32::from_le_bytes([raw[0], raw[1], raw[2], raw[3]]))
}

fn le_i32(bytes: &[u8], offset: usize) -> Result<i32, AssetError> {
    let raw = bytes
        .get(offset..offset + 4)
        .ok_or(AssetError::MalformedMedia)?;
    Ok(i32::from_le_bytes([raw[0], raw[1], raw[2], raw[3]]))
}

fn crc32(bytes: &[u8]) -> u32 {
    let mut crc = u32::MAX;
    for byte in bytes {
        let index = usize::from(crc.to_le_bytes()[0] ^ *byte);
        crc = (crc >> 8) ^ CRC32_TABLE[index];
    }
    !crc
}

#[allow(clippy::cast_possible_truncation)]
const fn crc32_table() -> [u32; 256] {
    let mut table = [0_u32; 256];
    let mut index = 0_usize;
    while index < 256 {
        // The loop bound proves that every index fits in u32.
        let mut value = index as u32;
        let mut bit = 0;
        while bit < 8 {
            value = (value >> 1) ^ (0xedb8_8320 & (0_u32.wrapping_sub(value & 1)));
            bit += 1;
        }
        table[index] = value;
        index += 1;
    }
    table
}

#[derive(Debug, Error)]
pub enum AssetError {
    #[error("invalid finite asset limit for {field}: {value} (ceiling {ceiling})")]
    InvalidLimit {
        field: &'static str,
        value: u64,
        ceiling: u64,
    },
    #[error("asset payload is empty")]
    EmptyAsset,
    #[error("asset payload exceeds the configured byte limit")]
    AssetTooLarge,
    #[error("asset media type is outside the finite image profile")]
    UnsupportedMedia,
    #[error("declared asset media type disagrees with sniffed content")]
    DeclaredMediaMismatch,
    #[error("asset media structure is malformed or truncated")]
    MalformedMedia,
    #[error("asset image dimensions exceed a configured limit")]
    DimensionLimit,
    #[error("existing package asset inventory exceeds a configured limit")]
    ExistingAssetLimit,
    #[error("existing asset relationship is missing, ambiguous, or inconsistent")]
    RelationshipBroken,
    #[error("existing asset bytes have a conflicting declared media type")]
    ExistingAssetMediaMismatch,
    #[error("deterministic asset relationship ID collides with another target")]
    RelationshipIdCollision,
    #[error("deterministic asset package part collides with another part")]
    PartCollision,
    #[error("source package graph changed before asset lowering")]
    SourceGraphDrift,
    #[error("asset plan does not match recomputed source and payload state")]
    PlanMismatch,
    #[error("private asset plan JSON exceeds its configured bound")]
    PlanJsonTooLarge,
    #[error("private asset plan JSON is invalid")]
    InvalidJson(#[from] serde_json::Error),
    #[error("asset plan schema or profile version is unsupported")]
    UnsupportedVersion,
    #[error("private asset plan digest is invalid or untrusted")]
    UntrustedPlan,
    #[error("asset pipeline allocation failed")]
    AllocationFailed,
    #[error("generated asset package path is invalid")]
    Package(#[from] PackageError),
    #[error("asset patch intent construction failed")]
    Patch(#[from] PatchError),
}

impl AssetError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit { .. } => "asset_invalid_limit",
            Self::EmptyAsset => "asset_empty",
            Self::AssetTooLarge => "asset_too_large",
            Self::UnsupportedMedia => "asset_unsupported_media",
            Self::DeclaredMediaMismatch => "asset_declared_media_mismatch",
            Self::MalformedMedia => "asset_malformed_media",
            Self::DimensionLimit => "asset_dimension_limit",
            Self::ExistingAssetLimit => "asset_existing_inventory_limit",
            Self::RelationshipBroken => "asset_relationship_broken",
            Self::ExistingAssetMediaMismatch => "asset_existing_media_mismatch",
            Self::RelationshipIdCollision => "asset_relationship_id_collision",
            Self::PartCollision => "asset_part_collision",
            Self::SourceGraphDrift => "asset_source_graph_drift",
            Self::PlanMismatch => "asset_plan_mismatch",
            Self::PlanJsonTooLarge => "asset_plan_json_too_large",
            Self::InvalidJson(_) => "asset_invalid_json",
            Self::UnsupportedVersion => "asset_unsupported_version",
            Self::UntrustedPlan => "asset_untrusted_plan",
            Self::AllocationFailed => "asset_allocation_failed",
            Self::Package(error) => error.code(),
            Self::Patch(error) => error.code(),
        }
    }
}
