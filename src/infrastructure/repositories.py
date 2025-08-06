# src/infrastructure/repositories.py
"""Repository implementations using SQLAlchemy."""

from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session

from src.application.repositories import (
    BookingRepository,
    GuestRepository, 
    HotelRepository,
    RoomRepository,
)
from src.domain.entities import Booking, Guest, Hotel, Room, BookingStatus
from src.domain.value_objects import (
    BookingReference,
    DateRange,
    GuestAge,
    GuestCapacity,
    Money,
    RoomNumber,
    RoomType,
)
from src.infrastructure.models import BookingModel, GuestModel, HotelModel, RoomModel


class SqlAlchemyGuestRepository(GuestRepository):
    """SQLAlchemy implementation of GuestRepository."""
    
    def __init__(self, db: Session):
        self._db = db
    
    def save(self, guest: Guest) -> Guest:
        """Save a guest and return the saved entity."""
        # Check if guest already exists
        existing = self._db.query(GuestModel).filter(GuestModel.id == guest.id).first()
        
        if existing:
            # Update existing guest
            existing.first_name = guest.first_name
            existing.last_name = guest.last_name
            existing.email = guest.email
            existing.phone = guest.phone
            existing.age = guest.age.value if guest.age else 0
        else:
            # Create new guest
            guest_model = GuestModel(
                id=guest.id,
                first_name=guest.first_name,
                last_name=guest.last_name,
                email=guest.email,
                phone=guest.phone,
                age=guest.age.value if guest.age else 0,
                created_at=guest.created_at
            )
            self._db.add(guest_model)
        
        self._db.flush()  # Ensure the guest is saved
        return guest
    
    def find_by_id(self, guest_id: UUID) -> Optional[Guest]:
        """Find a guest by ID."""
        guest_model = self._db.query(GuestModel).filter(GuestModel.id == guest_id).first()
        if not guest_model:
            return None
        return self._model_to_entity(guest_model)
    
    def find_by_email(self, email: str) -> Optional[Guest]:
        """Find a guest by email address."""
        guest_model = self._db.query(GuestModel).filter(GuestModel.email == email).first()
        if not guest_model:
            return None
        return self._model_to_entity(guest_model)
    
    def _model_to_entity(self, model: GuestModel) -> Guest:
        """Convert GuestModel to Guest entity."""
        return Guest(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            phone=model.phone,
            age=GuestAge(model.age),
            created_at=model.created_at
        )


class SqlAlchemyRoomRepository(RoomRepository):
    """SQLAlchemy implementation of RoomRepository."""
    
    def __init__(self, db: Session):
        self._db = db
    
    def save(self, room: Room) -> Room:
        """Save a room and return the saved entity."""
        existing = self._db.query(RoomModel).filter(RoomModel.id == room.id).first()
        
        if existing:
            # Update existing room
            existing.number = room.number.value
            existing.room_type = room.room_type
            existing.max_capacity = room.max_capacity.value
            existing.is_available = room.is_available
        else:
            # Create new room
            room_model = RoomModel(
                id=room.id,
                number=room.number.value,
                room_type=room.room_type,
                max_capacity=room.max_capacity.value,
                is_available=room.is_available,
                created_at=room.created_at
            )
            self._db.add(room_model)
        
        self._db.flush()
        return room
    
    def find_by_id(self, room_id: UUID) -> Optional[Room]:
        """Find a room by ID."""
        room_model = self._db.query(RoomModel).filter(RoomModel.id == room_id).first()
        if not room_model:
            return None
        return self._model_to_entity(room_model)
    
    def find_by_number(self, room_number: RoomNumber) -> Optional[Room]:
        """Find a room by room number."""
        room_model = self._db.query(RoomModel).filter(
            RoomModel.number == room_number.value
        ).first()
        if not room_model:
            return None
        return self._model_to_entity(room_model)
    
    def find_all(self) -> List[Room]:
        """Find all rooms."""
        room_models = self._db.query(RoomModel).all()
        return [self._model_to_entity(model) for model in room_models]
    
    def find_by_type(self, room_type: RoomType) -> List[Room]:
        """Find all rooms of a specific type."""
        room_models = self._db.query(RoomModel).filter(
            RoomModel.room_type == room_type
        ).all()
        return [self._model_to_entity(model) for model in room_models]
    
    def _model_to_entity(self, model: RoomModel) -> Room:
        """Convert RoomModel to Room entity."""
        return Room(
            id=model.id,
            number=RoomNumber(model.number),
            room_type=model.room_type,
            max_capacity=GuestCapacity(model.max_capacity),
            is_available=model.is_available,
            created_at=model.created_at
        )


