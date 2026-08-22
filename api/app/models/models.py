from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.models.database import Base
import uuid


class AnalysisModel(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String, nullable=True)
    period = Column(String, nullable=True)
    file_name = Column(String, nullable=False)
    file_hash = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class RatioResultModel(Base):
    __tablename__ = "ratio_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    category = Column(String, nullable=False)
    ratio_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    benchmark = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="good")


class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    format = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    size_bytes = Column(Integer, nullable=True)


class SyncEventModel(Base):
    __tablename__ = "sync_events"
    __table_args__ = (UniqueConstraint("organization_id", "client_event_id", name="uq_sync_events_organization_client_event"),)

    cursor = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(String, nullable=False, index=True)
    client_event_id = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    revision = Column(Integer, nullable=False)
    payload_ciphertext = Column(Text, nullable=False)
    payload_digest = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class SettingsModel(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    ai_config = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LicenseModel(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    license_key = Column(String, nullable=False)
    tier = Column(String, nullable=False, default="free")
    machine_id = Column(String, nullable=True)
    activated_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
