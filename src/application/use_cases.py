# src/application/use_cases.py
"""Use cases for the hotel booking system."""

from typing import List, Optional
from uuid import UUID

from src.domain.entities import Booking, Guest, Room
from src.domain.value_objects import (
    BookingReference,
    DateRange,
    GuestAge,
    Money,
    RoomRate,
    RoomNumber,
)
from src.application.dtos import (
    AvailabilityQueryDTO,
    AvailableRoomDTO,
    BookingDTO,
    BookingHistoryDTO,
    CreateBookingDTO,
    CreateGuestDTO,
    GuestDTO,
    PaymentDTO,
    RoomDTO,
)
from src.application.repositories import BookingRepository, GuestRepository, RoomRepository
from src.application.services import PaymentService, NotificationService


class CreateBookingUseCase:
    """Use case for creating a new booking."""
    
    def __init__(
        self,
        guest_repository: GuestRepository,
        room_repository: RoomRepository,
        booking_repository: BookingRepository,
        payment_service: PaymentService,
        notification_service: NotificationService,
    ):
        self._guest_repository = guest_repository
        self._room_repository = room_repository
        self._booking_repository = booking_repository
        self._payment_service = payment_service
        self._notification_service = notification_service
    
    def execute(self, create_booking_dto: CreateBookingDTO) -> BookingDTO:
        """Execute the create booking use case."""
        # 1. Create or find guest
        guest = self._create_or_find_guest(create_booking_dto.guest)
        
        # 2. Create date range and validate
        date_range = DateRange(
            check_in=create_booking_dto.check_in,
            check_out=create_booking_dto.check_out
        )
        
        # 3. Find available room
        available_rooms = self._find_available_rooms(
            create_booking_dto.room_type,
            date_range,
            create_booking_dto.guest_count
        )
        
        if not available_rooms:
            raise ValueError("No rooms available for the requested dates and criteria")
        
        # Select the first available room
        room = available_rooms[0]
        
        # 4. Calculate total amount
        room_rates = RoomRate.get_standard_rates()
        room_rate = room_rates[room.room_type]
        total_amount = room_rate.price_per_night * date_range.nights
        
        # 5. Create booking
        booking = Booking(
            guest_id=guest.id,
            room_id=room.id,
            date_range=date_range,
            guest_count=create_booking_dto.guest_count,
            total_amount=total_amount,
        )
        
        # 6. Process payment
        payment_dto = PaymentDTO(
            booking_id=booking.id,
            amount=total_amount.amount,
            currency=total_amount.currency,
        )
        
        if not self._payment_service.process_payment(payment_dto):
            raise ValueError("Payment processing failed")
        
        # 7. Confirm payment and save booking
        booking.confirm_payment()
        saved_booking = self._booking_repository.save(booking)
        
        # 8. Send confirmation
        self._notification_service.send_booking_confirmation(
            booking_reference=saved_booking.reference.value,
            guest_email=guest.email
        )
        
        # 9. Return booking DTO
        return self._booking_to_dto(saved_booking, room)
    
    def _create_or_find_guest(self, guest_dto: CreateGuestDTO) -> Guest:
        """Create a new guest or return existing one by email."""
        existing_guest = self._guest_repository.find_by_email(guest_dto.email)
        if existing_guest:
            return existing_guest
        
        guest = Guest(
            first_name=guest_dto.first_name,
            last_name=guest_dto.last_name,
            email=guest_dto.email,
            phone=guest_dto.phone,
            age=GuestAge(guest_dto.age),
        )
        
        return self._guest_repository.save(guest)
    
    def _find_available_rooms(self, room_type, date_range, guest_count) -> List[Room]:
        """Find available rooms matching criteria."""
        rooms = self._room_repository.find_by_type(room_type)
        available_rooms = []
        
        for room in rooms:
            if not room.can_accommodate(guest_count):
                continue
            
            overlapping_bookings = self._booking_repository.find_overlapping_bookings(
                room.id, date_range
            )
            
            if room.is_available_for_dates(date_range, overlapping_bookings):
                available_rooms.append(room)
        
        return available_rooms
    
    def _booking_to_dto(self, booking: Booking, room: Room) -> BookingDTO:
        """Convert booking entity to DTO."""
        return BookingDTO(
            id=booking.id,
            reference=booking.reference.value,
            guest_id=booking.guest_id,
            room_id=booking.room_id,
            room_number=room.number.value,
            room_type=room.room_type,
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
            checked_out_at=booking.checked_out_at,
        )


