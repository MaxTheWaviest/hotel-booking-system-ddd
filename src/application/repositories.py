# src/application/repositories.py
"""Repository interfaces (ports) for the application layer."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities import Booking, Guest, Hotel, Room
from src.domain.value_objects import BookingReference, DateRange, RoomNumber, RoomType


class GuestRepository(ABC):
    """Repository interface for Guest entities."""
    
    @abstractmethod
    def save(self, guest: Guest) -> Guest:
        """Save a guest and return the saved entity."""
        pass
    
    @abstractmethod
    def find_by_id(self, guest_id: UUID) -> Optional[Guest]:
        """Find a guest by ID."""
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Guest]:
        """Find a guest by email address."""
        pass


class RoomRepository(ABC):
    """Repository interface for Room entities."""
    
    @abstractmethod
    def save(self, room: Room) -> Room:
        """Save a room and return the saved entity."""
        pass
    
    @abstractmethod
    def find_by_id(self, room_id: UUID) -> Optional[Room]:
        """Find a room by ID."""
        pass
    
    @abstractmethod
    def find_by_number(self, room_number: RoomNumber) -> Optional[Room]:
        """Find a room by room number."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Room]:
        """Find all rooms."""
        pass
    
    @abstractmethod
    def find_by_type(self, room_type: RoomType) -> List[Room]:
        """Find all rooms of a specific type."""
        pass


class BookingRepository(ABC):
    """Repository interface for Booking entities."""
    
    @abstractmethod
    def save(self, booking: Booking) -> Booking:
        """Save a booking and return the saved entity."""
        pass
    
    @abstractmethod
    def find_by_id(self, booking_id: UUID) -> Optional[Booking]:
        """Find a booking by ID."""
        pass
    
    @abstractmethod
    def find_by_reference(self, reference: BookingReference) -> Optional[Booking]:
        """Find a booking by reference number."""
        pass
    
    @abstractmethod
    def find_by_guest_id(self, guest_id: UUID) -> List[Booking]:
        """Find all bookings for a guest."""
        pass
    
    @abstractmethod
    def find_active_bookings_for_room(self, room_id: UUID) -> List[Booking]:
        """Find all active bookings for a specific room."""
        pass
    
    @abstractmethod
    def find_overlapping_bookings(self, room_id: UUID, date_range: DateRange) -> List[Booking]:
        """Find bookings that overlap with the given date range for a room."""
        pass


class HotelRepository(ABC):
    """Repository interface for Hotel aggregate."""
    
    @abstractmethod
    def save(self, hotel: Hotel) -> Hotel:
        """Save a hotel and return the saved entity."""
        pass
    
    @abstractmethod
    def find_by_id(self, hotel_id: UUID) -> Optional[Hotel]:
        """Find a hotel by ID."""
        pass
    
    @abstractmethod
    def get_default_hotel(self) -> Hotel:
        """Get the default hotel (Crown Hotels)."""
        pass
