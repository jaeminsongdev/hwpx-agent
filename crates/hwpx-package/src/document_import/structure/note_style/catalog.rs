//! Closed spellings from the pinned Hancom OWPML model; no case conversion.
use domain_ir::{NoteLineType as L, NoteLineWidth as W, NoteNumberFormat as N};

pub(super) const NUMBERS: &[(N, &str)] = &[
    (N::Digit,"DIGIT"), (N::CircledDigit,"CIRCLED_DIGIT"),
    (N::RomanCapital,"ROMAN_CAPITAL"), (N::RomanSmall,"ROMAN_SMALL"),
    (N::LatinCapital,"LATIN_CAPITAL"), (N::LatinSmall,"LATIN_SMALL"),
    (N::CircledLatinCapital,"CIRCLED_LATIN_CAPITAL"), (N::CircledLatinSmall,"CIRCLED_LATIN_SMALL"),
    (N::HangulSyllable,"HANGUL_SYLLABLE"), (N::CircledHangulSyllable,"CIRCLED_HANGUL_SYLLABLE"),
    (N::HangulJamo,"HANGUL_JAMO"), (N::CircledHangulJamo,"CIRCLED_HANGUL_JAMO"),
    (N::HangulPhonetic,"HANGUL_PHONETIC"), (N::Ideograph,"IDEOGRAPH"),
    (N::CircledIdeograph,"CIRCLED_IDEOGRAPH"), (N::DecagonCircle,"DECAGON_CIRCLE"),
    (N::DecagonCircleHanja,"DECAGON_CIRCLE_HANJA"), (N::Symbol,"SYMBOL"),
    (N::UserChar,"USER_CHAR"), (N::Symbol2,"SYMBOL2"), (N::Image,"IMAGE"), (N::TwoDigit,"2DIGIT"),
];
pub(super) const LINES: &[(L, &str)] = &[
    (L::None,"NONE"), (L::Solid,"SOLID"), (L::Dot,"DOT"), (L::Dash,"DASH"),
    (L::DashDot,"DASH_DOT"), (L::DashDotDot,"DASH_DOT_DOT"), (L::LongDash,"LONG_DASH"),
    (L::Circle,"CIRCLE"), (L::DoubleSlim,"DOUBLE_SLIM"), (L::SlimThick,"SLIM_THICK"),
    (L::ThickSlim,"THICK_SLIM"), (L::SlimThickSlim,"SLIM_THICK_SLIM"),
    (L::Wave,"WAVE"), (L::DoubleWave,"DOUBLEWAVE"), (L::Thick3d,"THICK3D"),
    (L::ThickReverse3d,"THICKREV3D"), (L::ThreeDimensional,"3D"), (L::Reverse3d,"REV3D"),
];
pub(super) const WIDTHS: &[(W, &str)] = &[
    (W::Mm0_1,"0.1 mm"), (W::Mm0_12,"0.12 mm"), (W::Mm0_15,"0.15 mm"),
    (W::Mm0_2,"0.2 mm"), (W::Mm0_25,"0.25 mm"), (W::Mm0_3,"0.3 mm"),
    (W::Mm0_4,"0.4 mm"), (W::Mm0_5,"0.5 mm"), (W::Mm0_6,"0.6 mm"),
    (W::Mm0_7,"0.7 mm"), (W::Mm1_0,"1.0 mm"), (W::Mm1_5,"1.5 mm"),
    (W::Mm2_0,"2.0 mm"), (W::Mm3_0,"3.0 mm"), (W::Mm4_0,"4.0 mm"), (W::Mm5_0,"5.0 mm"),
];
pub(super) fn read<T: Copy>(table: &[(T, &str)], text: &str) -> Option<T> {
    table.iter().find(|(_, spelling)| *spelling == text).map(|(value, _)| *value)
}
pub(super) fn write<T: PartialEq>(table: &[(T, &'static str)], value: T) -> &'static str {
    // All domain variants are covered; unit tests independently check the table.
    table.iter().find(|(item, _)| *item == value).map_or("", |(_, spelling)| *spelling)
}
