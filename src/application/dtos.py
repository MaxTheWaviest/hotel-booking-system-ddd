# src/application/dtos.py
"""Data Transfer Objects for the application layer."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from src.domain.value_objects import RoomType
from src.domain.entities import BookingStatus


@dataclass
class CreateGuestDTO:
    """DTO for creating a new guest."""
    first_name: str
    last_name: str
    email: str
    phone: str
    age: int


@dataclass
class GuestDTO:
    """DTO for guest information."""
    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    age: int
    created_at: datetime


@dataclass
class CreateBookingDTO:
    """DTO for creating a new booking."""
    guest: CreateGuestDTO
    room_type: RoomType
    check_in: date
    check_out: date
    guest_count: int


@dataclass
class BookingDTO:
    """DTO for booking information."""
    id: UUID
    reference: str
    guest_id: UUID
    room_id: UUID
    room_number: str
    room_type: RoomType
    check_in: date
    check_out: date
    guest_count: int
    total_amount: Decimal
    currency: str
    status: BookingStatus
    payment_confirmed: bool
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None


@dataclass
class RoomDTO:
    """DTO for room information."""
    id: UUID
    number: str
    room_type: RoomType
    max_capacity: int
    is_available: bool


@dataclass
class AvailabilityQueryDTO:
    """DTO for room availability queries."""
    check_in: date
    check_out: date
    guest_count: int
    room_type: Optional[RoomType] = None


@dataclass
class AvailableRoomDTO:
    """DTO for available room information."""
    id: UUID
    number: str
    room_type: RoomType
    max_capacity: int
    price_per_night: Decimal
    total_price: Decimal
    currency: str


@dataclass
class PaymentDTO:
    """DTO for payment information."""
    booking_id: UUID
    amount: Decimal
    currency: str
    payment_method: str = "mock"


@dataclass
class BookingHistoryDTO:
    """DTO for guest booking history."""
    guest_id: UUID
    guest_name: str
    bookings: List[BookingDTO]
