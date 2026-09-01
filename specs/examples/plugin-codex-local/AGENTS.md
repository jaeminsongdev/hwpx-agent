# HWPX Agent local instructions

- Read `.hancom/project-state.json`, then reconcile with `project_open` before mutation.
- Use semantic capabilities and OperationPlan; never emit raw HWPX XML or raw HAction.
- Preserve input files and create revisioned outputs.
- Run design/backend tests and report target Hancom validation as pass/fail/unverified.
