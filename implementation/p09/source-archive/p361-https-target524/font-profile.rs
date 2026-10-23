//! Keep the legacy profile unless original font/substitute declarations contain binary edges.
//! The existing explicit v11 union validates those edges; it does not excuse missing targets.
use crate::{IdRuleProfile,document_import::ImportedSourcePackage};

pub(super) fn select(source:&ImportedSourcePackage,legacy:IdRuleProfile)->IdRuleProfile {
    let binary_edges=source.parts().iter().find(|part|part.path().as_str()=="Contents/header.xml")
        .and_then(|part|part.xml()).is_some_and(|xml|xml.elements().iter().any(|node| {
            node.name().namespace()==Some(crate::HANCOM_2020_HEAD_NAMESPACE)
                &&matches!(node.name().local_name(),"font"|"substFont")
                &&node.attributes().iter().any(|attribute|attribute.name().namespace().is_none()
                    &&attribute.name().local_name()=="binaryItemIDRef")
        }));
    if binary_edges {IdRuleProfile::hwpml_2011_scoped_font_v11()}else{legacy}
}
