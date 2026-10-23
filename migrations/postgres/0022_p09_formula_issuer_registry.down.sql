-- Source only, NOT executed. No forced downgrade, CASCADE or history loss.
BEGIN;
DO $$
BEGIN
    IF current_setting('hwpx_agent.allow_destructive_rollback',true) IS DISTINCT FROM 'on' THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_ROLLBACK_REQUIRES_EXPLICIT_GATE';
    END IF;
    -- FORCE RLS can hide other tenants even from a table owner. Global emptiness needs bypass visibility.
    -- This is an explicit administrator-only downgrade gate, not an application privilege grant.
    IF NOT EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=current_user AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='FORMULA_ISSUER_ROLLBACK_GLOBAL_VISIBILITY_REQUIRED';
    END IF;
    IF EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version>22)
        OR NOT EXISTS(SELECT 1 FROM hwpx_agent.schema_versions WHERE version=22 AND migration_name='p09.formula_issuer_registry_v1') THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='FORMULA_ISSUER_ROLLBACK_REQUIRES_SCHEMA_22';
    END IF;
    -- Hold through COMMIT: no metadata writer may insert between emptiness check and DROP.
    LOCK TABLE hwpx_agent.formula_issuer_trust_versions,hwpx_agent.formula_issuer_trust_revocations,
        hwpx_agent.formula_approval_versions,hwpx_agent.formula_approval_revocations IN ACCESS EXCLUSIVE MODE;
    IF EXISTS(SELECT 1 FROM hwpx_agent.formula_approval_revocations)
        OR EXISTS(SELECT 1 FROM hwpx_agent.formula_approval_versions)
        OR EXISTS(SELECT 1 FROM hwpx_agent.formula_issuer_trust_revocations)
        OR EXISTS(SELECT 1 FROM hwpx_agent.formula_issuer_trust_versions) THEN
        RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='FORMULA_ISSUER_ROLLBACK_REFUSES_DATA_LOSS';
    END IF;
END
$$;
DROP FUNCTION hwpx_agent.revoke_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,uuid,bigint);
DROP FUNCTION hwpx_agent.read_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint);
DROP FUNCTION hwpx_agent.register_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,uuid,bigint,uuid,bigint,uuid,character);
DROP FUNCTION hwpx_agent.revoke_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint);
DROP FUNCTION hwpx_agent.read_formula_issuer_trust_v1(uuid,uuid,character);
DROP FUNCTION hwpx_agent.register_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint,text,bigint,bigint,bigint,uuid,character);
DROP FUNCTION hwpx_agent.require_formula_issuer_artifact_v1(uuid,character,uuid,character,boolean,boolean);
DROP FUNCTION hwpx_agent.require_formula_issuer_owner_v1(uuid,uuid,character);
DROP FUNCTION hwpx_agent.lock_formula_issuer_scope_v1(uuid,uuid,character,boolean);
DROP TABLE hwpx_agent.formula_approval_revocations;
DROP TABLE hwpx_agent.formula_approval_versions;
DROP TABLE hwpx_agent.formula_issuer_trust_revocations;
DROP TABLE hwpx_agent.formula_issuer_trust_versions;
ALTER TABLE hwpx_agent.schema_versions DISABLE TRIGGER schema_versions_immutable;
DELETE FROM hwpx_agent.schema_versions WHERE version=22 AND migration_name='p09.formula_issuer_registry_v1';
ALTER TABLE hwpx_agent.schema_versions ENABLE TRIGGER schema_versions_immutable;
COMMIT;
