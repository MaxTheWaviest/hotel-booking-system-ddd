"""Main FastAPI application for Crown Hotels."""

from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.models import (
    AvailableRoomResponse,
    BookingHistoryResponse,
    BookingResponse,
    CreateBookingRequest,
    CreateGuestRequest,
    GuestResponse,
    RoomResponse,
    SuccessResponse,
)
from src.application.dtos import AvailabilityQueryDTO, CreateBookingDTO, CreateGuestDTO
from src.application.use_cases import (
    CancelBookingUseCase,
    CheckRoomAvailabilityUseCase,
    CreateBookingUseCase,
    GetBookingUseCase,
)
from src.domain.entities import Guest
from src.domain.value_objects import GuestAge, RoomType, BookingReference
from src.infrastructure.database import get_db
from src.infrastructure.repositories import (
    SqlAlchemyBookingRepository,
    SqlAlchemyGuestRepository,
    SqlAlchemyRoomRepository,
)
from src.infrastructure.services import MockNotificationService, MockPaymentService

app = FastAPI(
    title="Crown Hotels Booking System",
    description="A Domain-Driven Design hotel booking system for Crown Hotels",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Validation Error", "detail": str(exc)}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Crown Hotels Booking System",
        "status": "running",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "hotel-booking-system"}


@app.post("/bookings", response_model=BookingResponse, status_code=201)
async def create_booking(
    request: CreateBookingRequest,
    db: Session = Depends(get_db)
):
    """Create a new booking."""
    try:
        # Create use case
        use_case = CreateBookingUseCase(
            guest_repository=SqlAlchemyGuestRepository(db),
            room_repository=SqlAlchemyRoomRepository(db),
            booking_repository=SqlAlchemyBookingRepository(db),
            payment_service=MockPaymentService(),
            notification_service=MockNotificationService(),
        )
        
        # Create DTO
        create_booking_dto = CreateBookingDTO(
            guest=CreateGuestDTO(
                first_name=request.guest.first_name,
                last_name=request.guest.last_name,
                email=request.guest.email,
                phone=request.guest.phone,
                age=request.guest.age
            ),
            room_type=request.room_type,
            check_in=request.check_in,
            check_out=request.check_out,
            guest_count=request.guest_count
        )
        
        # Execute use case
        booking_dto = use_case.execute(create_booking_dto)
        db.commit()
        
        return BookingResponse(**booking_dto.__dict__)
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Booking creation failed")


@app.get("/bookings/{reference}", response_model=BookingResponse)
async def get_booking(
    reference: str,
    db: Session = Depends(get_db)
):
    """Get booking details by reference."""
    try:
        use_case = GetBookingUseCase(
            booking_repository=SqlAlchemyBookingRepository(db),
            room_repository=SqlAlchemyRoomRepository(db),
        )
        
        booking_dto = use_case.execute(reference)
        if not booking_dto:
            raise HTTPException(status_code=404, detail=f"Booking {reference} not found")
        
        return BookingResponse(**booking_dto.__dict__)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/bookings/{reference}", response_model=SuccessResponse)
async def cancel_booking(
    reference: str,
    db: Session = Depends(get_db)
):
    """Cancel a booking."""
    try:
        use_case = CancelBookingUseCase(
            booking_repository=SqlAlchemyBookingRepository(db),
            guest_repository=SqlAlchemyGuestRepository(db),
            payment_service=MockPaymentService(),
            notification_service=MockNotificationService(),
        )
        
        success = use_case.execute(reference)
        db.commit()
        
        return SuccessResponse(message=f"Booking {reference} cancelled successfully")
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Cancellation failed")


@app.get("/rooms", response_model=List[RoomResponse])
async def list_rooms(
    room_type: Optional[RoomType] = Query(None),
    db: Session = Depends(get_db)
):
    """List all rooms."""
    room_repository = SqlAlchemyRoomRepository(db)
    
    if room_type:
        rooms = room_repository.find_by_type(room_type)
    else:
        rooms = room_repository.find_all()
    
    return [
        RoomResponse(
            id=room.id,
            number=room.number.value,
            room_type=room.room_type,
            max_capacity=room.max_capacity.value,
            is_available=room.is_available
        )
        for room in rooms
    ]


