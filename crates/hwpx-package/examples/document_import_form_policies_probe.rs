//! Fresh actual-source binding with EXPLICIT TEST policies, no real issuer/native oracle.
mod document_import_form_policies_support;
use document_import_form_policies_support::{
    explicit_test_policies, fixture_bytes, fixture_manifest,
};
use domain_ir::DocumentId;
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    forms::{
        ImportedDocumentForms,
        policies::{FormPolicyBindingReceipt, FormPolicySourceBinding, PolicyBoundDocumentForms},
    },
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::error::Error;

#[derive(Serialize)]
struct Evidence {
    profile: &'static str,
    policy_authority: &'static str,
    cases: usize,
    policy_bound_forms: usize,
    kinds: [usize; 5],
    receipts: Vec<FormPolicyBindingReceipt>,
}
fn main() -> Result<(), Box<dyn Error>> {
    let (_, manifest) = fixture_manifest()?;
    let mut evidence = Evidence {
        profile: "hwpx-agent.explicit-form-policy-probe/v1",
        policy_authority: "explicit_test_choices_not_real_provider_or_native_defaults",
        cases: 0,
        policy_bound_forms: 0,
        kinds: [0; 5],
        receipts: vec![],
    };
    for row in manifest["cases"].as_array().ok_or("cases")? {
        for kind in ["source", "output"] {
            let bytes = fixture_bytes(row["case"].as_str().ok_or("case")?, kind)?;
            let imported = ImportedDocumentForms::import(ImportedSourcePackage::import(
                &bytes,
                DocumentId::parse("actual-policy-probe")?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
            )?)?;
            let binding = FormPolicySourceBinding::for_imported(&imported);
            let policies = explicit_test_policies(&imported);
            let bound = PolicyBoundDocumentForms::bind(&imported, &binding, &policies)?;
            if bound.verify_source(&bytes, &binding, &policies)? != *bound.receipt() {
                return Err("fresh policy/source drift".into());
            }
            evidence.cases += 1;
            evidence.policy_bound_forms += bound.receipt().form_controls;
            for (sum, value) in evidence.kinds.iter_mut().zip(bound.receipt().kinds) {
                *sum += value;
            }
            evidence.receipts.push(bound.receipt().clone());
        }
    }
    if evidence.cases != 10
        || evidence.policy_bound_forms != 50
        || evidence.kinds != [10, 8, 16, 8, 8]
    {
        return Err("policy corpus count".into());
    }
    println!("{}", serde_json::to_string(&evidence)?);
    Ok(())
}
