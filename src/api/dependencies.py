# src/api/dependencies.py
"""Dependency injection for API endpoints."""

from functools import lru_cache
from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.repositories import (
    BookingRepository,
    GuestRepository,
    HotelRepository,
    RoomRepository,
)
from src.application.services import NotificationService, PaymentService
from src.application.use_cases import (
    CancelBookingUseCase,
    CheckRoomAvailabilityUseCase,
    CreateBookingUseCase,
    GetBookingUseCase,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories import (
    SqlAlchemyBookingRepository,
    SqlAlchemyGuestRepository,
    SqlAlchemyHotelRepository,
    SqlAlchemyRoomRepository,
)
from src.infrastructure.services import MockNotificationService, MockPaymentService


# Service singletons
@lru_cache()
def get_payment_service() -> PaymentService:
    """Get payment service instance."""
    return MockPaymentService()


@lru_cache()
def get_notification_service() -> NotificationService:
    """Get notification service instance."""
    return MockNotificationService()


# Repository factories - these need to be functions that FastAPI can call
def get_guest_repository(db: Session = Depends(get_db)) -> GuestRepository:
    """Get guest repository instance."""
    return SqlAlchemyGuestRepository(db)


def get_room_repository(db: Session = Depends(get_db)) -> RoomRepository:
    """Get room repository instance."""
    return SqlAlchemyRoomRepository(db)


def get_booking_repository(db: Session = Depends(get_db)) -> BookingRepository:
    """Get booking repository instance."""
    return SqlAlchemyBookingRepository(db)


def get_hotel_repository(db: Session = Depends(get_db)) -> HotelRepository:
    """Get hotel repository instance."""
    return SqlAlchemyHotelRepository(db)


# Use case factories - these also need to be dependency functions
def get_create_booking_use_case(
    db: Session = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
    notification_service: NotificationService = Depends(get_notification_service)
) -> CreateBookingUseCase:
    """Get create booking use case instance."""
    return CreateBookingUseCase(
        guest_repository=SqlAlchemyGuestRepository(db),
        room_repository=SqlAlchemyRoomRepository(db),
        booking_repository=SqlAlchemyBookingRepository(db),
        payment_service=payment_service,
        notification_service=notification_service,
    )


def get_get_booking_use_case(db: Session = Depends(get_db)) -> GetBookingUseCase:
    """Get booking retrieval use case instance."""
    return GetBookingUseCase(
        booking_repository=SqlAlchemyBookingRepository(db),
        room_repository=SqlAlchemyRoomRepository(db),
    )


def get_cancel_booking_use_case(
    db: Session = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
    notification_service: NotificationService = Depends(get_notification_service)
) -> CancelBookingUseCase:
    """Get cancel booking use case instance."""
    return CancelBookingUseCase(
        booking_repository=SqlAlchemyBookingRepository(db),
        guest_repository=SqlAlchemyGuestRepository(db),
        payment_service=payment_service,
        notification_service=notification_service,
    )


def get_check_availability_use_case(db: Session = Depends(get_db)) -> CheckRoomAvailabilityUseCase:
    """Get room availability check use case instance."""
    return CheckRoomAvailabilityUseCase(
        room_repository=SqlAlchemyRoomRepository(db),
        booking_repository=SqlAlchemyBookingRepository(db),
    )
