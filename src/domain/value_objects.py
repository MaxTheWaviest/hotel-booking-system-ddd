# src/domain/value_objects.py
"""Domain value objects for the hotel booking system."""

import re
import secrets
import string
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Self


class RoomType(Enum):
    """Room types available in the hotel."""
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"


@dataclass(frozen=True)
class Money:
    """Value object representing money amounts."""
    amount: Decimal
    currency: str = "GBP"
    
    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency is required")
    
    def __add__(self, other: Self) -> Self:
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def __mul__(self, multiplier: int) -> Self:
        return Money(self.amount * multiplier, self.currency)


@dataclass(frozen=True)
class RoomNumber:
    """Value object for room numbers with format validation."""
    value: str
    
    def __post_init__(self) -> None:
        if not re.match(r"^[1-9]\d{2}$", self.value):
            raise ValueError("Room number must be 3 digits (e.g., '301')")
        
        floor = int(self.value[0])
        room_on_floor = int(self.value[1:])
        
        if floor < 1 or floor > 9:
            raise ValueError("Floor must be between 1 and 9")
        if room_on_floor < 1 or room_on_floor > 50:
            raise ValueError("Room number on floor must be between 01 and 50")
    
    @property
    def floor(self) -> int:
        """Get the floor number."""
        return int(self.value[0])


@dataclass(frozen=True)
class BookingReference:
    """10-character booking reference."""
    value: str
    
    def __post_init__(self) -> None:
        if len(self.value) != 10:
            raise ValueError("Booking reference must be exactly 10 characters")
        if not self.value.isalnum():
            raise ValueError("Booking reference must contain only alphanumeric characters")
    
    @classmethod
    def generate(cls) -> Self:
        """Generate a new random booking reference."""
        chars = string.ascii_uppercase + string.digits
        reference = ''.join(secrets.choice(chars) for _ in range(10))
        return cls(reference)


@dataclass(frozen=True)
class GuestAge:
    """Value object for guest age with validation."""
    value: int
    
    def __post_init__(self) -> None:
        if self.value < 18:
            raise ValueError("Guest must be at least 18 years old")
        if self.value > 120:
            raise ValueError("Invalid age")


@dataclass(frozen=True)
class DateRange:
    """Value object for date ranges with hotel business rules."""
    check_in: date
    check_out: date
    
    def __post_init__(self) -> None:
        # Validate date range
        if self.check_in >= self.check_out:
            raise ValueError("Check-in date must be before check-out date")
        
        # 24-hour advance booking rule
        tomorrow = (datetime.now().date() + timedelta(days=1))
        if self.check_in < tomorrow:
            raise ValueError("Bookings must be made at least 24 hours in advance")
        
        # Maximum 30-night stay rule
        if self.nights > 30:
            raise ValueError("Maximum stay is 30 nights")
    
    @property
    def nights(self) -> int:
        """Calculate number of nights."""
        return (self.check_out - self.check_in).days
    
    def overlaps_with(self, other: Self) -> bool:
        """Check if this date range overlaps with another."""
        return (self.check_in < other.check_out and 
                self.check_out > other.check_in)


@dataclass(frozen=True)
class GuestCapacity:
    """Value object for room guest capacity."""
    value: int
    
    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError("Guest capacity must be at least 1")
        if self.value > 4:
            raise ValueError("Maximum guest capacity is 4")
    
    @classmethod
    def for_room_type(cls, room_type: RoomType) -> Self:
        """Get maximum capacity for a room type."""
        capacities = {
            RoomType.STANDARD: 2,
            RoomType.DELUXE: 3,
            RoomType.SUITE: 4,
        }
        return cls(capacities[room_type])


@dataclass(frozen=True)
class RoomRate:
    """Value object for room pricing."""
    room_type: RoomType
    price_per_night: Money
    
    @classmethod
    def get_standard_rates(cls) -> dict[RoomType, Self]:
        """Get the standard room rates."""
        return {
            RoomType.STANDARD: cls(RoomType.STANDARD, Money(Decimal("100.00"))),
            RoomType.DELUXE: cls(RoomType.DELUXE, Money(Decimal("200.00"))),
            RoomType.SUITE: cls(RoomType.SUITE, Money(Decimal("300.00"))),
        }
