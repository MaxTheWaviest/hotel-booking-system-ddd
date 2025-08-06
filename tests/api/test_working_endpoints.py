# tests/api/test_working_endpoints.py
"""Working API tests that avoid threading issues."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.api.main import app
from src.domain.entities import Guest, Room, Booking, BookingStatus
from src.domain.value_objects import (
    GuestAge, RoomNumber, RoomType, GuestCapacity, 
    DateRange, Money, BookingReference
)
from src.application.dtos import BookingDTO, AvailableRoomDTO


class TestBasicEndpoints:
    """Test basic endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to Crown Hotels Booking System"
        assert data["status"] == "running"
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAPIWithMocks:
    """Test API endpoints using mocks to avoid database threading issues."""
    
    @patch('src.api.main.get_db')
    @patch('src.api.main.SqlAlchemyRoomRepository')
    def test_list_rooms_success(self, mock_room_repo_class, mock_get_db):
        """Test listing rooms with mocked repository."""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_room_repo = Mock()
        mock_room_repo_class.return_value = mock_room_repo
        
        # Create mock rooms
        mock_room = Room(
            number=RoomNumber("101"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        mock_room_repo.find_all.return_value = [mock_room]
        
        # Test the endpoint
        client = TestClient(app)
        response = client.get("/rooms")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["number"] == "101"
        assert data[0]["room_type"] == "standard"
        assert data[0]["max_capacity"] == 2
    
    @patch('src.api.main.get_db')
    @patch('src.api.main.CheckRoomAvailabilityUseCase')
    def test_check_availability_success(self, mock_use_case_class, mock_get_db):
        """Test room availability check with mocked use case."""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_use_case = Mock()
        mock_use_case_class.return_value = mock_use_case
        
        # Create mock available room
        available_room = AvailableRoomDTO(
            id=uuid4(),
            number="101",
            room_type=RoomType.STANDARD,
            max_capacity=2,
            price_per_night=Decimal("100.00"),
            total_price=Decimal("200.00"),
            currency="GBP"
        )
        mock_use_case.execute.return_value = [available_room]
        
        # Test the endpoint
        client = TestClient(app)
        response = client.get("/rooms/availability?check_in=2025-08-10&check_out=2025-08-12&guest_count=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["number"] == "101"
        assert float(data[0]["price_per_night"]) == 100.0  # Convert to float for comparison
        assert float(data[0]["total_price"]) == 200.0
    
    @patch('src.api.main.get_db')
    @patch('src.api.main.CreateBookingUseCase')
    def test_create_booking_success(self, mock_use_case_class, mock_get_db):
        """Test booking creation with mocked use case."""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.commit = Mock()
        mock_db.rollback = Mock()
        
        mock_use_case = Mock()
        mock_use_case_class.return_value = mock_use_case
        
        # Create mock booking result
        from datetime import datetime
        booking_dto = BookingDTO(
            id=uuid4(),
            reference="ABC1234567",
            guest_id=uuid4(),
            room_id=uuid4(),
            room_number="101",
            room_type=RoomType.STANDARD,
            check_in=date.today() + timedelta(days=2),
            check_out=date.today() + timedelta(days=4),
            guest_count=2,
            total_amount=Decimal("200.00"),
            currency="GBP",
            status=BookingStatus.CONFIRMED,
            payment_confirmed=True,
            created_at=datetime.now()
        )
        mock_use_case.execute.return_value = booking_dto
        
        # Test the endpoint
        client = TestClient(app)
        booking_request = {
            "guest": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+44 20 1234 5678",
                "age": 25
            },
            "room_type": "standard",
            "check_in": "2025-08-10",
            "check_out": "2025-08-12",
            "guest_count": 2
        }
        
        response = client.post("/bookings", json=booking_request)
        
        assert response.status_code == 201
        data = response.json()
        assert data["reference"] == "ABC1234567"
        assert data["room_type"] == "standard"
        assert data["guest_count"] == 2
        assert data["status"] == "confirmed"
        assert data["payment_confirmed"] is True
    
    @patch('src.api.main.get_db')
    @patch('src.api.main.GetBookingUseCase')
    def test_get_booking_success(self, mock_use_case_class, mock_get_db):
        """Test getting a booking with mocked use case."""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_use_case = Mock()
        mock_use_case_class.return_value = mock_use_case
        
        # Create mock booking result
        from datetime import datetime
        booking_dto = BookingDTO(
            id=uuid4(),
            reference="ABC1234567",
            guest_id=uuid4(),
            room_id=uuid4(),
            room_number="101",
            room_type=RoomType.STANDARD,
            check_in=date.today() + timedelta(days=2),
            check_out=date.today() + timedelta(days=4),
            guest_count=2,
            total_amount=Decimal("200.00"),
            currency="GBP",
            status=BookingStatus.CONFIRMED,
            payment_confirmed=True,
            created_at=datetime.now()
        )
        mock_use_case.execute.return_value = booking_dto
        
        # Test the endpoint
        client = TestClient(app)
        response = client.get("/bookings/ABC1234567")
        
        assert response.status_code == 200
        data = response.json()
        assert data["reference"] == "ABC1234567"
        assert data["room_type"] == "standard"
    
    @patch('src.api.main.get_db')
    @patch('src.api.main.GetBookingUseCase')
    def test_get_booking_not_found(self, mock_use_case_class, mock_get_db):
        """Test getting a non-existent booking."""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_use_case = Mock()
        mock_use_case_class.return_value = mock_use_case
        mock_use_case.execute.return_value = None  # Booking not found
        
        # Test the endpoint
        client = TestClient(app)
        response = client.get("/bookings/NOTFOUND12")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @patch('src.api.main.get_db')
    @patch('src.api.main.CancelBookingUseCase')
    def test_cancel_booking_success(self, mock_use_case_class, mock_get_db):
        """Test cancelling a booking with mocked use case."""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.commit = Mock()
        mock_db.rollback = Mock()
        
        mock_use_case = Mock()
        mock_use_case_class.return_value = mock_use_case
        mock_use_case.execute.return_value = True  # Successful cancellation
        
        # Test the endpoint
        client = TestClient(app)
        response = client.delete("/bookings/ABC1234567")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cancelled successfully" in data["message"]
    
    @patch('src.api.main.get_db')
    @patch('src.api.main.SqlAlchemyGuestRepository')
    def test_create_guest_success(self, mock_guest_repo_class, mock_get_db):
        """Test creating a guest with mocked repository."""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.commit = Mock()
        mock_db.rollback = Mock()
        
        mock_guest_repo = Mock()
        mock_guest_repo_class.return_value = mock_guest_repo
        
        # Mock that guest doesn't exist yet
        mock_guest_repo.find_by_email.return_value = None
        
        # Mock saved guest
        mock_guest = Guest(
            first_name="Alice",
            last_name="Smith",
            email="alice.smith@example.com",
            phone="+44 20 9876 5432",
            age=GuestAge(30)
        )
        mock_guest_repo.save.return_value = mock_guest
        
        # Test the endpoint
        client = TestClient(app)
        guest_request = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice.smith@example.com",
            "phone": "+44 20 9876 5432",
            "age": 30
        }
        
        response = client.post("/guests", json=guest_request)
        
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Smith"
        assert data["email"] == "alice.smith@example.com"
        assert data["age"] == 30
    
    def test_invalid_booking_validation(self):
        """Test that invalid booking data returns validation error."""
        client = TestClient(app)
        
        # Invalid booking data (underage guest, invalid dates)
        invalid_booking = {
            "guest": {
                "first_name": "Jane",
                "last_name": "Young",
                "email": "jane.young@example.com",
                "phone": "+44 20 1234 5678",
                "age": 17  # Underage
            },
            "room_type": "standard",
            "check_in": "2025-08-12",
            "check_out": "2025-08-10",  # Check-out before check-in
            "guest_count": 0  # Invalid guest count
        }
        
        response = client.post("/bookings", json=invalid_booking)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_guest_validation(self):
        """Test that invalid guest data returns validation error."""
        client = TestClient(app)
        
        # Invalid guest data
        invalid_guest = {
            "first_name": "",  # Empty name
            "last_name": "Smith",
            "email": "not-an-email",  # Invalid email
            "phone": "+44 20 9876 5432",
            "age": 16  # Underage
        }
        
        response = client.post("/guests", json=invalid_guest)
        assert response.status_code == 422  # Validation error


class TestDomainIntegrationViaAPI:
    """Test that domain logic works through the API layer."""
    
    def test_domain_model_integration(self):
        """Test that the domain model works correctly."""
        # This tests the core business logic that the API uses
        
        # Create a guest
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+44 20 1234 5678",
            age=GuestAge(25)
        )
        
        # Create a room
        room = Room(
            number=RoomNumber("101"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        
        # Create a booking
        date_range = DateRange(
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=4)
        )
        
        booking = Booking(
            guest_id=guest.id,
            room_id=room.id,
            date_range=date_range,
            guest_count=2,
            total_amount=Money(Decimal("200.00"))
        )
        
        # Test business rules
        assert guest.is_adult()
        assert room.can_accommodate(2)
        assert booking.can_be_cancelled()
        assert date_range.nights == 2
        
        # Test booking workflow
        booking.confirm_payment()
        assert booking.payment_confirmed
        assert booking.status == BookingStatus.CONFIRMED
        
        # Test cancellation
        assert booking.can_be_cancelled()  # Should be cancellable
        booking.cancel()
        assert booking.status == BookingStatus.CANCELLED
    
    def test_room_availability_logic(self):
        """Test room availability business logic."""
        room = Room(
            number=RoomNumber("101"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        
        # Test capacity limits
        assert room.can_accommodate(1)
        assert room.can_accommodate(2)
        assert not room.can_accommodate(3)  # Exceeds capacity
        
        # Test date range validation
        future_range = DateRange(
            check_in=date.today() + timedelta(days=2),
            check_out=date.today() + timedelta(days=4)
        )
        
        # With no existing bookings, room should be available
        assert room.is_available_for_dates(future_range, [])
        
        # Create a conflicting booking
        conflicting_booking = Booking(
            guest_id=uuid4(),
            room_id=room.id,
            date_range=future_range,
            guest_count=1,
            total_amount=Money(Decimal("200.00"))
        )
        conflicting_booking.confirm_payment()
        
        # Room should not be available for overlapping dates
        overlapping_range = DateRange(
            check_in=date.today() + timedelta(days=3),
            check_out=date.today() + timedelta(days=5)
        )
        
        assert not room.is_available_for_dates(overlapping_range, [conflicting_booking])
    
    def test_business_rule_validation(self):
        """Test that business rules are enforced."""
        
        # Test age requirement
        with pytest.raises(ValueError, match="at least 18 years old"):
            GuestAge(17)
        
        # Test advance booking requirement
        with pytest.raises(ValueError, match="at least 24 hours in advance"):
            DateRange(
                check_in=date.today(),  # Today should fail
                check_out=date.today() + timedelta(days=1)
            )
        
        # Test maximum stay
        with pytest.raises(ValueError, match="Maximum stay is 30 nights"):
            DateRange(
                check_in=date.today() + timedelta(days=2),
                check_out=date.today() + timedelta(days=33)  # 31 nights
            )
        
        # Test room number format
        with pytest.raises(ValueError, match="Room number must be 3 digits"):
            RoomNumber("1")  # Too short
        
        with pytest.raises(ValueError, match="Room number must be 3 digits"):
            RoomNumber("001")  # Starts with 0
