from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.database import Base


class GoogleCredential(Base):
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgreSQLUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    access_token = Column(String(2048), nullable=False)
    refresh_token = Column(String(2048), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
