# src/application/services.py
"""Service interfaces (ports) for external services."""

from abc import ABC, abstractmethod
from src.application.dtos import PaymentDTO


class PaymentService(ABC):
    """Interface for payment processing service."""
    
    @abstractmethod
    def process_payment(self, payment: PaymentDTO) -> bool:
        """Process a payment and return success status."""
        pass
    
    @abstractmethod
    def refund_payment(self, payment: PaymentDTO) -> bool:
        """Process a refund and return success status."""
        pass


class NotificationService(ABC):
    """Interface for notification service."""
    
    @abstractmethod
    def send_booking_confirmation(self, booking_reference: str, guest_email: str) -> bool:
        """Send booking confirmation email."""
        pass
    
    @abstractmethod
    def send_cancellation_confirmation(self, booking_reference: str, guest_email: str) -> bool:
        """Send cancellation confirmation email."""
        pass
