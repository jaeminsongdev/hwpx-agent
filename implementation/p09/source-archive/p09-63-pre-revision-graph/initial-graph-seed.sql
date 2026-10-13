-- Additional branch in the owned synthetic metadata fixture; no user/product DB.
INSERT INTO hwpx_agent.branches(tenant_id,project_id,branch_id,name,is_default,created_by_subject_sha256)
VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',
'00000000-0000-0000-0000-000000000004','sibling',false,repeat('a',64));
