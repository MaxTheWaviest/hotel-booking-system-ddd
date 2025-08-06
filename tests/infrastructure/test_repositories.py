# tests/infrastructure/test_repositories.py
"""Tests for infrastructure repositories."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
from src.infrastructure.database import Base
from src.infrastructure.repositories import (
    SqlAlchemyBookingRepository,
    SqlAlchemyGuestRepository,
    SqlAlchemyRoomRepository,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:", 
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()


class TestSqlAlchemyGuestRepository:
    """Tests for SqlAlchemyGuestRepository."""
    
    def test_save_and_find_guest(self, db_session):
        """Test saving and finding a guest."""
        repository = SqlAlchemyGuestRepository(db_session)
        
        # Create a guest
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+44 20 1234 5678",
            age=GuestAge(25)
        )
        
        # Save the guest
        saved_guest = repository.save(guest)
        db_session.commit()
        
        # Find by ID
        found_guest = repository.find_by_id(saved_guest.id)
        assert found_guest is not None
        assert found_guest.first_name == "John"
        assert found_guest.last_name == "Doe"
        assert found_guest.email == "john.doe@example.com"
        assert found_guest.age.value == 25
        
        # Find by email
        found_by_email = repository.find_by_email("john.doe@example.com")
        assert found_by_email is not None
        assert found_by_email.id == guest.id
    
    def test_find_nonexistent_guest_returns_none(self, db_session):
        """Test that finding a non-existent guest returns None."""
        repository = SqlAlchemyGuestRepository(db_session)
        
        from uuid import uuid4
        result = repository.find_by_id(uuid4())
        assert result is None
        
        result = repository.find_by_email("nonexistent@example.com")
        assert result is None


class TestSqlAlchemyRoomRepository:
    """Tests for SqlAlchemyRoomRepository."""
    
    def test_save_and_find_room(self, db_session):
        """Test saving and finding a room."""
        repository = SqlAlchemyRoomRepository(db_session)
        
        # Create a room
        room = Room(
            number=RoomNumber("301"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        
        # Save the room
        saved_room = repository.save(room)
        db_session.commit()
        
        # Find by ID
        found_room = repository.find_by_id(saved_room.id)
        assert found_room is not None
        assert found_room.number.value == "301"
        assert found_room.room_type == RoomType.STANDARD
        assert found_room.max_capacity.value == 2
        
        # Find by number
        found_by_number = repository.find_by_number(RoomNumber("301"))
        assert found_by_number is not None
        assert found_by_number.id == room.id
    
    def test_find_rooms_by_type(self, db_session):
        """Test finding rooms by type."""
        repository = SqlAlchemyRoomRepository(db_session)
        
        # Create rooms of different types
        standard_room = Room(
            number=RoomNumber("101"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        
        deluxe_room = Room(
            number=RoomNumber("201"),
            room_type=RoomType.DELUXE,
            max_capacity=GuestCapacity(3)
        )
        
        # Save rooms
        repository.save(standard_room)
        repository.save(deluxe_room)
        db_session.commit()
        
        # Find standard rooms
        standard_rooms = repository.find_by_type(RoomType.STANDARD)
        assert len(standard_rooms) == 1
        assert standard_rooms[0].room_type == RoomType.STANDARD
        
        # Find deluxe rooms
        deluxe_rooms = repository.find_by_type(RoomType.DELUXE)
        assert len(deluxe_rooms) == 1
        assert deluxe_rooms[0].room_type == RoomType.DELUXE
        
        # Find all rooms
        all_rooms = repository.find_all()
        assert len(all_rooms) == 2


class TestSqlAlchemyBookingRepository:
    """Tests for SqlAlchemyBookingRepository."""
    
    def test_save_and_find_booking(self, db_session):
        """Test saving and finding a booking."""
        # Create repositories
        guest_repo = SqlAlchemyGuestRepository(db_session)
        room_repo = SqlAlchemyRoomRepository(db_session)
        booking_repo = SqlAlchemyBookingRepository(db_session)
        
        # Create and save guest
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+44 20 1234 5678",
            age=GuestAge(25)
        )
        saved_guest = guest_repo.save(guest)
        
        # Create and save room
        room = Room(
            number=RoomNumber("301"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        saved_room = room_repo.save(room)
        
        # Create booking
        date_range = DateRange(
            check_in=date.today() + timedelta(days=2),
            check_out=date.today() + timedelta(days=4)
        )
        
        booking = Booking(
            guest_id=saved_guest.id,
            room_id=saved_room.id,
            date_range=date_range,
            guest_count=2,
            total_amount=Money(Decimal("200.00"))
        )
        
        # Save booking
        saved_booking = booking_repo.save(booking)
        db_session.commit()
        
        # Find by ID
        found_booking = booking_repo.find_by_id(saved_booking.id)
        assert found_booking is not None
        assert found_booking.guest_id == saved_guest.id
        assert found_booking.room_id == saved_room.id
        assert found_booking.guest_count == 2
        assert found_booking.total_amount.amount == Decimal("200.00")
        
        # Find by reference
        found_by_ref = booking_repo.find_by_reference(saved_booking.reference)
        assert found_by_ref is not None
        assert found_by_ref.id == booking.id
    
    def test_find_overlapping_bookings(self, db_session):
        """Test finding overlapping bookings."""
        # Create repositories
        guest_repo = SqlAlchemyGuestRepository(db_session)
        room_repo = SqlAlchemyRoomRepository(db_session)
        booking_repo = SqlAlchemyBookingRepository(db_session)
        
        # Create guest and room
        guest = Guest(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+44 20 1234 5678",
            age=GuestAge(25)
        )
        saved_guest = guest_repo.save(guest)
        
        room = Room(
            number=RoomNumber("301"),
            room_type=RoomType.STANDARD,
            max_capacity=GuestCapacity(2)
        )
        saved_room = room_repo.save(room)
        
        # Create existing booking
        existing_booking = Booking(
            guest_id=saved_guest.id,
            room_id=saved_room.id,
            date_range=DateRange(
                check_in=date.today() + timedelta(days=2),
                check_out=date.today() + timedelta(days=5)
            ),
            guest_count=2,
            total_amount=Money(Decimal("300.00"))
        )
        existing_booking.confirm_payment()
        booking_repo.save(existing_booking)
        db_session.commit()
        
        # Test overlapping date range
        overlapping_range = DateRange(
            check_in=date.today() + timedelta(days=3),
            check_out=date.today() + timedelta(days=6)
        )
        
        overlapping_bookings = booking_repo.find_overlapping_bookings(
            saved_room.id, overlapping_range
        )
        
        assert len(overlapping_bookings) == 1
        assert overlapping_bookings[0].id == existing_booking.id
        
        # Test non-overlapping date range
        non_overlapping_range = DateRange(
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=12)
        )
        
        non_overlapping_bookings = booking_repo.find_overlapping_bookings(
            saved_room.id, non_overlapping_range
        )
        
        assert len(non_overlapping_bookings) == 0
