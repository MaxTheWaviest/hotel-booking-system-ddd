# src/infrastructure/models.py
"""SQLAlchemy database models."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean, 
    Column, 
    DateTime, 
    Enum, 
    ForeignKey, 
    Integer, 
    Numeric, 
    String,
    Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.domain.entities import BookingStatus
from src.domain.value_objects import RoomType

Base = declarative_base()


class GuestModel(Base):
    """SQLAlchemy model for Guest entity."""
    __tablename__ = "guests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=False)
    age = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    bookings = relationship("BookingModel", back_populates="guest")


class RoomModel(Base):
    """SQLAlchemy model for Room entity."""
    __tablename__ = "rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    number = Column(String(10), nullable=False, unique=True, index=True)
    room_type = Column(Enum(RoomType), nullable=False, index=True)
    max_capacity = Column(Integer, nullable=False)
    is_available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    bookings = relationship("BookingModel", back_populates="room")


class BookingModel(Base):
    """SQLAlchemy model for Booking entity."""
    __tablename__ = "bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    reference = Column(String(10), nullable=False, unique=True, index=True)
    guest_id = Column(UUID(as_uuid=True), ForeignKey("guests.id"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False, index=True)
    check_in = Column(Date, nullable=False, index=True)
    check_out = Column(Date, nullable=False, index=True)
    guest_count = Column(Integer, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="GBP")
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING, index=True)
    payment_confirmed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    checked_out_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    guest = relationship("GuestModel", back_populates="bookings")
    room = relationship("RoomModel", back_populates="bookings")


class HotelModel(Base):
    """SQLAlchemy model for Hotel entity."""
    __tablename__ = "hotels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
