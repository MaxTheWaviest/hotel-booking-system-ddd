# src/domain/entities.py
"""Domain entities for the hotel booking system."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from .value_objects import (
    BookingReference,
    DateRange,
    GuestAge,
    GuestCapacity,
    Money,
    RoomNumber,
    RoomType,
)


class BookingStatus(Enum):
    """Booking status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


@dataclass
class Guest:
    """Guest entity."""
    id: UUID = field(default_factory=uuid4)
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    age: Optional[GuestAge] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        if not self.first_name or not self.first_name.strip():
            raise ValueError("First name is required")
        if not self.last_name or not self.last_name.strip():
            raise ValueError("Last name is required")
        if not self.email or not self.email.strip():
            raise ValueError("Email is required")
        if not self.age:
            raise ValueError("Guest age is required")
    
    @property
    def full_name(self) -> str:
        """Get the guest's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def is_adult(self) -> bool:
        """Check if the guest is an adult (18+)."""
        return self.age is not None and self.age.value >= 18


@dataclass
class Room:
    """Room entity."""
    id: UUID = field(default_factory=uuid4)
    number: RoomNumber = field(default=None)
    room_type: RoomType = field(default=None)
    max_capacity: GuestCapacity = field(default=None)
    is_available: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        if not self.number:
            raise ValueError("Room number is required")
        if not self.room_type:
            raise ValueError("Room type is required")
        if not self.max_capacity:
            self.max_capacity = GuestCapacity.for_room_type(self.room_type)
    
    def can_accommodate(self, guest_count: int) -> bool:
        """Check if the room can accommodate the given number of guests."""
        return guest_count <= self.max_capacity.value
    
    def is_available_for_dates(self, date_range: DateRange, 
                              existing_bookings: List['Booking']) -> bool:
        """Check if the room is available for the given date range."""
        if not self.is_available:
            return False
        
        for booking in existing_bookings:
            if (booking.room_id == self.id and 
                booking.status not in [BookingStatus.CANCELLED, BookingStatus.CHECKED_OUT] and
                booking.date_range.overlaps_with(date_range)):
                return False
        
        return True


@dataclass
class Booking:
    """Booking entity."""
    id: UUID = field(default_factory=uuid4)
    reference: BookingReference = field(default_factory=BookingReference.generate)
    guest_id: UUID = field(default=None)
    room_id: UUID = field(default=None)
    date_range: DateRange = field(default=None)
    guest_count: int = 1
    total_amount: Money = field(default=None)
    status: BookingStatus = BookingStatus.PENDING
    payment_confirmed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    cancelled_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        if not self.guest_id:
            raise ValueError("Guest ID is required")
        if not self.room_id:
            raise ValueError("Room ID is required")
        if not self.date_range:
            raise ValueError("Date range is required")
        if self.guest_count < 1:
            raise ValueError("Guest count must be at least 1")
    
    def calculate_total_amount(self, room_rate: Money) -> Money:
        """Calculate the total amount for this booking."""
        if not self.date_range:
            raise ValueError("Date range is required to calculate total")
        
        nights = self.date_range.nights
        return room_rate * nights
    
    def can_be_cancelled(self) -> bool:
        """Check if the booking can be cancelled (48+ hours before check-in)."""
        if self.status in [BookingStatus.CANCELLED, BookingStatus.CHECKED_OUT]:
            return False
        
        if not self.date_range:
            return False
        
        # 48-hour cancellation policy
        cutoff_time = datetime.combine(self.date_range.check_in, datetime.min.time()) - timedelta(hours=48)
        return datetime.now() < cutoff_time
    
    def cancel(self) -> None:
        """Cancel the booking if allowed."""
        if not self.can_be_cancelled():
            raise ValueError("Booking cannot be cancelled within 48 hours of check-in")
        
        self.status = BookingStatus.CANCELLED
        self.cancelled_at = datetime.now()
    
    def confirm_payment(self) -> None:
        """Confirm payment and update booking status."""
        if self.status != BookingStatus.PENDING:
            raise ValueError("Only pending bookings can have payment confirmed")
        
        self.payment_confirmed = True
        self.status = BookingStatus.CONFIRMED
    
    def check_in(self) -> None:
        """Process guest check-in."""
        if self.status != BookingStatus.CONFIRMED:
            raise ValueError("Only confirmed bookings can be checked in")
        
        # Check if it's the check-in date
        today = date.today()
        if today < self.date_range.check_in:
            raise ValueError("Cannot check in before the check-in date")
        
        self.status = BookingStatus.CHECKED_IN
        self.checked_in_at = datetime.now()
    
    def check_out(self) -> None:
        """Process guest check-out."""
        if self.status != BookingStatus.CHECKED_IN:
            raise ValueError("Only checked-in bookings can be checked out")
        
        self.status = BookingStatus.CHECKED_OUT
        self.checked_out_at = datetime.now()
    
    def is_active(self) -> bool:
        """Check if the booking is currently active."""
        return self.status in [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]


@dataclass
class Hotel:
    """Hotel aggregate root."""
    id: UUID = field(default_factory=uuid4)
    name: str = "Crown Hotels"
    rooms: List[Room] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_room(self, room: Room) -> None:
        """Add a room to the hotel."""
        # Check for duplicate room numbers
        existing_numbers = {r.number.value for r in self.rooms}
        if room.number.value in existing_numbers:
            raise ValueError(f"Room {room.number.value} already exists")
        
        self.rooms.append(room)
    
    def get_room_by_number(self, room_number: RoomNumber) -> Optional[Room]:
        """Get a room by its number."""
        for room in self.rooms:
            if room.number.value == room_number.value:
                return room
        return None
    
    def get_available_rooms(self, date_range: DateRange, guest_count: int,
                           room_type: Optional[RoomType], 
                           existing_bookings: List[Booking]) -> List[Room]:
        """Get available rooms for the given criteria."""
        available_rooms = []
        
        for room in self.rooms:
            # Check room type filter
            if room_type and room.room_type != room_type:
                continue
            
            # Check capacity
            if not room.can_accommodate(guest_count):
                continue
            
            # Check availability for dates
            if room.is_available_for_dates(date_range, existing_bookings):
                available_rooms.append(room)
        
        return available_rooms
    
    def get_rooms_by_type(self, room_type: RoomType) -> List[Room]:
        """Get all rooms of a specific type."""
        return [room for room in self.rooms if room.room_type == room_type]
