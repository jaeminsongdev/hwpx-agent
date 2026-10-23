//! Private wire DTOs; no raw source/current value/style/execution fields or silent defaults.
use super::{
    MAX_POLICY_BYTES, SOURCE_POLICY_PAYLOAD_SCHEMA, SourcePolicyBinding, StoredSourcePolicyError,
};
use domain_ir::{
    FormButtonValue, FormSelectionValidation, FormTextValidation, LogicalId, SourceAnchorHandle,
};
use hwpx_package::document_import::forms::policies::{ExplicitFormPolicy, SourceFormPolicy};
use serde::{Deserialize, Deserializer};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Envelope {
    schema_version: String,
    binding: SourcePolicyBinding,
    policies: Vec<Policy>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Policy {
    node_id: LogicalId,
    source_anchor: SourceAnchorHandle,
    values: Values,
}
#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
enum Values {
    Text {
        default_value: String,
        validation: TextValidation,
    },
    Checkbox {
        default_value: FormButtonValue,
        must_be_checked: bool,
    },
    Radio {
        default_value: FormButtonValue,
        group_required: bool,
    },
    Combo {
        #[serde(deserialize_with = "required_option")]
        default_selected_value: Option<String>,
        validation: SelectionValidation,
    },
    List {
        #[serde(deserialize_with = "required_option")]
        default_selected_value: Option<String>,
        validation: SelectionValidation,
    },
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TextValidation {
    required: bool,
    minimum_characters: u32,
    #[serde(deserialize_with = "required_option")]
    maximum_characters: Option<u32>,
    #[serde(deserialize_with = "required_option")]
    external_validator_sha256: Option<String>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SelectionValidation {
    required: bool,
    #[serde(deserialize_with = "required_option")]
    external_validator_sha256: Option<String>,
}
fn required_option<'de, D, T>(d: D) -> Result<Option<T>, D::Error>
where
    D: Deserializer<'de>,
    T: Deserialize<'de>,
{
    Option::<T>::deserialize(d)
}
pub(super) fn decode(
    bytes: &[u8],
    binding: &SourcePolicyBinding,
) -> Result<Vec<SourceFormPolicy>, StoredSourcePolicyError> {
    if bytes.is_empty() || bytes.len() > MAX_POLICY_BYTES {
        return Err(StoredSourcePolicyError::Payload);
    }
    let e: Envelope =
        serde_json::from_slice(bytes).map_err(|_| StoredSourcePolicyError::Payload)?;
    if e.schema_version != SOURCE_POLICY_PAYLOAD_SCHEMA
        || e.binding != *binding
        || e.policies.is_empty()
        || e.policies.len() > 4096
    {
        return Err(StoredSourcePolicyError::Payload);
    }
    Ok(e.policies
        .into_iter()
        .map(|p| SourceFormPolicy {
            node_id: p.node_id,
            source_anchor: p.source_anchor,
            values: match p.values {
                Values::Text {
                    default_value,
                    validation: v,
                } => ExplicitFormPolicy::Text {
                    default_value,
                    validation: FormTextValidation {
                        required: v.required,
                        minimum_characters: v.minimum_characters,
                        maximum_characters: v.maximum_characters,
                        external_validator_sha256: v.external_validator_sha256,
                    },
                },
                Values::Checkbox {
                    default_value,
                    must_be_checked,
                } => ExplicitFormPolicy::Checkbox {
                    default_value,
                    must_be_checked,
                },
                Values::Radio {
                    default_value,
                    group_required,
                } => ExplicitFormPolicy::Radio {
                    default_value,
                    group_required,
                },
                Values::Combo {
                    default_selected_value,
                    validation: v,
                } => ExplicitFormPolicy::Combo {
                    default_selected_value,
                    validation: FormSelectionValidation {
                        required: v.required,
                        external_validator_sha256: v.external_validator_sha256,
                    },
                },
                Values::List {
                    default_selected_value,
                    validation: v,
                } => ExplicitFormPolicy::List {
                    default_selected_value,
                    validation: FormSelectionValidation {
                        required: v.required,
                        external_validator_sha256: v.external_validator_sha256,
                    },
                },
            },
        })
        .collect())
}
