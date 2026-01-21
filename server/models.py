from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import JSONB, UUID
from database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    
    email = Column(String, primary_key=True, index=True)
    name = Column(String)
    plan = Column(String, default="Free")
    joined_at = Column(Float, default=0.0)
    config = Column(JSONB, default={})
    connected_platforms = Column(ARRAY(String), default=[])
    twitter_oauth = Column(JSONB, default={})
    twitter_quota = Column(JSONB, default={})

class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String, primary_key=True, index=True)
    source_id = Column(String)
    summary = Column(String)
    status = Column(String)
    type = Column(String)
    urgency = Column(String)
    linked_users = Column(ARRAY(String), default=[])
    created_at = Column(Float, default=0.0)
    notified = Column(Boolean, default=False)
    owner = Column(String, ForeignKey("users.email"))

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {"extend_existing": True}
    
    tracking_id = Column(UUID(as_uuid=True), primary_key=True)
    merchant_reference = Column(UUID(as_uuid=True))
    email = Column(String, ForeignKey("users.email"))
    status = Column(String)
    created_at = Column(Float, default=0.0)
