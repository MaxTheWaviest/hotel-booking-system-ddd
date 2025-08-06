# tests/infrastructure/test_services.py
"""Tests for infrastructure services."""

import pytest
from decimal import Decimal
from uuid import uuid4

from src.application.dtos import PaymentDTO
from src.infrastructure.services import MockPaymentService, MockNotificationService


class TestMockPaymentService:
    """Tests for MockPaymentService."""
    
    def test_successful_payment_processing(self):
        """Test successful payment processing."""
        service = MockPaymentService()
        
        payment = PaymentDTO(
            booking_id=uuid4(),
            amount=Decimal("200.00"),
            currency="GBP"
        )
        
        result = service.process_payment(payment)
        assert result is True
        
        # Check payment was recorded
        status = service.get_payment_status(str(payment.booking_id))
        assert status["status"] == "completed"
        assert status["amount"] == 200.0
        assert status["currency"] == "GBP"
    
    def test_invalid_payment_amount_fails(self):
        """Test that invalid payment amounts fail."""
        service = MockPaymentService()
        
        # Negative amount
        payment = PaymentDTO(
            booking_id=uuid4(),
            amount=Decimal("-10.00"),
            currency="GBP"
        )
        
        result = service.process_payment(payment)
        assert result is False
        
        # Zero amount
        payment.amount = Decimal("0.00")
        result = service.process_payment(payment)
        assert result is False
    
    def test_payment_amount_too_large_fails(self):
        """Test that very large payments fail."""
        service = MockPaymentService()
        
        payment = PaymentDTO(
            booking_id=uuid4(),
            amount=Decimal("15000.00"),  # Exceeds 10k limit
            currency="GBP"
        )
        
        result = service.process_payment(payment)
        assert result is False
    
    def test_successful_refund_processing(self):
        """Test successful refund processing."""
        service = MockPaymentService()
        
        payment = PaymentDTO(
            booking_id=uuid4(),
            amount=Decimal("200.00"),
            currency="GBP"
        )
        
        # First process the original payment
        assert service.process_payment(payment) is True
        
        # Then process the refund
        refund_result = service.refund_payment(payment)
        assert refund_result is True
        
        # Check refund was recorded
        refund_status = service.get_refund_status(str(payment.booking_id))
        assert refund_status["status"] == "completed"
        assert refund_status["amount"] == 200.0
    
    def test_refund_without_original_payment_fails(self):
        """Test that refund fails without original payment."""
        service = MockPaymentService()
        
        payment = PaymentDTO(
            booking_id=uuid4(),
            amount=Decimal("200.00"),
            currency="GBP"
        )
        
        # Try to refund without original payment
        result = service.refund_payment(payment)
        assert result is False


class TestMockNotificationService:
    """Tests for MockNotificationService."""
    
    def test_successful_booking_confirmation(self):
        """Test successful booking confirmation email."""
        service = MockNotificationService()
        
        result = service.send_booking_confirmation(
            booking_reference="ABC1234567",
            guest_email="john.doe@example.com"
        )
        
        assert result is True
        
        # Check notification was recorded
        history = service.get_notification_history("ABC1234567")
        assert "ABC1234567_confirmation" in history
        
        confirmation = history["ABC1234567_confirmation"]
        assert confirmation["type"] == "booking_confirmation"
        assert confirmation["recipient"] == "john.doe@example.com"
        assert confirmation["status"] == "sent"
    
    def test_successful_cancellation_confirmation(self):
        """Test successful cancellation confirmation email."""
        service = MockNotificationService()
        
        result = service.send_cancellation_confirmation(
            booking_reference="ABC1234567",
            guest_email="john.doe@example.com"
        )
        
        assert result is True
        
        # Check notification was recorded
        history = service.get_notification_history("ABC1234567")
        assert "ABC1234567_cancellation" in history
        
        cancellation = history["ABC1234567_cancellation"]
        assert cancellation["type"] == "cancellation_confirmation"
        assert cancellation["recipient"] == "john.doe@example.com"
        assert cancellation["status"] == "sent"
    
    def test_invalid_email_fails(self):
        """Test that invalid email addresses fail."""
        service = MockNotificationService()
        
        # Empty email
        result = service.send_booking_confirmation(
            booking_reference="ABC1234567",
            guest_email=""
        )
        assert result is False
        
        # Invalid email format
        result = service.send_booking_confirmation(
            booking_reference="ABC1234567",
            guest_email="not-an-email"
        )
        assert result is False
    
    def test_notification_history_tracking(self):
        """Test that notification history is properly tracked."""
        service = MockNotificationService()
        
        # Send multiple notifications
        service.send_booking_confirmation("REF1234567", "guest1@example.com")
        service.send_cancellation_confirmation("REF1234567", "guest1@example.com")
        service.send_booking_confirmation("REF7654321", "guest2@example.com")
        
        # Check individual booking history
        ref1_history = service.get_notification_history("REF1234567")
        assert len(ref1_history) == 2  # Confirmation + cancellation
        
        ref2_history = service.get_notification_history("REF7654321")
        assert len(ref2_history) == 1  # Just confirmation
        
        # Check all notifications
        all_notifications = service.get_all_notifications()
        assert len(all_notifications) == 3
