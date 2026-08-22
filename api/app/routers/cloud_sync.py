"""Cloud Sync API for encrypted Evidence Compiler journal events."""

from __future__ import annotations

import hmac
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.cloud_sync import CloudSyncError, CloudSyncService, SyncEventInput

router = APIRouter(tags=["cloud-sync"])


class SyncPushRequest(BaseModel):
    client_event_id: str = Field(min_length=1, max_length=128)
    entity_type: str = Field(min_length=1, max_length=64)
    entity_id: str = Field(min_length=1, max_length=128)
    revision: int = Field(ge=1)
    payload: dict[str, Any]


class SyncPullEvent(BaseModel):
    cursor: int
    client_event_id: str
    entity_type: str
    entity_id: str
    revision: int
    payload: dict[str, Any]
    payload_digest: str
    created_at: str


class SyncPullResponse(BaseModel):
    events: list[SyncPullEvent]
    next_cursor: int


def require_organization(
    x_organization_id: Annotated[str | None, Header(alias="X-Organization-ID")] = None,
    x_cloud_sync_token: Annotated[str | None, Header(alias="X-Cloud-Sync-Token")] = None,
) -> str:
    """Resolve tenant context and reject unauthenticated production traffic.

    The desktop prototype permits local development without a token. Production
    requires FINSIGHT_CLOUD_SYNC_TOKEN until this gate is replaced by the
    application identity provider and signed organization claims.
    """
    if not x_organization_id or len(x_organization_id.strip()) > 128:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid X-Organization-ID is required")

    expected_token = os.getenv("FINSIGHT_CLOUD_SYNC_TOKEN")
    production_mode = os.getenv("FINSIGHT_ENV", "development").lower() == "production"
    if production_mode and not expected_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cloud Sync production authentication is not configured")
    if expected_token and not hmac.compare_digest(x_cloud_sync_token or "", expected_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cloud Sync token is invalid")
    return x_organization_id.strip()


@router.post("/push", status_code=status.HTTP_201_CREATED)
def push_event(
    request: SyncPushRequest,
    organization_id: Annotated[str, Depends(require_organization)],
    db: Session = Depends(get_db),
):
    service = CloudSyncService(db)
    try:
        event, inserted = service.push(
            organization_id,
            SyncEventInput(
                client_event_id=request.client_event_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                revision=request.revision,
                payload=request.payload,
            ),
        )
    except CloudSyncError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return {
        "cursor": event.cursor,
        "client_event_id": event.client_event_id,
        "payload_digest": event.payload_digest,
        "inserted": inserted,
    }


@router.get("/pull", response_model=SyncPullResponse)
def pull_events(
    organization_id: Annotated[str, Depends(require_organization)],
    after_cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
):
    try:
        events, next_cursor = CloudSyncService(db).pull(organization_id, after_cursor=after_cursor, limit=limit)
    except CloudSyncError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return {"events": events, "next_cursor": next_cursor}
