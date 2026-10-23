"""Closed fresh identity fixture; original PostgreSQL/AEAD campaign and guards only."""
from pathlib import Path
import native_postgres_catalog_storage as original
OWNED=Path('D:/devdata/hwpx-agent-p09-pg18-catalog-identity-450')
OBSERVATION='target/p09-catalog-identity-sql23-observations-450.json'
if __name__=='__main__':raise SystemExit(original.main(identity=True))
