-- P142 disposable owned DB only. Original artifact AEAD/ACL/audit service capabilities.
-- No registry-table/helper, schema-owner, superuser, bypass-RLS or replication privileges.
BEGIN;
SET LOCAL statement_timeout='10s';
CREATE ROLE p142_artifact LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS NOREPLICATION CONNECTION LIMIT 8;
GRANT USAGE ON SCHEMA hwpx_agent TO p142_artifact;
GRANT SELECT ON hwpx_agent.schema_versions TO p142_artifact;
GRANT EXECUTE ON FUNCTION hwpx_agent.current_tenant_id() TO p142_artifact;
GRANT SELECT,INSERT,UPDATE ON hwpx_agent.artifacts TO p142_artifact;
GRANT SELECT,INSERT,UPDATE,DELETE ON hwpx_agent.artifact_acl TO p142_artifact;
GRANT SELECT,INSERT ON hwpx_agent.artifact_service_audit TO p142_artifact;
GRANT USAGE ON SEQUENCE hwpx_agent.artifact_service_audit_event_id_seq TO p142_artifact;
SET CONSTRAINTS ALL IMMEDIATE;
COMMIT;
