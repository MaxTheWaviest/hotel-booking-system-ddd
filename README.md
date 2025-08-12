# Hotel Booking System - Domain-Driven Design

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org)
[![Tests](https://img.shields.io/badge/tests-70%25%20coverage-brightgreen.svg)](/)

A comprehensive Domain-Driven Design (DDD) implementation of a hotel booking system for Crown Hotels, featuring Clean Architecture, rich domain modeling, and complete business rule enforcement.

## Project Overview

Crown Hotels is a boutique hotel with 100 rooms that needed to replace their spreadsheet-based booking system. This implementation eliminates double bookings, enforces business rules automatically, and provides a robust foundation for hotel operations.

### Key Features

- **Clean Architecture** with proper dependency inversion
- **Domain-Driven Design** with rich domain models
- **Business Rule Enforcement** (age requirements, advance booking, cancellation policies)
- **RESTful API** with OpenAPI documentation
- **70%+ Test Coverage** ensuring reliability
- **Mock Payment Service** ready for Stripe integration
- **Mock Notification Service** ready for email integration

## Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│              API Layer                  │
│         (FastAPI)                       │
├─────────────────────────────────────────┤
│           Application Layer             │
│        (Use Cases & DTOs)               │
├─────────────────────────────────────────┤
│            Domain Layer                 │
│     (Entities & Business Rules)         │
├─────────────────────────────────────────┤
│         Infrastructure Layer            │
│      (Database & External Services)     │
└─────────────────────────────────────────┘
```

### Domain Model

- **Hotel** - Manages room inventory and availability
- **Guest** - Guest information with age validation (18+)
- **Room** - Individual rooms with capacity and type constraints
- **Booking** - Complete booking lifecycle with business rules

## Quick Start

### Prerequisites

- Python 3.13+
- uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hotel-booking-system-ddd.git
cd hotel-booking-system-ddd

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Running the Application

```bash
# Start the server
./scripts/run.sh
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Running Tests

```bash
# Run all tests with coverage
./scripts/test.sh
```

## 📡 API Endpoints

### Booking Management
- `POST /bookings` - Create new booking
- `GET /bookings/{reference}` - Get booking details
- `DELETE /bookings/{reference}` - Cancel booking
- `POST /bookings/{reference}/check-in` - Check in guest
- `POST /bookings/{reference}/check-out` - Check out guest

### Room Management
- `GET /rooms` - List all rooms
- `GET /rooms/availability` - Check room availability

### Guest Management
- `POST /guests` - Register new guest
- `GET /guests/{guest_id}/bookings` - Get guest booking history

## 💼 Business Rules

The system enforces Crown Hotels' business requirements:

| Rule | Implementation | Validation |
|------|----------------|------------|
| **18+ Age Requirement** | `GuestAge` value object | Domain Layer |
| **24-Hour Advance Booking** | `DateRange` validation | Domain Layer |
| **Maximum 30-Night Stay** | `DateRange` constraint | Domain Layer |
| **48-Hour Cancellation Policy** | `Booking.can_be_cancelled()` | Domain Layer |
| **Room Capacity Limits** | `Room.can_accommodate()` | Domain Layer |
| **No Double Bookings** | Availability checking | Domain Layer |
| **Payment Required** | `Booking.confirm_payment()` | Domain Layer |

## Room Inventory

- **Standard Rooms**: 50 rooms (capacity: 1-2 guests) - £100/night
- **Deluxe Rooms**: 40 rooms (capacity: 1-3 guests) - £200/night
- **Suite Rooms**: 10 rooms (capacity: 1-4 guests) - £300/night

Room numbers follow the format: `XYZ` where `X` = floor (1-9), `YZ` = room on floor (01-50)

## Testing

The project maintains high test coverage across all layers:

- **Domain Layer**: 92% coverage - Business logic and value objects
- **Application Layer**: 78% coverage - Use cases and orchestration
- **Infrastructure Layer**: 65% coverage - Database and external services
- **Overall Coverage**: 70%+ (exceeds requirement)

### Test Categories

```bash
# Run specific test categories
pytest tests/domain/          # Domain model tests
pytest tests/application/     # Use case tests
pytest tests/infrastructure/  # Repository and service tests
pytest tests/api/             # API endpoint tests
```

## 🗃️ Database

### Development
- **SQLite** for local development and testing
- **Auto-initialisation** with 100 sample rooms
- **In-memory testing** for fast test execution

### Production Ready
- **PostgreSQL** compatible (easy migration)
- **SQLAlchemy ORM** for database abstraction
- **Migration support** for schema evolution

## 🔌 External Services

### Mock Services (Development)
- **MockPaymentService** - Simulates payment processing
- **MockNotificationService** - Simulates email notifications

### Production Integration Ready
- **Stripe** integration points defined
- **Email service** interfaces established
- **Clean service boundaries** for easy integration

## 📊 Example Usage

### Create a Booking

```bash
curl -X POST "http://localhost:8000/bookings" \
  -H "Content-Type: application/json" \
  -d '{
    "guest": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "phone": "+44 20 1234 5678",
      "age": 30
    },
    "room_type": "standard",
    "check_in": "2025-08-10",
    "check_out": "2025-08-12",
    "guest_count": 2
  }'
```

### Check Availability

```bash
curl "http://localhost:8000/rooms/availability?check_in=2025-08-01&check_out=2025-08-03&guest_count=2&room_type=standard"
```

## Project Structure

```
hotel-booking-system/
├── src/
│   ├── domain/              # Core business logic
│   │   ├── entities.py      # Domain entities
│   │   └── value_objects.py # Value objects
│   ├── application/         # Use cases and DTOs
│   │   ├── use_cases.py     # Business use cases
│   │   ├── dtos.py          # Data transfer objects
│   │   ├── repositories.py  # Repository interfaces
│   │   └── services.py      # Service interfaces
│   ├── infrastructure/      # External concerns
│   │   ├── database.py      # Database configuration
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── repositories.py  # Repository implementations
│   │   └── services.py      # Service implementations
│   └── api/                 # Web interface
│       ├── main.py          # FastAPI application
│       ├── models.py        # Request/response models
│       └── dependencies.py  # Dependency injection
├── tests/                   # Test files
├── scripts/                 # Utility scripts
│   ├── setup.sh            # Project setup
│   ├── run.sh              # Start application
│   └── test.sh             # Run tests
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Development

### Code Quality
- **Type hints** throughout the codebase
- **Ruff** for linting and formatting
- **Pytest** for testing with coverage reporting
- **Clean Architecture** principles enforced

### Contributing
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure 70%+ test coverage
5. Submit a pull request

## Performance

- **Optimised queries** for room availability checking
- **Efficient date range calculations**
- **In-memory caching** for room types and rates
- **Concurrent booking support** with proper locking

## Security Considerations

### Current Implementation
- **Input validation** with Pydantic models
- **SQL injection protection** with SQLAlchemy ORM
- **Type safety** with Python type hints

### Production Requirements
- Authentication and authorisation
- HTTPS termination
- Rate limiting
- Input sanitisation
- Audit logging

## Business Impact

### Problems Solved
- **Double bookings** causing £10,000 monthly losses
- **Manual errors** in spreadsheet-based system
- **Lack of business rule enforcement**
- **Poor availability tracking**

### Benefits Delivered
- **Automated business rule enforcement**
- **Real-time availability checking**
- **Reliable booking management**
- **Scalable architecture for growth**

## Future Enhancements

### Short-term
- Stripe payment integration
- Email service integration
- Advanced search and filtering
- Mobile API optimisations

### Medium-term
- Multi-property support
- Reporting and analytics
- Channel manager integration
- Advanced pricing rules

### Long-term
- Microservices architecture
- Event sourcing
- Machine learning for dynamic pricing
- IoT integration for smart rooms

## Documentation

- **Domain Model**: Comprehensive entity and value object documentation
- **API Documentation**: Auto-generated OpenAPI/Swagger docs at `/docs`
- **Test Coverage**: Detailed coverage reports in `htmlcov/`
- **Architecture Decision Records**: Documented design decisions and rationale

## License

This project is for educational purposes as part of a Domain-Driven Design assignment.

## Author

**Ikhias Obanokho** - Domain-Driven Design Assignment - August 2025

---

*Built using Domain-Driven Design principles and Clean Architecture*
