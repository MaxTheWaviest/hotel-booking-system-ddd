# tests/api/test_simple_endpoints.py
"""Simplified API tests focusing on core functionality."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import date, timedelta

from src.api.main import app


class TestBasicEndpoints:
    """Test basic endpoints that don't require database."""
    
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


class TestAPIStructure:
    """Test that the API structure is correct."""
    
    def test_openapi_schema_generation(self):
        """Test that OpenAPI schema can be generated."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "paths" in schema
        
        # Check that our expected endpoints are in the schema
        paths = schema["paths"]
        assert "/" in paths
        assert "/health" in paths
        assert "/bookings" in paths
        assert "/rooms" in paths
        assert "/guests" in paths
        
        # Check that POST /bookings exists
        assert "post" in paths["/bookings"]
        
        # Check that GET /rooms exists
        assert "get" in paths["/rooms"]
    
    def test_docs_endpoint_accessible(self):
        """Test that the API docs endpoint is accessible."""
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200
        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")


class TestAPIValidation:
    """Test API input validation without database operations."""
    
    def test_booking_validation_errors(self):
        """Test that booking creation validates input properly."""
        client = TestClient(app)
        
        # Test with invalid data (missing required fields)
        invalid_booking = {
            "guest": {
                "first_name": "",  # Empty first name should fail
                "last_name": "Doe",
                "email": "invalid-email",  # Invalid email
                "phone": "+44 20 1234 5678",
                "age": 17  # Underage should fail
            },
            "room_type": "standard",
            "check_in": "2025-08-01",
            "check_out": "2025-08-01",  # Same as check-in should fail
            "guest_count": 0  # Invalid guest count
        }
        
        response = client.post("/bookings", json=invalid_booking)
        # Should return a validation error (422)
        assert response.status_code == 422
    
    def test_guest_validation_errors(self):
        """Test that guest creation validates input properly."""
        client = TestClient(app)
        
        # Test with invalid guest data
        invalid_guest = {
            "first_name": "",  # Empty name
            "last_name": "Smith",
            "email": "not-an-email",  # Invalid email
            "phone": "+44 20 9876 5432",
            "age": 15  # Underage
        }
        
        response = client.post("/guests", json=invalid_guest)
        assert response.status_code == 422


# Simple integration test that demonstrates the system works
def test_system_integration_without_database():
    """Test that shows the system components work together."""
    from src.domain.entities import Guest, Room, Booking
    from src.domain.value_objects import (
        GuestAge, RoomNumber, RoomType, GuestCapacity, 
        DateRange, Money, BookingReference
    )
    from decimal import Decimal
    
    # Test domain model integration
    guest = Guest(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+44 20 1234 5678",
        age=GuestAge(25)
    )
    
    room = Room(
        number=RoomNumber("101"),
        room_type=RoomType.STANDARD,
        max_capacity=GuestCapacity(2)
    )
    
    date_range = DateRange(
        check_in=date.today() + timedelta(days=5),  # Far enough for cancellation
        check_out=date.today() + timedelta(days=7)
    )
    
    booking = Booking(
        guest_id=guest.id,
        room_id=room.id,
        date_range=date_range,
        guest_count=2,
        total_amount=Money(Decimal("200.00"))
    )
    
    # Test that business logic works
    assert guest.is_adult()
    assert room.can_accommodate(2)
    assert booking.can_be_cancelled()  # Should be true for future bookings
    
    # Test booking confirmation
    booking.confirm_payment()
    assert booking.payment_confirmed
    assert booking.status.value == "confirmed"
