//! Authoring admission for the currently imported POINT bookmark target family.
//! Raw SDK discovery remains separate. No block-range or execution authority.
use crate::cross_reference_sdk::SdkCrossReferenceDisplay;
use thiserror::Error;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PointBookmarkAuthoringDisplay {
    Page,
    BookmarkName,
    RelativePosition,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum PointBookmarkDisplayError {
    #[error("POINT_BOOKMARK_CONTENT_REQUIRES_BLOCK_BOOKMARK")]
    ContentRequiresBlockBookmark,
    #[error("POINT_BOOKMARK_AUTHORING_DISPLAY_UNSUPPORTED")]
    Unsupported,
}
impl TryFrom<SdkCrossReferenceDisplay> for PointBookmarkAuthoringDisplay {
    type Error = PointBookmarkDisplayError;
    fn try_from(display: SdkCrossReferenceDisplay) -> Result<Self, Self::Error> {
        // Hancom 2020 help limits Content to block bookmarks. The GUI switches
        // normal bookmarks to BookmarkName; this API must not silently change
        // the requested meaning. No caller-controlled "block" flag is admitted.
        match display {
            SdkCrossReferenceDisplay::Page => Ok(Self::Page),
            SdkCrossReferenceDisplay::BookmarkName => Ok(Self::BookmarkName),
            SdkCrossReferenceDisplay::RelativePosition => Ok(Self::RelativePosition),
            SdkCrossReferenceDisplay::Content => Err(Self::Error::ContentRequiresBlockBookmark),
            SdkCrossReferenceDisplay::ObjectNumber => Err(Self::Error::Unsupported),
        }
    }
}
