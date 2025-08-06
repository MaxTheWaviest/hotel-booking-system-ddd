# src/api/models.py
"""Pydantic models for API requests and responses."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from src.domain.entities import BookingStatus
from src.domain.value_objects import RoomType


class CreateGuestRequest(BaseModel):
    """Request model for creating a guest."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=20)
    age: int = Field(..., ge=18, le=120)


class GuestResponse(BaseModel):
    """Response model for guest information."""
    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    age: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateBookingRequest(BaseModel):
    """Request model for creating a booking."""
    guest: CreateGuestRequest
    room_type: RoomType
    check_in: date
    check_out: date
    guest_count: int = Field(..., ge=1, le=4)
    
    @validator('check_out')
    def check_out_after_check_in(cls, v, values):
        """Validate that check-out is after check-in."""
        if 'check_in' in values and v <= values['check_in']:
            raise ValueError('Check-out date must be after check-in date')
        return v


class BookingResponse(BaseModel):
    """Response model for booking information."""
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
    
    class Config:
        from_attributes = True


class RoomResponse(BaseModel):
    """Response model for room information."""
    id: UUID
    number: str
    room_type: RoomType
    max_capacity: int
    is_available: bool
    
    class Config:
        from_attributes = True


class AvailabilityRequest(BaseModel):
    """Request model for checking room availability."""
    check_in: date
    check_out: date
    guest_count: int = Field(..., ge=1, le=4)
    room_type: Optional[RoomType] = None
    
    @validator('check_out')
    def check_out_after_check_in(cls, v, values):
        """Validate that check-out is after check-in."""
        if 'check_in' in values and v <= values['check_in']:
            raise ValueError('Check-out date must be after check-in date')
        return v


class AvailableRoomResponse(BaseModel):
    """Response model for available room information."""
    id: UUID
    number: str
    room_type: RoomType
    max_capacity: int
    price_per_night: Decimal
    total_price: Decimal
    currency: str
    
    class Config:
        from_attributes = True


class BookingHistoryResponse(BaseModel):
    """Response model for guest booking history."""
    guest_id: UUID
    guest_name: str
    bookings: List[BookingResponse]
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Response model for successful operations."""
    message: str
    success: bool = True
