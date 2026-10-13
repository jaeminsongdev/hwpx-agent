-- Additional branch in the owned synthetic metadata fixture; no user/product DB.
INSERT INTO hwpx_agent.branches(tenant_id,project_id,branch_id,name,is_default,created_by_subject_sha256)
VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',
'00000000-0000-0000-0000-000000000004','sibling',false,repeat('a',64));

-- Each genuine request has a different transaction receipt; original unique indexes remain.
WITH seed(base,sha) AS (VALUES
('40', '32ebb1abcc1c601ceb9c4e3c4faba0caa5b85bb98c4f1e6612c40faa528a91c9'),
('50', 'd4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35'),
('60', 'dabd3aff769f07eb2965401eb029974ebba3407afd02b26ddb564ea5f8efae72'),
('70', 'f67ab10ad4e4c53121b6a5fe4da9c10ddee905b978d3788d2723d7bfacbe28a9'),
('80', '5c62e091b8c0565f1bafad0dad5934276143ae2ccef7a5381e8ada5b1a8d26d2'),
('90', 'bbeebd879e1dff6918546dc0c179fdde505f2a21591c9a9c96e36b054ec5af83')
)
INSERT INTO hwpx_agent.artifacts(tenant_id,artifact_id,content_sha256,size_bytes,media_type,artifact_kind,
storage_state,encryption_key_ref,verified_at,service_metadata_version,filename,object_key,encryption_algorithm,
encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,scanner_engine_ref,scanner_signature_version,authorization_generation)
SELECT tenant_id,('00000000-0000-0000-0000-'||lpad(to_hex(base::integer+6),12,'0'))::uuid,
sha,size_bytes,media_type,artifact_kind,storage_state,encryption_key_ref,transaction_timestamp(),service_metadata_version,
filename,'artifacts/v1/00000000000000000000000000000001/receipt/available/'||sha||'.aes256gcm',
encryption_algorithm,encryption_nonce,aad_sha256,ciphertext_sha256,validation_state,
scanner_engine_ref,scanner_signature_version,authorization_generation
FROM hwpx_agent.artifacts CROSS JOIN seed
WHERE tenant_id='00000000-0000-0000-0000-000000000001' AND artifact_id='00000000-0000-0000-0000-00000000000f';
INSERT INTO hwpx_agent.artifact_acl(tenant_id,artifact_id,subject_sha256,can_read,can_manage)
SELECT tenant_id,artifact_id,repeat('a',64),true,true FROM hwpx_agent.artifacts
WHERE tenant_id='00000000-0000-0000-0000-000000000001'
AND artifact_id IN ('00000000-0000-0000-0000-00000000002e','00000000-0000-0000-0000-000000000038',
'00000000-0000-0000-0000-000000000042','00000000-0000-0000-0000-00000000004c',
'00000000-0000-0000-0000-000000000056','00000000-0000-0000-0000-000000000060');
