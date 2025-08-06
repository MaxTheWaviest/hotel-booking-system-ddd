# tests/domain/test_value_objects.py
"""Tests for domain value objects."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from src.domain.value_objects import (
    BookingReference,
    DateRange,
    GuestAge,
    GuestCapacity,
    Money,
    RoomNumber,
    RoomType,
)


class TestMoney:
    """Tests for Money value object."""
    
    def test_valid_money_creation(self):
        money = Money(Decimal("100.00"))
        assert money.amount == Decimal("100.00")
        assert money.currency == "GBP"
    
    def test_negative_amount_raises_error(self):
        with pytest.raises(ValueError, match="Money amount cannot be negative"):
            Money(Decimal("-10.00"))
    
    def test_money_addition(self):
        money1 = Money(Decimal("100.00"))
        money2 = Money(Decimal("50.00"))
        result = money1 + money2
        assert result.amount == Decimal("150.00")
    
    def test_money_multiplication(self):
        money = Money(Decimal("100.00"))
        result = money * 3
        assert result.amount == Decimal("300.00")


class TestRoomNumber:
    """Tests for RoomNumber value object."""
    
    def test_valid_room_number(self):
        room_num = RoomNumber("301")
        assert room_num.value == "301"
        assert room_num.floor == 3
    
    def test_invalid_format_raises_error(self):
        with pytest.raises(ValueError, match="Room number must be 3 digits"):
            RoomNumber("30")
    
    def test_invalid_floor_raises_error(self):
        with pytest.raises(ValueError, match="Room number must be 3 digits"):
            RoomNumber("001")


class TestBookingReference:
    """Tests for BookingReference value object."""
    
    def test_valid_reference(self):
        ref = BookingReference("ABC1234567")
        assert ref.value == "ABC1234567"
    
    def test_invalid_length_raises_error(self):
        with pytest.raises(ValueError, match="must be exactly 10 characters"):
            BookingReference("ABC123")
    
    def test_generate_creates_valid_reference(self):
        ref = BookingReference.generate()
        assert len(ref.value) == 10
        assert ref.value.isalnum()


class TestGuestAge:
    """Tests for GuestAge value object."""
    
    def test_valid_age(self):
        age = GuestAge(25)
        assert age.value == 25
    
    def test_underage_raises_error(self):
        with pytest.raises(ValueError, match="Guest must be at least 18 years old"):
            GuestAge(17)


class TestDateRange:
    """Tests for DateRange value object."""
    
    def test_valid_date_range(self):
        tomorrow = date.today() + timedelta(days=2)
        day_after = tomorrow + timedelta(days=1)
        date_range = DateRange(tomorrow, day_after)
        assert date_range.nights == 1
    
    def test_invalid_date_order_raises_error(self):
        tomorrow = date.today() + timedelta(days=2)
        with pytest.raises(ValueError, match="Check-in date must be before check-out date"):
            DateRange(tomorrow, tomorrow)
    
    def test_24_hour_advance_booking_rule(self):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        with pytest.raises(ValueError, match="at least 24 hours in advance"):
            DateRange(today, tomorrow)
    
    def test_maximum_30_nights_rule(self):
        start_date = date.today() + timedelta(days=2)
        end_date = start_date + timedelta(days=31)
        with pytest.raises(ValueError, match="Maximum stay is 30 nights"):
            DateRange(start_date, end_date)
    
    def test_overlaps_with(self):
        base_start = date.today() + timedelta(days=2)
        range1 = DateRange(base_start, base_start + timedelta(days=3))
        range2 = DateRange(base_start + timedelta(days=1), base_start + timedelta(days=4))
        assert range1.overlaps_with(range2)


class TestGuestCapacity:
    """Tests for GuestCapacity value object."""
    
    def test_valid_capacity(self):
        capacity = GuestCapacity(2)
        assert capacity.value == 2
    
    def test_for_room_type(self):
        standard_capacity = GuestCapacity.for_room_type(RoomType.STANDARD)
        assert standard_capacity.value == 2
        
        suite_capacity = GuestCapacity.for_room_type(RoomType.SUITE)
        assert suite_capacity.value == 4
