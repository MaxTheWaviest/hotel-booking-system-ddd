# src/infrastructure/services.py
"""Mock implementations of external services."""

import logging
from typing import Dict, Any
from decimal import Decimal

from src.application.dtos import PaymentDTO
from src.application.services import PaymentService, NotificationService

logger = logging.getLogger(__name__)


class MockPaymentService(PaymentService):
    """Mock payment service that simulates payment processing."""
    
    def __init__(self):
        self._processed_payments: Dict[str, Dict[str, Any]] = {}
        self._refunded_payments: Dict[str, Dict[str, Any]] = {}
    
    def process_payment(self, payment: PaymentDTO) -> bool:
        """Process a payment and return success status."""
        logger.info(f"Processing payment for booking {payment.booking_id}: "
                   f"{payment.amount} {payment.currency}")
        
        # Simulate payment validation
        if payment.amount <= 0:
            logger.error(f"Invalid payment amount: {payment.amount}")
            return False
        
        if payment.amount > Decimal("10000.00"):
            logger.error(f"Payment amount too large: {payment.amount}")
            return False
        
        # Simulate successful payment processing
        payment_record = {
            "booking_id": str(payment.booking_id),
            "amount": float(payment.amount),
            "currency": payment.currency,
            "payment_method": payment.payment_method,
            "status": "completed",
            "transaction_id": f"mock_txn_{payment.booking_id}"
        }
        
        self._processed_payments[str(payment.booking_id)] = payment_record
        
        logger.info(f"Payment processed successfully for booking {payment.booking_id}")
        return True
    
    def refund_payment(self, payment: PaymentDTO) -> bool:
        """Process a refund and return success status."""
        logger.info(f"Processing refund for booking {payment.booking_id}: "
                   f"{payment.amount} {payment.currency}")
        
        booking_id = str(payment.booking_id)
        
        # Check if original payment exists
        if booking_id not in self._processed_payments:
            logger.error(f"No original payment found for booking {booking_id}")
            return False
        
        original_payment = self._processed_payments[booking_id]
        
        # Validate refund amount
        if payment.amount > Decimal(str(original_payment["amount"])):
            logger.error(f"Refund amount {payment.amount} exceeds original payment "
                        f"{original_payment['amount']}")
            return False
        
        # Process refund
        refund_record = {
            "booking_id": booking_id,
            "amount": float(payment.amount),
            "currency": payment.currency,
            "original_transaction_id": original_payment["transaction_id"],
            "refund_transaction_id": f"refund_txn_{payment.booking_id}",
            "status": "completed"
        }
        
        self._refunded_payments[booking_id] = refund_record
        
        logger.info(f"Refund processed successfully for booking {payment.booking_id}")
        return True
    
    def get_payment_status(self, booking_id: str) -> Dict[str, Any]:
        """Get payment status for a booking (utility method for testing)."""
        return self._processed_payments.get(booking_id, {})
    
    def get_refund_status(self, booking_id: str) -> Dict[str, Any]:
        """Get refund status for a booking (utility method for testing)."""
        return self._refunded_payments.get(booking_id, {})


class MockNotificationService(NotificationService):
    """Mock notification service that simulates email sending."""
    
    def __init__(self):
        self._sent_notifications: Dict[str, Dict[str, Any]] = {}
    
    def send_booking_confirmation(self, booking_reference: str, guest_email: str) -> bool:
        """Send booking confirmation email."""
        logger.info(f"Sending booking confirmation to {guest_email} "
                   f"for booking {booking_reference}")
        
        # Simulate email validation
        if not guest_email or "@" not in guest_email:
            logger.error(f"Invalid email address: {guest_email}")
            return False
        
        # Simulate successful email sending
        notification_record = {
            "type": "booking_confirmation",
            "booking_reference": booking_reference,
            "recipient": guest_email,
            "status": "sent",
            "subject": f"Booking Confirmation - {booking_reference}",
            "message": f"Your booking {booking_reference} has been confirmed!"
        }
        
        key = f"{booking_reference}_confirmation"
        self._sent_notifications[key] = notification_record
        
        logger.info(f"Booking confirmation sent successfully to {guest_email}")
        return True
    
    def send_cancellation_confirmation(self, booking_reference: str, guest_email: str) -> bool:
        """Send cancellation confirmation email."""
        logger.info(f"Sending cancellation confirmation to {guest_email} "
                   f"for booking {booking_reference}")
        
        # Simulate email validation
        if not guest_email or "@" not in guest_email:
            logger.error(f"Invalid email address: {guest_email}")
            return False
        
        # Simulate successful email sending
        notification_record = {
            "type": "cancellation_confirmation",
            "booking_reference": booking_reference,
            "recipient": guest_email,
            "status": "sent",
            "subject": f"Booking Cancellation - {booking_reference}",
            "message": f"Your booking {booking_reference} has been cancelled and refunded."
        }
        
        key = f"{booking_reference}_cancellation"
        self._sent_notifications[key] = notification_record
        
        logger.info(f"Cancellation confirmation sent successfully to {guest_email}")
        return True
    
    def get_notification_history(self, booking_reference: str) -> Dict[str, Any]:
        """Get notification history for a booking (utility method for testing)."""
        history = {}
        for key, notification in self._sent_notifications.items():
            if booking_reference in key:
                history[key] = notification
        return history
    
    def get_all_notifications(self) -> Dict[str, Dict[str, Any]]:
        """Get all sent notifications (utility method for testing)."""
        return self._sent_notifications.copy()


# Singleton instances for the application
payment_service = MockPaymentService()
notification_service = MockNotificationService()
