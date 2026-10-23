//! Actual product-library color preparation; native and signed publication remain closed.
use domain_ir::{FormControlLimitConfig, FormControlLimits};
use hwpx_package::{
    NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackagePolicy,
    NativeFormPackageReader,
    native_form_color::{
        NativeFormColorLimits, NativeFormColorOutput, NativeFormColorPlan, NativeFormColorPreparer,
        NativeFormColorReceipt, NativeFormColorRequest,
    },
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    fmt,
    io::{self, Write},
};
use thiserror::Error;
const BINDING_LIMIT: usize = 1024 * 1024;
pub const FORM_COLOR_PREPARATION_PROFILE: &str = "hwpx-agent.product-form-color-preparation/v1";
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FormColorPreparationLimits {
    domain: FormControlLimits,
    package: NativeFormPackageLimits,
    output: NativeFormColorLimits,
}
impl FormColorPreparationLimits {
    /// Creates the bounded default product preparation profile.
    /// # Errors
    /// Rejects invalid typed limits.
    pub fn bounded_default() -> Result<Self, FormColorPreparationError> {
        Ok(Self {
            domain: FormControlLimits::new(FormControlLimitConfig::default())
                .map_err(|_| FormColorPreparationError::Limit)?,
            package: NativeFormPackageLimits::default(),
            output: NativeFormColorLimits::default(),
        })
    }
}
/// Provider-owned complete source/map/policy references, not public paths or COM parameters.
pub struct FormColorContext<'a> {
    source: &'a [u8],
    map: &'a NativeFormPackageMap,
    policies: &'a [NativeFormPackagePolicy],
    limits: FormColorPreparationLimits,
}
impl fmt::Debug for FormColorContext<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormColorContext(<redacted>)")
    }
}
impl<'a> FormColorContext<'a> {
    /// Rechecks real complete package and explicit caller policies before preparation.
    /// # Errors
    /// Rejects malformed, mismatched, protected or unbounded provider context.
    pub fn bind(
        source: &'a [u8],
        map: &'a NativeFormPackageMap,
        policies: &'a [NativeFormPackagePolicy],
        limits: FormColorPreparationLimits,
    ) -> Result<Self, FormColorPreparationError> {
        let value = Self {
            source,
            map,
            policies,
            limits,
        };
        value.fingerprint()?;
        Ok(value)
    }
    fn fingerprint(&self) -> Result<String, FormColorPreparationError> {
        let observed = NativeFormPackageReader::read(self.source, self.map, self.limits.package)
            .map_err(|_| FormColorPreparationError::Binding)?;
        observed
            .bind_policies(self.policies, self.limits.domain)
            .map_err(|_| FormColorPreparationError::Binding)?;
        if observed.bindings().protection_signal_observed() {
            return Err(FormColorPreparationError::Protection);
        }
        let mut writer = HashWriter::new();
        serde_json::to_writer(
            &mut writer,
            &(
                FORM_COLOR_PREPARATION_PROFILE,
                observed.package_sha256(),
                self.map,
                self.policies,
            ),
        )
        .map_err(|_| FormColorPreparationError::Limit)?;
        Ok(writer.finish())
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FormColorPreparationReceipt {
    pub profile: &'static str,
    pub provider_context_sha256: String,
    pub typed_request_sha256: String,
    pub candidate_bytes: usize,
    pub component: NativeFormColorReceipt,
    pub qualification: &'static str,
}
pub struct PreparedFormColors {
    plan: NativeFormColorPlan,
    output: NativeFormColorOutput,
    receipt: FormColorPreparationReceipt,
    limits: FormColorPreparationLimits,
}
impl fmt::Debug for PreparedFormColors {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedFormColors(<redacted>)")
    }
}
impl PreparedFormColors {
    #[must_use]
    pub fn candidate_bytes(&self) -> &[u8] {
        self.output.bytes()
    }
    #[must_use]
    pub const fn receipt(&self) -> &FormColorPreparationReceipt {
        &self.receipt
    }
    /// Revalidates fresh whole source/map/policies and external candidate output.
    /// # Errors
    /// Rejects provider context drift or any whole-output/receipt mismatch.
    pub fn verify(
        &self,
        fresh: &FormColorContext<'_>,
    ) -> Result<FormColorPreparationReceipt, FormColorPreparationError> {
        if fresh.limits != self.limits
            || fresh.fingerprint()? != self.receipt.provider_context_sha256
        {
            return Err(FormColorPreparationError::Drift);
        }
        let actual = NativeFormColorPreparer::verify_output(
            fresh.source,
            &self.plan,
            self.output.bytes(),
            self.limits.domain,
            self.limits.package,
            self.limits.output,
        )
        .map_err(|_| FormColorPreparationError::Output)?;
        if self.output.receipt() != &actual
            || self.receipt.component != actual
            || self.receipt.candidate_bytes != self.output.bytes().len()
        {
            return Err(FormColorPreparationError::Drift);
        }
        Ok(self.receipt.clone())
    }
    /// Checks real signed authority; current VS0-only evidence does not authorize forms.
    /// # Errors
    /// Always denies color/form publication under the current actual attestation.
    pub fn require_current_product_route(
        &self,
        fresh: &FormColorContext<'_>,
    ) -> Result<(), FormColorPreparationError> {
        self.verify(fresh)?;
        crate::verify_route_attestation().map_err(|_| FormColorPreparationError::RouteAuthority)?;
        Err(FormColorPreparationError::RouteUnqualified)
    }
}
#[derive(Debug)]
pub struct FormColorPreparation;
impl FormColorPreparation {
    /// Compiles exact typed color intent through the real coupled full-package SDK.
    /// # Errors
    /// Rejects stale provider bindings, missing/duplicate/invalid intent or preservation drift.
    pub fn prepare(
        context: &FormColorContext<'_>,
        requests: &[NativeFormColorRequest],
    ) -> Result<PreparedFormColors, FormColorPreparationError> {
        let fingerprint = context.fingerprint()?;
        let limits = context.limits;
        let plan = NativeFormColorPlan::bind(
            context.source,
            context.map,
            context.policies,
            requests,
            limits.domain,
            limits.package,
        )
        .map_err(|_| FormColorPreparationError::Request)?;
        let mut writer = HashWriter::new();
        serde_json::to_writer(&mut writer, requests)
            .map_err(|_| FormColorPreparationError::Limit)?;
        let output = NativeFormColorPreparer::prepare(
            context.source,
            &plan,
            limits.domain,
            limits.package,
            limits.output,
        )
        .map_err(|_| FormColorPreparationError::Output)?;
        let receipt = FormColorPreparationReceipt {
            profile: FORM_COLOR_PREPARATION_PROFILE,
            provider_context_sha256: fingerprint,
            typed_request_sha256: writer.finish(),
            candidate_bytes: output.bytes().len(),
            component: output.receipt().clone(),
            qualification: "product_preparation_only_route_native_and_gate_unqualified",
        };
        let value = PreparedFormColors {
            plan,
            output,
            receipt,
            limits,
        };
        value.verify(context)?;
        Ok(value)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormColorPreparationError {
    #[error("FORM_COLOR_PREPARATION_LIMIT")]
    Limit,
    #[error("FORM_COLOR_PREPARATION_BINDING_REJECTED")]
    Binding,
    #[error("FORM_COLOR_PREPARATION_PROTECTION_REJECTED")]
    Protection,
    #[error("FORM_COLOR_PREPARATION_REQUEST_REJECTED")]
    Request,
    #[error("FORM_COLOR_PREPARATION_OUTPUT_REJECTED")]
    Output,
    #[error("FORM_COLOR_PREPARATION_DRIFT_REJECTED")]
    Drift,
    #[error("FORM_COLOR_PREPARATION_ROUTE_AUTHORITY_REJECTED")]
    RouteAuthority,
    #[error("FORM_COLOR_PREPARATION_ROUTE_UNQUALIFIED")]
    RouteUnqualified,
}
struct HashWriter {
    hash: Sha256,
    bytes: usize,
}
impl HashWriter {
    fn new() -> Self {
        Self {
            hash: Sha256::new(),
            bytes: 0,
        }
    }
    fn finish(self) -> String {
        hex::encode(self.hash.finalize())
    }
}
impl Write for HashWriter {
    fn write(&mut self, raw: &[u8]) -> io::Result<usize> {
        let next = self
            .bytes
            .checked_add(raw.len())
            .filter(|n| *n <= BINDING_LIMIT)
            .ok_or_else(|| {
                io::Error::new(io::ErrorKind::FileTooLarge, "form color binding bound")
            })?;
        self.hash.update(raw);
        self.bytes = next;
        Ok(raw.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bounded_hash_writer_rejects_overrun_before_hash_or_byte_count_change()
    -> Result<(), io::Error> {
        let mut writer = HashWriter::new();
        writer.write_all(&vec![b'x'; BINDING_LIMIT])?;
        let hash = writer.hash.clone().finalize();
        let count = writer.bytes;
        assert_eq!(
            writer.write(b"x").err().map(|e| e.kind()),
            Some(io::ErrorKind::FileTooLarge)
        );
        assert_eq!(writer.bytes, count);
        assert_eq!(writer.hash.finalize(), hash);
        Ok(())
    }
}
