# P09 form-control v0 to v1 migration

There is no accepted v0 form-control schema and no migration switch.

`hwpx-agent.form-control/v1` must be created from a freshly inspected complete control inventory.
Legacy maps, raw XML fragments, command strings, incomplete tab-order lists, unknown native tags and
date-as-edit guesses fail closed. Existing logical/native identity, anchors, common form properties,
kind-specific properties, values/defaults/validation, inherited shape state, protection, resources,
opaque payload and document-flow bindings must be supplied explicitly.

The five qualified native tags are `edit`, `checkBtn`, `radioBtn`, `comboBox`, and `listBox`.
Date remains `unverified_date_control`; migration must not convert it to any exact native tag without
new source and target evidence. Command-button and form-data-binding capabilities remain owned by P11.
