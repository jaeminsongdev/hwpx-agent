# P09 link/reference v1 to v2

- `hwpx-agent.link-reference/v2` replaces v1 for new producers.
- `EditHyperlink` now requires `new_parameters_sha256`; changing a logical target while retaining the
  old native-parameter digest is no longer representable.
- `hangul_2020_https_current_tab_v1` is added as an explicitly qualified semantic binding. Existing
  generic records remain `unverified_field_parameters` and do not gain direct-HWPX support.
- The qualified binding is limited to the discovered HTTPS/current-tab six-parameter tuple. Internal
  bookmarks, mail addresses, managed documents, alternate open modes, arbitrary display ranges and
  display-text mutation do not migrate into this profile.
- No missing digest, binding, target, anchor, native identifier or policy approval is synthesized.
  Such v1 input must be rebuilt from a complete source snapshot or fail closed.