class SqlAlchemyBookingRepository(BookingRepository):
    """SQLAlchemy implementation of BookingRepository."""
    
    def __init__(self, db: Session):
        self._db = db
    
    def save(self, booking: Booking) -> Booking:
        """Save a booking and return the saved entity."""
        existing = self._db.query(BookingModel).filter(BookingModel.id == booking.id).first()
        
        if existing:
            # Update existing booking
            existing.reference = booking.reference.value
            existing.guest_id = booking.guest_id
            existing.room_id = booking.room_id
            existing.check_in = booking.date_range.check_in
            existing.check_out = booking.date_range.check_out
            existing.guest_count = booking.guest_count
            existing.total_amount = booking.total_amount.amount
            existing.currency = booking.total_amount.currency
            existing.status = booking.status
            existing.payment_confirmed = booking.payment_confirmed
            existing.cancelled_at = booking.cancelled_at
            existing.checked_in_at = booking.checked_in_at
            existing.checked_out_at = booking.checked_out_at
        else:
            # Create new booking
            booking_model = BookingModel(
                id=booking.id,
                reference=booking.reference.value,
                guest_id=booking.guest_id,
                room_id=booking.room_id,
                check_in=booking.date_range.check_in,
                check_out=booking.date_range.check_out,
                guest_count=booking.guest_count,
                total_amount=booking.total_amount.amount,
                currency=booking.total_amount.currency,
                status=booking.status,
                payment_confirmed=booking.payment_confirmed,
                created_at=booking.created_at,
                cancelled_at=booking.cancelled_at,
                checked_in_at=booking.checked_in_at,
                checked_out_at=booking.checked_out_at
            )
            self._db.add(booking_model)
        
        self._db.flush()
        return booking
    
    def find_by_id(self, booking_id: UUID) -> Optional[Booking]:
        """Find a booking by ID."""
        booking_model = self._db.query(BookingModel).filter(
            BookingModel.id == booking_id
        ).first()
        if not booking_model:
            return None
        return self._model_to_entity(booking_model)
    
    def find_by_reference(self, reference: BookingReference) -> Optional[Booking]:
        """Find a booking by reference number."""
        booking_model = self._db.query(BookingModel).filter(
            BookingModel.reference == reference.value
        ).first()
        if not booking_model:
            return None
        return self._model_to_entity(booking_model)
    
    def find_by_guest_id(self, guest_id: UUID) -> List[Booking]:
        """Find all bookings for a guest."""
        booking_models = self._db.query(BookingModel).filter(
            BookingModel.guest_id == guest_id
        ).order_by(BookingModel.created_at.desc()).all()
        return [self._model_to_entity(model) for model in booking_models]
    
    def find_active_bookings_for_room(self, room_id: UUID) -> List[Booking]:
        """Find all active bookings for a specific room."""
        booking_models = self._db.query(BookingModel).filter(
            BookingModel.room_id == room_id,
            BookingModel.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN])
        ).all()
        return [self._model_to_entity(model) for model in booking_models]
    
    def find_overlapping_bookings(self, room_id: UUID, date_range: DateRange) -> List[Booking]:
        """Find bookings that overlap with the given date range for a room."""
        booking_models = self._db.query(BookingModel).filter(
            BookingModel.room_id == room_id,
            BookingModel.status.in_([
                BookingStatus.CONFIRMED, 
                BookingStatus.CHECKED_IN,
                BookingStatus.PENDING
            ]),
            BookingModel.check_in < date_range.check_out,
            BookingModel.check_out > date_range.check_in
        ).all()
        return [self._model_to_entity(model) for model in booking_models]
    
    def _model_to_entity(self, model: BookingModel) -> Booking:
        """Convert BookingModel to Booking entity."""
        booking = Booking(
            id=model.id,
            reference=BookingReference(model.reference),
            guest_id=model.guest_id,
            room_id=model.room_id,
            date_range=DateRange(model.check_in, model.check_out),
            guest_count=model.guest_count,
            total_amount=Money(Decimal(str(model.total_amount)), model.currency),
            status=model.status,
            payment_confirmed=model.payment_confirmed,
            created_at=model.created_at,
            cancelled_at=model.cancelled_at,
            checked_in_at=model.checked_in_at,
            checked_out_at=model.checked_out_at
        )
        return booking


class SqlAlchemyHotelRepository(HotelRepository):
    """SQLAlchemy implementation of HotelRepository."""
    
    def __init__(self, db: Session):
        self._db = db
    
    def save(self, hotel: Hotel) -> Hotel:
        """Save a hotel and return the saved entity."""
        existing = self._db.query(HotelModel).filter(HotelModel.id == hotel.id).first()
        
        if existing:
            existing.name = hotel.name
        else:
            hotel_model = HotelModel(
                id=hotel.id,
                name=hotel.name,
                created_at=hotel.created_at
            )
            self._db.add(hotel_model)
        
        self._db.flush()
        return hotel
    
    def find_by_id(self, hotel_id: UUID) -> Optional[Hotel]:
        """Find a hotel by ID."""
        hotel_model = self._db.query(HotelModel).filter(HotelModel.id == hotel_id).first()
        if not hotel_model:
            return None
        return self._model_to_entity(hotel_model)
    
    def get_default_hotel(self) -> Hotel:
        """Get the default hotel (Crown Hotels)."""
        hotel_model = self._db.query(HotelModel).first()
        if not hotel_model:
            # Create default hotel if it doesn't exist
            hotel = Hotel(name="Crown Hotels")
            return self.save(hotel)
        return self._model_to_entity(hotel_model)
    
    def _model_to_entity(self, model: HotelModel) -> Hotel:
        """Convert HotelModel to Hotel entity."""
        return Hotel(
            id=model.id,
            name=model.name,
            created_at=model.created_at
        )

