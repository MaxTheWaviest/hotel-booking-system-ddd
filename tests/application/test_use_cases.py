# tests/application/test_use_cases.py
"""Tests for application use cases."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

from src.domain.entities import Booking, Guest, Room
from src.domain.value_objects import (
    BookingReference,
    DateRange,
    GuestAge,
    GuestCapacity,
    Money,
    RoomNumber,
    RoomType,
)
from src.application.dtos import AvailabilityQueryDTO, CreateBookingDTO, CreateGuestDTO
from src.application.use_cases import (
    CheckRoomAvailabilityUseCase,
    CreateBookingUseCase,
    GetBookingUseCase,
)


class TestCreateBookingUseCase:
    """Tests for CreateBookingUseCase."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.guest_repository = Mock()
        self.room_repository = Mock()
        self.booking_repository = Mock()
        self.payment_service = Mock()
        self.notification_service = Mock()
        
        self.use_case = CreateBookingUseCase(
            self.guest_repository,
            self.room_repository,
            self.booking_repository,
            self.payment_service,
            self.notification_service,
        )
    
    def test_successful_booking_creation(self):
        """Test successful booking creation."""
        # Arrange
        guest_dto = CreateGuestDTO(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+44 20 1234 5678",
            age=25
        )
        
        booking_dto = CreateBookingDTO(
            guest=guest_dto,
            room_type=RoomType.STANDARD,
            check_in=date.today() + timedelta(days=2),
            check_out=date.today() + timedelta(days=4),
            guest_count=2
        )
        
        # Mock guest
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+44 20 1234 5678",
            age=GuestAge(25)
        )
        self.guest_repository.find_by_email.return_value = None
        self.guest_repository.save.return_value = guest
        
        # Mock room
        room = Room(
            number=RoomNumber("301"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        self.room_repository.find_by_type.return_value = [room]
        self.booking_repository.find_overlapping_bookings.return_value = []
        
        # Mock payment
        self.payment_service.process_payment.return_value = True
        
        # Mock booking save
        booking = Booking(
            reference=BookingReference("ABC1234567"),
            guest_id=guest.id,
            room_id=room.id,
            date_range=DateRange(booking_dto.check_in, booking_dto.check_out),
            guest_count=2,
            total_amount=Money(Decimal("200.00"))
        )
        booking.confirm_payment()
        self.booking_repository.save.return_value = booking
        
        # Mock notification
        self.notification_service.send_booking_confirmation.return_value = True
        
        # Act
        result = self.use_case.execute(booking_dto)
        
        # Assert
        assert result.reference == "ABC1234567"
        assert result.guest_id == guest.id
        assert result.room_id == room.id
        assert result.total_amount == Decimal("200.00")
        assert result.payment_confirmed is True
        
        # Verify calls
        self.guest_repository.save.assert_called_once()
        self.booking_repository.save.assert_called_once()
        self.payment_service.process_payment.assert_called_once()
        self.notification_service.send_booking_confirmation.assert_called_once()
    
    def test_no_available_rooms_raises_error(self):
        """Test that no available rooms raises an error."""
        # Arrange
        guest_dto = CreateGuestDTO(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+44 20 1234 5678",
            age=25
        )
        
        booking_dto = CreateBookingDTO(
            guest=guest_dto,
            room_type=RoomType.STANDARD,
            check_in=date.today() + timedelta(days=2),
            check_out=date.today() + timedelta(days=4),
            guest_count=2
        )
        
        # Mock no available rooms
        self.room_repository.find_by_type.return_value = []
        
        # Act & Assert
        with pytest.raises(ValueError, match="No rooms available"):
            self.use_case.execute(booking_dto)


class TestGetBookingUseCase:
    """Tests for GetBookingUseCase."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.booking_repository = Mock()
        self.room_repository = Mock()
        self.use_case = GetBookingUseCase(self.booking_repository, self.room_repository)
    
    def test_get_existing_booking(self):
        """Test retrieving an existing booking."""
        # Arrange
        reference = "ABC1234567"
        booking_ref = BookingReference(reference)
        
        guest_id = uuid4()
        room_id = uuid4()
        
        booking = Booking(
            reference=booking_ref,
            guest_id=guest_id,
            room_id=room_id,
            date_range=DateRange(
                date.today() + timedelta(days=2),
                date.today() + timedelta(days=4)
            ),
            guest_count=2,
            total_amount=Money(Decimal("200.00"))
        )
        
        room = Room(
            id=room_id,
            number=RoomNumber("301"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        
        self.booking_repository.find_by_reference.return_value = booking
        self.room_repository.find_by_id.return_value = room
        
        # Act
        result = self.use_case.execute(reference)
        
        # Assert
        assert result is not None
        assert result.reference == reference
        assert result.room_number == "301"
        assert result.room_type == RoomType.STANDARD
    
    def test_get_nonexistent_booking_returns_none(self):
        """Test retrieving a non-existent booking returns None."""
        # Arrange
        reference = "NOTFOUND12"  # Exactly 10 characters
        self.booking_repository.find_by_reference.return_value = None
        
        # Act
        result = self.use_case.execute(reference)
        
        # Assert
        assert result is None


class TestCheckRoomAvailabilityUseCase:
    """Tests for CheckRoomAvailabilityUseCase."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.room_repository = Mock()
        self.booking_repository = Mock()
        self.use_case = CheckRoomAvailabilityUseCase(
            self.room_repository, 
            self.booking_repository
        )
    
    def test_find_available_rooms(self):
        """Test finding available rooms."""
        # Arrange
        query = AvailabilityQueryDTO(
            check_in=date.today() + timedelta(days=2),
            check_out=date.today() + timedelta(days=4),
            guest_count=2,
            room_type=RoomType.STANDARD
        )
        
        room = Room(
            number=RoomNumber("301"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        
        self.room_repository.find_by_type.return_value = [room]
        self.booking_repository.find_overlapping_bookings.return_value = []
        
        # Act
        result = self.use_case.execute(query)
        
        # Assert
        assert len(result) == 1
        assert result[0].number == "301"
        assert result[0].room_type == RoomType.STANDARD
        assert result[0].price_per_night == Decimal("100.00")
        assert result[0].total_price == Decimal("200.00")  # 2 nights
