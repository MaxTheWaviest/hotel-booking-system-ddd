#!/bin/bash

# scripts/run.sh
set -e

echo "Starting Hotel Booking System..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/setup.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if main.py exists
if [ ! -f "src/api/main.py" ]; then
    echo "⚠️  API main.py not found. Creating a basic one..."
    cat > src/api/main.py << 'EOF'
"""Main FastAPI application for Crown Hotels."""

from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_cancel_booking_use_case,
    get_check_availability_use_case,
    get_create_booking_use_case,
    get_get_booking_use_case,
    get_room_repository,
    get_guest_repository,
    get_booking_repository,
)
from src.api.models import (
    AvailabilityRequest,
    AvailableRoomResponse,
    BookingHistoryResponse,
    BookingResponse,
    CreateBookingRequest,
    CreateGuestRequest,
    ErrorResponse,
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
from src.domain.value_objects import RoomType
from src.infrastructure.database import get_db

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


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
    )


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Crown Hotels Booking System",
        "status": "running",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "hotel-booking-system"}


# Booking endpoints
@app.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: CreateBookingRequest,
    db: Session = Depends(get_db),
    use_case: CreateBookingUseCase = Depends(get_create_booking_use_case)
):
    """Create a new booking."""
    try:
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
        
        booking_dto = use_case.execute(create_booking_dto)
        db.commit()
        
        return BookingResponse(**booking_dto.__dict__)
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Booking creation failed")


@app.get("/bookings/{reference}", response_model=BookingResponse)
async def get_booking(
    reference: str,
    db: Session = Depends(get_db),
    use_case: GetBookingUseCase = Depends(get_get_booking_use_case)
):
    """Get booking details by reference."""
    try:
        booking_dto = use_case.execute(reference)
        if not booking_dto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {reference} not found"
            )
        
        return BookingResponse(**booking_dto.__dict__)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete("/bookings/{reference}", response_model=SuccessResponse)
async def cancel_booking(
    reference: str,
    db: Session = Depends(get_db),
    use_case: CancelBookingUseCase = Depends(get_cancel_booking_use_case)
):
    """Cancel a booking."""
    try:
        success = use_case.execute(reference)
        db.commit()
        
        if success:
            return SuccessResponse(message=f"Booking {reference} cancelled successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking cancellation failed"
            )
            
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cancellation failed")


# Room endpoints
@app.get("/rooms", response_model=List[RoomResponse])
async def list_rooms(
    room_type: Optional[RoomType] = Query(None, description="Filter by room type"),
    db: Session = Depends(get_db)
):
    """List all rooms, optionally filtered by type."""
    room_repository = get_room_repository(db)
    
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
    check_in: date = Query(..., description="Check-in date"),
    check_out: date = Query(..., description="Check-out date"),
    guest_count: int = Query(..., ge=1, le=4, description="Number of guests"),
    room_type: Optional[RoomType] = Query(None, description="Room type filter"),
    db: Session = Depends(get_db),
    use_case: CheckRoomAvailabilityUseCase = Depends(get_check_availability_use_case)
):
    """Check room availability for given dates."""
    try:
        query_dto = AvailabilityQueryDTO(
            check_in=check_in,
            check_out=check_out,
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Guest endpoints
@app.post("/guests", response_model=GuestResponse, status_code=status.HTTP_201_CREATED)
async def create_guest(
    request: CreateGuestRequest,
    db: Session = Depends(get_db)
):
    """Register a new guest."""
    try:
        guest_repository = get_guest_repository(db)
        
        # Check if guest already exists
        existing_guest = guest_repository.find_by_email(request.email)
        if existing_guest:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Guest with email {request.email} already exists"
            )
        
        # Create new guest
        from src.domain.entities import Guest
        from src.domain.value_objects import GuestAge
        
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Guest creation failed")


@app.get("/guests/{guest_id}/bookings", response_model=BookingHistoryResponse)
async def get_guest_bookings(
    guest_id: str,
    db: Session = Depends(get_db)
):
    """Get guest booking history."""
    try:
        from uuid import UUID
        guest_uuid = UUID(guest_id)
        
        guest_repository = get_guest_repository(db)
        booking_repository = get_booking_repository(db)
        room_repository = get_room_repository(db)
        
        # Find guest
        guest = guest_repository.find_by_id(guest_uuid)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Guest {guest_id} not found"
            )
        
        # Find bookings
        bookings = booking_repository.find_by_guest_id(guest_uuid)
        
        # Convert to DTOs
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Check-in and Check-out endpoints
@app.post("/bookings/{reference}/check-in", response_model=SuccessResponse)
async def check_in_booking(
    reference: str,
    db: Session = Depends(get_db)
):
    """Process guest check-in."""
    try:
        booking_repository = get_booking_repository(db)
        
        from src.domain.value_objects import BookingReference
        booking_ref = BookingReference(reference)
        booking = booking_repository.find_by_reference(booking_ref)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {reference} not found"
            )
        
        booking.check_in()
        booking_repository.save(booking)
        db.commit()
        
        return SuccessResponse(message=f"Guest checked in successfully for booking {reference}")
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Check-in failed")


@app.post("/bookings/{reference}/check-out", response_model=SuccessResponse)
async def check_out_booking(
    reference: str,
    db: Session = Depends(get_db)
):
    """Process guest check-out."""
    try:
        booking_repository = get_booking_repository(db)
        
        from src.domain.value_objects import BookingReference
        booking_ref = BookingReference(reference)
        booking = booking_repository.find_by_reference(booking_ref)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {reference} not found"
            )
        
        booking.check_out()
        booking_repository.save(booking)
        db.commit()
        
        return SuccessResponse(message=f"Guest checked out successfully for booking {reference}")
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Check-out failed")
EOF
    echo "✅ Basic API created"
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "
from src.infrastructure.database import init_db
try:
    init_db()
    print('✅ Database initialized successfully!')
except Exception as e:
    print(f'⚠️  Database initialization error: {e}')
    print('This is normal if database already exists.')
"

# Start FastAPI server
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo "📖 API documentation available at http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"
echo ""
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
