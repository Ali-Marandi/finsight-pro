"""Integration coverage for encrypted, tenant-isolated Cloud Sync."""

import os
import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).parents[1]
API_ROOT = PROJECT_ROOT / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.models.database import Base, get_db
from app.models.models import SyncEventModel
from app.routers.cloud_sync import router
from app.services.cloud_sync import CloudSyncError, decrypt_payload


class CloudSyncIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.app = FastAPI()
        self.app.include_router(router, prefix="/api/v1/cloud-sync")

        def get_test_db():
            session = self.session_factory()
            try:
                yield session
            finally:
                session.close()

        self.app.dependency_overrides[get_db] = get_test_db
        self.client = TestClient(self.app)
        self.headers = {"X-Organization-ID": "firm-alpha"}

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
        os.environ.pop("FINSIGHT_ENV", None)
        os.environ.pop("FINSIGHT_CLOUD_SYNC_TOKEN", None)

    def push(self, event_id: str = "event-001", organization: str = "firm-alpha"):
        return self.client.post(
            "/api/v1/cloud-sync/push",
            headers={"X-Organization-ID": organization},
            json={
                "client_event_id": event_id,
                "entity_type": "tax_audit_evidence",
                "entity_id": "evidence-2025-001",
                "revision": 1,
                "payload": {
                    "declared_tax": 1000,
                    "tax_adjustment": 250,
                    "tax_assessed": 1250,
                    "source_hash": "sha256:abc123",
                },
            },
        )

    def test_push_encrypts_sensitive_payload_and_retries_idempotently(self):
        first = self.push()
        duplicate = self.push()

        self.assertEqual(first.status_code, 201)
        self.assertTrue(first.json()["inserted"])
        self.assertEqual(duplicate.status_code, 201)
        self.assertFalse(duplicate.json()["inserted"])
        self.assertEqual(first.json()["cursor"], duplicate.json()["cursor"])

        session = self.session_factory()
        stored = session.query(SyncEventModel).one()
        self.assertNotIn("declared_tax", stored.payload_ciphertext)
        self.assertNotIn("1250", stored.payload_ciphertext)
        self.assertEqual(decrypt_payload("firm-alpha", stored.payload_ciphertext)["tax_assessed"], 1250)
        session.close()

    def test_cursor_pull_is_tenant_isolated_and_returns_plaintext_only_after_decryption(self):
        self.push("alpha-event", "firm-alpha")
        self.push("beta-event", "firm-beta")

        alpha = self.client.get("/api/v1/cloud-sync/pull", headers={"X-Organization-ID": "firm-alpha"})
        beta = self.client.get("/api/v1/cloud-sync/pull", headers={"X-Organization-ID": "firm-beta"})

        self.assertEqual(alpha.status_code, 200)
        self.assertEqual(len(alpha.json()["events"]), 1)
        self.assertEqual(alpha.json()["events"][0]["client_event_id"], "alpha-event")
        self.assertEqual(alpha.json()["events"][0]["payload"]["tax_assessed"], 1250)
        self.assertEqual(len(beta.json()["events"]), 1)
        self.assertEqual(beta.json()["events"][0]["client_event_id"], "beta-event")

    def test_ciphertext_cannot_be_verified_by_another_tenant_or_after_tampering(self):
        self.push()
        session = self.session_factory()
        stored = session.query(SyncEventModel).one()
        ciphertext = stored.payload_ciphertext
        session.close()

        with self.assertRaises(CloudSyncError):
            decrypt_payload("firm-beta", ciphertext)
        with self.assertRaises(CloudSyncError):
            decrypt_payload("firm-alpha", ciphertext[:-1] + "A")

    def test_production_mode_requires_configured_token(self):
        os.environ["FINSIGHT_ENV"] = "production"
        os.environ["FINSIGHT_CLOUD_SYNC_TOKEN"] = "test-sync-token"

        rejected = self.push("secure-event")
        accepted = self.client.post(
            "/api/v1/cloud-sync/push",
            headers={"X-Organization-ID": "firm-alpha", "X-Cloud-Sync-Token": "test-sync-token"},
            json={
                "client_event_id": "secure-event",
                "entity_type": "tax_audit_evidence",
                "entity_id": "evidence-2025-002",
                "revision": 1,
                "payload": {"tax_assessed": 1250},
            },
        )

        self.assertEqual(rejected.status_code, 401)
        self.assertEqual(accepted.status_code, 201)


if __name__ == "__main__":
    unittest.main()