@app.get("/rooms/availability", response_model=List[AvailableRoomResponse])
async def check_availability(
    check_in: str = Query(...),
    check_out: str = Query(...),
    guest_count: int = Query(..., ge=1, le=4),
    room_type: Optional[RoomType] = Query(None),
    db: Session = Depends(get_db)
):
    """Check room availability."""
    try:
        from datetime import datetime
        
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
        
        use_case = CheckRoomAvailabilityUseCase(
            room_repository=SqlAlchemyRoomRepository(db),
            booking_repository=SqlAlchemyBookingRepository(db),
        )
        
        query_dto = AvailabilityQueryDTO(
            check_in=check_in_date,
            check_out=check_out_date,
            guest_count=guest_count,
            room_type=room_type
        )
        
        available_rooms = use_case.execute(query_dto)
        
        return [
            AvailableRoomResponse(
                id=room.id,
                number=room.number,
                room_type=room.room_type,
                max_capacity=room.max_capacity,
                price_per_night=room.price_per_night,
                total_price=room.total_price,
                currency=room.currency
            )
            for room in available_rooms
        ]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/guests", response_model=GuestResponse, status_code=201)
async def create_guest(
    request: CreateGuestRequest,
    db: Session = Depends(get_db)
):
    """Register a new guest."""
    try:
        guest_repository = SqlAlchemyGuestRepository(db)
        
        # Check if guest already exists
        existing_guest = guest_repository.find_by_email(request.email)
        if existing_guest:
            raise HTTPException(status_code=409, detail=f"Guest with email {request.email} already exists")
        
        # Create new guest
        guest = Guest(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone=request.phone,
            age=GuestAge(request.age)
        )
        
        saved_guest = guest_repository.save(guest)
        db.commit()
        
        return GuestResponse(
            id=saved_guest.id,
            first_name=saved_guest.first_name,
            last_name=saved_guest.last_name,
            email=saved_guest.email,
            phone=saved_guest.phone,
            age=saved_guest.age.value,
            created_at=saved_guest.created_at
        )
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Guest creation failed")


@app.get("/guests/{guest_id}/bookings", response_model=BookingHistoryResponse)
async def get_guest_bookings(
    guest_id: str,
    db: Session = Depends(get_db)
):
    """Get guest booking history."""
    try:
        from uuid import UUID
        guest_uuid = UUID(guest_id)
        
        guest_repository = SqlAlchemyGuestRepository(db)
        booking_repository = SqlAlchemyBookingRepository(db)
        room_repository = SqlAlchemyRoomRepository(db)
        
        # Find guest
        guest = guest_repository.find_by_id(guest_uuid)
        if not guest:
            raise HTTPException(status_code=404, detail=f"Guest {guest_id} not found")
        
        # Find bookings
        bookings = booking_repository.find_by_guest_id(guest_uuid)
        
        # Convert to responses
        booking_responses = []
        for booking in bookings:
            room = room_repository.find_by_id(booking.room_id)
            if room:
                booking_responses.append(BookingResponse(
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
                    checked_out_at=booking.checked_out_at
                ))
        
        return BookingHistoryResponse(
            guest_id=guest.id,
            guest_name=guest.full_name,
            bookings=booking_responses
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/bookings/{reference}/check-in", response_model=SuccessResponse)
async def check_in_booking(
    reference: str,
    db: Session = Depends(get_db)
):
    """Process guest check-in."""
    try:
        booking_repository = SqlAlchemyBookingRepository(db)
        
        booking_ref = BookingReference(reference)
        booking = booking_repository.find_by_reference(booking_ref)
        
        if not booking:
            raise HTTPException(status_code=404, detail=f"Booking {reference} not found")
        
        booking.check_in()
        booking_repository.save(booking)
        db.commit()
        
        return SuccessResponse(message=f"Guest checked in successfully for booking {reference}")
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Check-in failed")


@app.post("/bookings/{reference}/check-out", response_model=SuccessResponse)
async def check_out_booking(
    reference: str,
    db: Session = Depends(get_db)
):
    """Process guest check-out."""
    try:
        booking_repository = SqlAlchemyBookingRepository(db)
        
        booking_ref = BookingReference(reference)
        booking = booking_repository.find_by_reference(booking_ref)
        
        if not booking:
            raise HTTPException(status_code=404, detail=f"Booking {reference} not found")
        
        booking.check_out()
        booking_repository.save(booking)
        db.commit()
        
        return SuccessResponse(message=f"Guest checked out successfully for booking {reference}")
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Check-out failed")
