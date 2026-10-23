//! Original validated native bindings retained by the immutable source-policy binder.
//! Source-local reservations are not persistent XML identities or execution authority.
use super::PolicyBoundDocumentForms;
use crate::{NativeFormPackageMap, NativeFormPackagePolicy};
use std::fmt;

/// Cannot be constructed or deserialized by consumers. Holds the exact map and
/// merged policies checked by the original package/domain binder, without re-merging.
/// Cached access alone does not establish current source, ACL or policy authority.
#[derive(Eq, PartialEq)]
pub struct BoundNativeFormPolicies {
    map: NativeFormPackageMap,
    policies: Vec<NativeFormPackagePolicy>,
}
impl fmt::Debug for BoundNativeFormPolicies {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("BoundNativeFormPolicies(<redacted>)")
    }
}
impl BoundNativeFormPolicies {
    pub(super) const fn new(
        map: NativeFormPackageMap,
        policies: Vec<NativeFormPackagePolicy>,
    ) -> Self {
        Self { map, policies }
    }

    #[must_use]
    pub const fn map(&self) -> &NativeFormPackageMap {
        &self.map
    }

    #[must_use]
    pub fn policies(&self) -> &[NativeFormPackagePolicy] {
        &self.policies
    }
}
impl PolicyBoundDocumentForms<'_> {
    /// Memory bindings only. Stored consumers must re-authorize the whole source
    /// and latest policy before preparation, verification or a route check.
    #[must_use]
    pub const fn native_binding(&self) -> &BoundNativeFormPolicies {
        &self.native
    }
}