class GetBookingUseCase:
    """Use case for retrieving a booking by reference."""
    
    def __init__(self, booking_repository: BookingRepository, room_repository: RoomRepository):
        self._booking_repository = booking_repository
        self._room_repository = room_repository
    
    def execute(self, reference: str) -> Optional[BookingDTO]:
        """Execute the get booking use case."""
        booking_ref = BookingReference(reference)
        booking = self._booking_repository.find_by_reference(booking_ref)
        
        if not booking:
            return None
        
        room = self._room_repository.find_by_id(booking.room_id)
        if not room:
            raise ValueError(f"Room not found for booking {reference}")
        
        return self._booking_to_dto(booking, room)
    
    def _booking_to_dto(self, booking: Booking, room: Room) -> BookingDTO:
        """Convert booking entity to DTO."""
        return BookingDTO(
            id=booking.id,
            reference=booking.reference.value,
            guest_id=booking.guest_id,
            room_id=booking.room_id,
            room_number=room.number.value,
            room_type=room.room_type,
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
            checked_out_at=booking.checked_out_at,
        )


class CancelBookingUseCase:
    """Use case for cancelling a booking."""
    
    def __init__(
        self,
        booking_repository: BookingRepository,
        guest_repository: GuestRepository,
        payment_service: PaymentService,
        notification_service: NotificationService,
    ):
        self._booking_repository = booking_repository
        self._guest_repository = guest_repository
        self._payment_service = payment_service
        self._notification_service = notification_service
    
    def execute(self, reference: str) -> bool:
        """Execute the cancel booking use case."""
        booking_ref = BookingReference(reference)
        booking = self._booking_repository.find_by_reference(booking_ref)
        
        if not booking:
            raise ValueError(f"Booking {reference} not found")
        
        # Check if cancellation is allowed
        if not booking.can_be_cancelled():
            raise ValueError("Booking cannot be cancelled within 48 hours of check-in")
        
        # Cancel the booking
        booking.cancel()
        self._booking_repository.save(booking)
        
        # Process refund
        if booking.payment_confirmed:
            payment_dto = PaymentDTO(
                booking_id=booking.id,
                amount=booking.total_amount.amount,
                currency=booking.total_amount.currency,
            )
            self._payment_service.refund_payment(payment_dto)
        
        # Send cancellation confirmation
        guest = self._guest_repository.find_by_id(booking.guest_id)
        if guest:
            self._notification_service.send_cancellation_confirmation(
                booking_reference=reference,
                guest_email=guest.email
            )
        
        return True


class CheckRoomAvailabilityUseCase:
    """Use case for checking room availability."""
    
    def __init__(self, room_repository: RoomRepository, booking_repository: BookingRepository):
        self._room_repository = room_repository
        self._booking_repository = booking_repository
    
    def execute(self, query: AvailabilityQueryDTO) -> List[AvailableRoomDTO]:
        """Execute the room availability check use case."""
        date_range = DateRange(check_in=query.check_in, check_out=query.check_out)
        
        # Get rooms to check
        if query.room_type:
            rooms = self._room_repository.find_by_type(query.room_type)
        else:
            rooms = self._room_repository.find_all()
        
        available_rooms = []
        room_rates = RoomRate.get_standard_rates()
        
        for room in rooms:
            # Check capacity
            if not room.can_accommodate(query.guest_count):
                continue
            
            # Check availability
            overlapping_bookings = self._booking_repository.find_overlapping_bookings(
                room.id, date_range
            )
            
            if room.is_available_for_dates(date_range, overlapping_bookings):
                room_rate = room_rates[room.room_type]
                total_price = room_rate.price_per_night * date_range.nights
                
                available_rooms.append(AvailableRoomDTO(
                    id=room.id,
                    number=room.number.value,
                    room_type=room.room_type,
                    max_capacity=room.max_capacity.value,
                    price_per_night=room_rate.price_per_night.amount,
                    total_price=total_price.amount,
                    currency=total_price.currency,
                ))
        
        return available_rooms
