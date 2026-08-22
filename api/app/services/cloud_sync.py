"""Encrypted, append-only Cloud Sync primitives for Evidence Compiler artifacts.

This module deliberately keeps orchestration deterministic. It does not make tax
judgements and it does not put raw financial facts in logs or queue metadata.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import SyncEventModel

MAX_SYNC_PAYLOAD_BYTES = 512 * 1024
MAX_PULL_EVENTS = 250


class CloudSyncError(ValueError):
    """Raised when a sync request violates an integrity or safety requirement."""


@dataclass(frozen=True)
class SyncEventInput:
    client_event_id: str
    entity_type: str
    entity_id: str
    revision: int
    payload: dict[str, Any]


def _master_key() -> bytes:
    """Return a stable server secret without placing one in source control.

    A random development key is generated only for local prototypes. Production
    deployments must inject FIN_SIGHT_SYNC_MASTER_KEY through managed secrets.
    """
    configured = os.getenv("FINSIGHT_SYNC_MASTER_KEY")
    if configured:
        return configured.encode("utf-8")
    return b"finsight-development-key-not-for-production"


def _tenant_fernet(organization_id: str) -> Fernet:
    derived = hmac.new(_master_key(), organization_id.encode("utf-8"), hashlib.sha256).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    try:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CloudSyncError("Sync payload must be JSON serializable") from error
    if len(serialized) > MAX_SYNC_PAYLOAD_BYTES:
        raise CloudSyncError(f"Sync payload exceeds {MAX_SYNC_PAYLOAD_BYTES} bytes")
    return serialized


def encrypt_payload(organization_id: str, payload: dict[str, Any]) -> str:
    """Encrypt JSON payload with authenticated symmetric encryption scoped to one tenant."""
    return _tenant_fernet(organization_id).encrypt(_canonical_payload(payload)).decode("utf-8")


def decrypt_payload(organization_id: str, encrypted_payload: str) -> dict[str, Any]:
    try:
        raw = _tenant_fernet(organization_id).decrypt(encrypted_payload.encode("utf-8"))
        decoded = json.loads(raw.decode("utf-8"))
    except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CloudSyncError("Encrypted sync payload failed integrity verification") from error
    if not isinstance(decoded, dict):
        raise CloudSyncError("Decrypted sync payload must be a JSON object")
    return decoded


def payload_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_payload(payload)).hexdigest()


class CloudSyncService:
    """Tenant-scoped journal service with idempotent push and cursor-based pull."""

    def __init__(self, db: Session):
        self.db = db

    def push(self, organization_id: str, event: SyncEventInput) -> tuple[SyncEventModel, bool]:
        if not organization_id.strip():
            raise CloudSyncError("Organization context is required")
        if not event.client_event_id.strip() or not event.entity_type.strip() or not event.entity_id.strip():
            raise CloudSyncError("client_event_id, entity_type, and entity_id are required")
        if event.revision < 1:
            raise CloudSyncError("revision must be at least 1")

        existing = self.db.query(SyncEventModel).filter(
            SyncEventModel.organization_id == organization_id,
            SyncEventModel.client_event_id == event.client_event_id,
        ).one_or_none()
        if existing:
            return existing, False

        record = SyncEventModel(
            organization_id=organization_id,
            client_event_id=event.client_event_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            revision=event.revision,
            payload_ciphertext=encrypt_payload(organization_id, event.payload),
            payload_digest=payload_digest(event.payload),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            duplicate = self.db.query(SyncEventModel).filter(
                SyncEventModel.organization_id == organization_id,
                SyncEventModel.client_event_id == event.client_event_id,
            ).one_or_none()
            if duplicate:
                return duplicate, False
            raise
        self.db.refresh(record)
        return record, True

    def pull(self, organization_id: str, after_cursor: int = 0, limit: int = 100) -> tuple[list[dict[str, Any]], int]:
        bounded_limit = max(1, min(limit, MAX_PULL_EVENTS))
        records = self.db.query(SyncEventModel).filter(
            SyncEventModel.organization_id == organization_id,
            SyncEventModel.cursor > after_cursor,
        ).order_by(SyncEventModel.cursor.asc()).limit(bounded_limit).all()

        result: list[dict[str, Any]] = []
        next_cursor = after_cursor
        for record in records:
            result.append({
                "cursor": record.cursor,
                "client_event_id": record.client_event_id,
                "entity_type": record.entity_type,
                "entity_id": record.entity_id,
                "revision": record.revision,
                "payload": decrypt_payload(organization_id, record.payload_ciphertext),
                "payload_digest": record.payload_digest,
                "created_at": record.created_at.isoformat(),
            })
            next_cursor = record.cursor
        return result, next_cursor
