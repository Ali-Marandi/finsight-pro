"""Locust workload for 50 concurrently active accounting firms.

The workload uses synthetic tax values only. It must never target production
without an approved tenant allowlist and a dedicated load-test environment.
"""

from __future__ import annotations

import itertools
import os
import uuid
from datetime import datetime, timezone

from locust import HttpUser, between, task

FIRM_COUNT = int(os.getenv("FINSIGHT_LOAD_FIRMS", "50"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("FINSIGHT_LOAD_TIMEOUT_SECONDS", "15"))
_user_sequence = itertools.count(1)


class AccountingFirmUser(HttpUser):
    """One simulated accounting firm with a tenant-bound encrypted sync journal."""

    wait_time = between(0.3, 1.2)

    def on_start(self):
        firm_number = (next(_user_sequence) - 1) % FIRM_COUNT + 1
        self.organization_id = f"load-firm-{firm_number:03d}"
        self.cursor = 0
        self.headers = {"X-Organization-ID": self.organization_id}

    @task(6)
    def push_evidence_revision(self):
        event_id = str(uuid.uuid4())
        payload = {
            "document_hash": f"sha256:load-{event_id}",
            "declared_tax": 1000,
            "tax_adjustment": 250,
            "tax_assessed": 1250,
            "review_status": "needs_review",
            "synthetic": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.client.post(
            "/api/v1/cloud-sync/push",
            headers=self.headers,
            json={
                "client_event_id": event_id,
                "entity_type": "tax_audit_evidence",
                "entity_id": f"evidence-{event_id[:12]}",
                "revision": 1,
                "payload": payload,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
            name="Cloud Sync / push encrypted event",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"Unexpected push status: {response.status_code}")
            elif not response.json().get("payload_digest"):
                response.failure("Push response did not include an integrity digest")
            else:
                response.success()

    @task(3)
    def pull_evidence_revisions(self):
        with self.client.get(
            "/api/v1/cloud-sync/pull",
            headers=self.headers,
            params={"after_cursor": self.cursor, "limit": 25},
            timeout=REQUEST_TIMEOUT_SECONDS,
            name="Cloud Sync / pull tenant cursor",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected pull status: {response.status_code}")
                return
            body = response.json()
            if "next_cursor" not in body or "events" not in body:
                response.failure("Pull response contract is incomplete")
                return
            for event in body["events"]:
                if event["payload"].get("synthetic") is not True:
                    response.failure("Tenant received a non-synthetic or unexpected sync event")
                    return
            self.cursor = body["next_cursor"]
            response.success()

    @task(1)
    def check_service_health(self):
        with self.client.get(
            "/api/v1/health",
            timeout=REQUEST_TIMEOUT_SECONDS,
            name="API / health",
            catch_response=True,
        ) as response:
            if response.status_code != 200 or response.json().get("status") != "ok":
                response.failure("Health check did not return an operational API")
            else:
                response.success()
