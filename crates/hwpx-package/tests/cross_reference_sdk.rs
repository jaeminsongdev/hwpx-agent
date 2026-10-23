use hwpx_package::cross_reference_sdk::{
    CROSS_REFERENCE_SDK_COMMAND_MAX_BYTES, SdkCrossReferenceCandidate as Candidate,
    SdkCrossReferenceDisplay as Display, SdkCrossReferenceError as Error,
    SdkCrossReferenceTarget as Target, SdkNoteKind, SdkNoteSourceOrderIndex as Index,
    SdkObjectKind,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

#[test]
fn visually_verified_manual_current_document_examples_match_without_runtime_claims() -> TestResult {
    for (target, display, expected) in [
        (
            Target::Object {
                kind: SdkObjectKind::Table,
                observed_instance_id: 2043988345,
            },
            Display::Page,
            "?#2043988345;0;0;0;0",
        ),
        (
            Target::Note {
                kind: SdkNoteKind::Footnote,
                source_order_index: Index::positive_specimen(1)?,
            },
            Display::ObjectNumber,
            "?#1;3;1;0;0",
        ),
        (
            Target::Bookmark {
                exact_source_name: "책갈피",
            },
            Display::Content,
            "?책갈피;6;2;0;0",
        ),
    ] {
        let candidate = Candidate::build(target, display, false)?;
        assert_eq!(candidate.command_for_discovery(), expected);
        assert!(candidate.requires_native_target_qualification());
    }
    Ok(())
}

#[test]
fn all_fifty_two_admitted_kind_display_hyperlink_combinations_are_closed_and_deterministic()
-> TestResult {
    let targets = [
        Target::Object {
            kind: SdkObjectKind::Table,
            observed_instance_id: 7,
        },
        Target::Object {
            kind: SdkObjectKind::Picture,
            observed_instance_id: 7,
        },
        Target::Object {
            kind: SdkObjectKind::Equation,
            observed_instance_id: 7,
        },
        Target::Note {
            kind: SdkNoteKind::Footnote,
            source_order_index: Index::positive_specimen(7)?,
        },
        Target::Note {
            kind: SdkNoteKind::Endnote,
            source_order_index: Index::positive_specimen(7)?,
        },
        Target::Object {
            kind: SdkObjectKind::Outline,
            observed_instance_id: 7,
        },
        Target::Bookmark {
            exact_source_name: "name",
        },
    ];
    let mut accepted = 0;
    for (kind, target) in targets.into_iter().enumerate() {
        for display in [
            Display::Page,
            Display::ObjectNumber,
            Display::BookmarkName,
            Display::Content,
            Display::RelativePosition,
        ] {
            let valid = match display {
                Display::ObjectNumber => kind != 6,
                Display::BookmarkName => kind == 6,
                Display::Content => kind != 3 && kind != 4,
                _ => true,
            };
            for hyperlink in [false, true] {
                let result = Candidate::build(target, display, hyperlink);
                if !valid {
                    assert!(matches!(result, Err(Error::Display)));
                    continue;
                }
                let candidate = result?;
                let fields: Vec<_> = candidate.command_for_discovery().split(';').collect();
                assert_eq!(fields.len(), 5);
                assert_eq!(fields[1], kind.to_string());
                assert_eq!(
                    fields[2],
                    match display {
                        Display::Page => "0",
                        Display::ObjectNumber | Display::BookmarkName => "1",
                        Display::Content => "2",
                        Display::RelativePosition => "3",
                    }
                );
                assert_eq!(fields[3], u8::from(hyperlink).to_string());
                assert_eq!(fields[4], "0");
                assert_eq!(
                    candidate.command_for_discovery(),
                    Candidate::build(target, display, hyperlink)?.command_for_discovery()
                );
                accepted += 1;
            }
        }
    }
    assert_eq!(accepted, 52);
    Ok(())
}

#[test]
fn unknown_escaping_external_routes_and_control_characters_reject_without_echo() {
    for name in [
        "",
        "#1",
        "a;b",
        "a?b",
        "a\0b",
        "a\nb",
        "a\rb",
        "C:\\private",
        "//server/share",
        "https://example.invalid",
    ] {
        assert!(matches!(
            Candidate::build(
                Target::Bookmark {
                    exact_source_name: name
                },
                Display::Content,
                false
            ),
            Err(Error::BookmarkEncoding)
        ));
    }
    assert!(matches!(
        Candidate::build(
            Target::Object {
                kind: SdkObjectKind::Table,
                observed_instance_id: 0
            },
            Display::Page,
            false
        ),
        Err(Error::Identity)
    ));
    assert_eq!(Index::positive_specimen(0), Err(Error::Identity));
}

#[test]
fn unicode_names_are_preserved_exactly_not_normalized_trimmed_or_case_folded() -> TestResult {
    for name in ["한글 이름", "e\u{301}", "é", "AbC", " name "] {
        assert_eq!(
            Candidate::build(
                Target::Bookmark {
                    exact_source_name: name
                },
                Display::BookmarkName,
                false
            )?
            .command_for_discovery(),
            format!("?{name};6;1;0;0")
        );
    }
    Ok(())
}

#[test]
fn exact_output_budget_and_maximum_positive_object_identity_are_bounded() -> TestResult {
    let name = "x".repeat(CROSS_REFERENCE_SDK_COMMAND_MAX_BYTES - 9);
    assert_eq!(
        Candidate::build(
            Target::Bookmark {
                exact_source_name: &name
            },
            Display::Page,
            true
        )?
        .command_for_discovery()
        .len(),
        CROSS_REFERENCE_SDK_COMMAND_MAX_BYTES
    );
    let oversized = format!("{name}x");
    assert!(matches!(
        Candidate::build(
            Target::Bookmark {
                exact_source_name: &oversized
            },
            Display::Page,
            true
        ),
        Err(Error::Limit)
    ));
    assert_eq!(
        Candidate::build(
            Target::Object {
                kind: SdkObjectKind::Equation,
                observed_instance_id: u32::MAX
            },
            Display::Content,
            true
        )?
        .command_for_discovery(),
        "?#4294967295;2;2;1;0"
    );
    Ok(())
}

#[test]
fn debug_and_errors_do_not_disclose_source_name_instance_index_or_command() -> TestResult {
    let target = Target::Bookmark {
        exact_source_name: "private source name",
    };
    let candidate = Candidate::build(target, Display::Page, false)?;
    for value in [
        format!("{target:?}"),
        format!("{candidate:?}"),
        format!("{:?}", Index::positive_specimen(123456)?),
    ] {
        assert!(!value.contains("private source name"));
        assert!(!value.contains("123456"));
        assert!(!value.contains(candidate.command_for_discovery()));
    }
    Ok(())
}
