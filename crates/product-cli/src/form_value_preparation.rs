//! Product-layer preparation only; no native, route or artifact publication authority.
use std::{fmt, io};

use domain_ir::{
    FormControlLimitConfig, FormControlLimits,
    form_input::{FormInputAccessPolicy, FormInputBuilder, FormInputRequest},
};
use hwpx_package::{
    NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackagePolicy,
    native_form_value_output::{
        NativeFormValueLimits, NativeFormValueLowerer, NativeFormValueOutput, NativeFormValuePlan,
        NativeFormValueReader, NativeFormValueReceipt,
    },
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const FORM_VALUE_PREPARATION_PROFILE: &str = "hwpx-agent.product-form-value-preparation/v1";
const MAX_PRIVATE_BINDING_BYTES: usize = 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FormValuePreparationLimits {
    domain: FormControlLimits,
    package: NativeFormPackageLimits,
    output: NativeFormValueLimits,
}
impl FormValuePreparationLimits {
    /// Creates finite SDK limits without clamping or loosening the product envelope.
    /// # Errors
    /// Rejects domain JSON bounds above the declared one MiB envelope.
    pub fn new(
        domain: FormControlLimits,
        package: NativeFormPackageLimits,
        output: NativeFormValueLimits,
    ) -> Result<Self, FormValuePreparationError> {
        if domain.config().output_bytes > MAX_PRIVATE_BINDING_BYTES {
            return Err(FormValuePreparationError::Limit);
        }
        Ok(Self {
            domain,
            package,
            output,
        })
    }
    /// Creates the bounded default product preparation profile.
    /// # Errors
    /// Rejects invalid typed SDK bounds.
    pub fn bounded_default() -> Result<Self, FormValuePreparationError> {
        Self::new(
            FormControlLimits::new(FormControlLimitConfig::default())
                .map_err(|_| FormValuePreparationError::Limit)?,
            NativeFormPackageLimits::default(),
            NativeFormValueLimits::default(),
        )
    }
}

/// Provider-owned complete source/map/caller-policy context; never a public action payload.
pub struct FormValueContext<'a> {
    source: &'a [u8],
    map: &'a NativeFormPackageMap,
    policies: &'a [NativeFormPackagePolicy],
    limits: FormValuePreparationLimits,
}
impl fmt::Debug for FormValueContext<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormValueContext(<redacted>)")
    }
}
impl<'a> FormValueContext<'a> {
    /// Binds references to a complete fresh provider snapshot, not a path or user-supplied XML map.
    /// # Errors
    /// Rejects incomplete or stale package/policy bindings through the actual public SDK.
    pub fn bind(
        source: &'a [u8],
        map: &'a NativeFormPackageMap,
        policies: &'a [NativeFormPackagePolicy],
        limits: FormValuePreparationLimits,
    ) -> Result<Self, FormValuePreparationError> {
        let context = Self {
            source,
            map,
            policies,
            limits,
        };
        context.read()?;
        context.fingerprint()?;
        Ok(context)
    }
    fn read(
        &self,
    ) -> Result<
        hwpx_package::native_form_value_output::NativeFormValueReadback,
        FormValuePreparationError,
    > {
        NativeFormValueReader::read(
            self.source,
            self.map,
            self.policies,
            self.limits.domain,
            self.limits.package,
        )
        .map_err(|_| FormValuePreparationError::Binding)
    }
    fn fingerprint(&self) -> Result<String, FormValuePreparationError> {
        let mut writer = HashWriter::new(MAX_PRIVATE_BINDING_BYTES);
        serde_json::to_writer(
            &mut writer,
            &(
                FORM_VALUE_PREPARATION_PROFILE,
                hex::encode(Sha256::digest(self.source)),
                self.map,
                self.policies,
            ),
        )
        .map_err(|_| FormValuePreparationError::Limit)?;
        Ok(writer.finish())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormValuePreparationQualification {
    ProductPreparationOnlyRoutePublicationNativeAndGateUnqualified,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FormValuePreparationReceipt {
    pub profile: &'static str,
    pub raw_request_sha256: String,
    pub canonical_request_sha256: String,
    pub provider_context_sha256: String,
    pub candidate_bytes: usize,
    pub component: NativeFormValueReceipt,
    pub qualification: FormValuePreparationQualification,
}

/// Private sealed preparation. Cannot be deserialized or used as a route authorization.
pub struct PreparedFormValues {
    plan: NativeFormValuePlan,
    output: NativeFormValueOutput,
    receipt: FormValuePreparationReceipt,
    limits: FormValuePreparationLimits,
    seal: String,
}
impl fmt::Debug for PreparedFormValues {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedFormValues(<redacted>)")
    }
}
impl PreparedFormValues {
    /// Complete in-memory source-qualified candidate, NOT a publishable product artifact.
    #[must_use]
    pub fn candidate_bytes(&self) -> &[u8] {
        self.output.bytes()
    }
    #[must_use]
    pub const fn receipt(&self) -> &FormValuePreparationReceipt {
        &self.receipt
    }
    /// Revalidates all caller-policy/map/source/limit/access bindings and the complete output.
    /// # Errors
    /// Rejects any stale provider context, changed limit, forged seal or output mismatch.
    pub fn verify(
        &self,
        fresh: &FormValueContext<'_>,
        access: &FormInputAccessPolicy,
    ) -> Result<FormValuePreparationReceipt, FormValuePreparationError> {
        if fresh.limits != self.limits
            || fresh.fingerprint()? != self.receipt.provider_context_sha256
            || self.digest()? != self.seal
        {
            return Err(FormValuePreparationError::Drift);
        }
        fresh.read()?;
        let receipt = NativeFormValueLowerer::verify_output(
            fresh.source,
            &self.plan,
            self.output.bytes(),
            access,
            self.limits.domain,
            self.limits.package,
            self.limits.output,
        )
        .map_err(|_| FormValuePreparationError::Output)?;
        if receipt != self.receipt.component
            || self.output.receipt() != &receipt
            || self.output.bytes().len() != self.receipt.candidate_bytes
        {
            return Err(FormValuePreparationError::Drift);
        }
        Ok(self.receipt.clone())
    }
    /// Checks the actual current signed authority WITHOUT treating its VS0 scope as forms proof.
    /// # Errors
    /// Always denies forms publication under the current VS0-only attestation.
    pub fn require_current_product_route(
        &self,
        fresh: &FormValueContext<'_>,
        access: &FormInputAccessPolicy,
    ) -> Result<(), FormValuePreparationError> {
        self.verify(fresh, access)?;
        crate::verify_route_attestation().map_err(|_| FormValuePreparationError::RouteAuthority)?;
        // P04 attests document.create_vs0 only. No form route/runtime evidence exists.
        // Do not infer form authority from a valid unrelated signature or caller boolean.
        Err(FormValuePreparationError::RouteUnqualified)
    }
    fn digest(&self) -> Result<String, FormValuePreparationError> {
        let mut writer = HashWriter::new(MAX_PRIVATE_BINDING_BYTES);
        serde_json::to_writer(&mut writer, &self.receipt)
            .map_err(|_| FormValuePreparationError::Limit)?;
        Ok(writer.finish())
    }
}

#[derive(Debug)]
pub struct FormValuePreparation;
impl FormValuePreparation {
    /// Runs the real typed JSON request, whole-source binding, atomic value output and fresh reread.
    /// The JSON contains only governed targets/values/digests, never XML, COM IDs or paths.
    /// # Errors
    /// Rejects malformed/duplicate/unknown/coerced JSON, stale state/flow/access, unsupported
    /// profiles, partial radio/default changes and output/preservation/finite-limit failures.
    pub fn prepare_json(
        context: &FormValueContext<'_>,
        request_json: &[u8],
        access: &FormInputAccessPolicy,
    ) -> Result<PreparedFormValues, FormValuePreparationError> {
        let limits = context.limits;
        let observed = context.read()?;
        let flow = observed.native_v1().document_flow_sha256();
        let request =
            FormInputRequest::from_json(request_json, observed.state(), flow, limits.domain)
                .map_err(|_| FormValuePreparationError::Request)?;
        let typed = FormInputBuilder::plan(observed.state(), &request, flow, limits.domain)
            .map_err(|_| FormValuePreparationError::Request)?;
        let plan = NativeFormValuePlan::bind(
            context.source,
            context.map,
            context.policies,
            &typed,
            access,
            limits.domain,
            limits.package,
        )
        .map_err(|_| FormValuePreparationError::Binding)?;
        let output = NativeFormValueLowerer::lower(
            context.source,
            &plan,
            access,
            limits.domain,
            limits.package,
            limits.output,
        )
        .map_err(|_| FormValuePreparationError::Output)?;
        let receipt=FormValuePreparationReceipt {
            profile:FORM_VALUE_PREPARATION_PROFILE,
            raw_request_sha256:hex::encode(Sha256::digest(request_json)),
            canonical_request_sha256:hex::encode(Sha256::digest(request.canonical_json(limits.domain).map_err(|_|FormValuePreparationError::Limit)?)),
            provider_context_sha256:context.fingerprint()?,
            candidate_bytes:output.bytes().len(),
            component:output.receipt().clone(),
            qualification:FormValuePreparationQualification::ProductPreparationOnlyRoutePublicationNativeAndGateUnqualified,
        };
        let mut prepared = PreparedFormValues {
            plan,
            output,
            receipt,
            limits,
            seal: String::new(),
        };
        prepared.seal = prepared.digest()?;
        prepared.verify(context, access)?;
        Ok(prepared)
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormValuePreparationError {
    #[error("FORM_VALUE_PREPARATION_LIMIT")]
    Limit,
    #[error("FORM_VALUE_PREPARATION_BINDING_REJECTED")]
    Binding,
    #[error("FORM_VALUE_PREPARATION_REQUEST_REJECTED")]
    Request,
    #[error("FORM_VALUE_PREPARATION_OUTPUT_REJECTED")]
    Output,
    #[error("FORM_VALUE_PREPARATION_FRESH_CONTEXT_DRIFT")]
    Drift,
    #[error("FORM_VALUE_PRODUCT_ROUTE_AUTHORITY_REJECTED")]
    RouteAuthority,
    #[error("FORM_VALUE_PRODUCT_ROUTE_UNQUALIFIED")]
    RouteUnqualified,
}

struct HashWriter {
    digest: Sha256,
    count: usize,
    limit: usize,
}
impl HashWriter {
    fn new(limit: usize) -> Self {
        Self {
            digest: Sha256::new(),
            count: 0,
            limit,
        }
    }
    fn finish(self) -> String {
        hex::encode(self.digest.finalize())
    }
}
impl io::Write for HashWriter {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let count = self
            .count
            .checked_add(bytes.len())
            .filter(|n| *n <= self.limit)
            .ok_or_else(|| io::Error::other("form binding limit"))?;
        self.digest.update(bytes);
        self.count = count;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::HashWriter;
    use sha2::Digest as _;
    use std::io::Write as _;
    #[test]
    fn private_binding_writer_checks_limit_before_hash_or_count_change() {
        let mut writer = HashWriter::new(3);
        assert!(writer.write_all(b"abc").is_ok());
        let digest = writer.digest.clone();
        assert!(writer.write_all(b"d").is_err());
        assert_eq!(writer.count, 3);
        assert_eq!(writer.digest.finalize(), digest.finalize());
    }
    #[test]
    fn private_binding_writer_rejects_arithmetic_overflow_without_mutation() {
        let mut writer = HashWriter::new(usize::MAX);
        writer.count = usize::MAX;
        assert!(writer.write_all(b"x").is_err());
        assert_eq!(writer.count, usize::MAX);
    }
}
