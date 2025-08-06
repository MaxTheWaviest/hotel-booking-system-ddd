"""Basic test to ensure pytest is working."""

def test_basic():
    """Basic test that always passes."""
    assert True

def test_string_operations():
    """Test basic string operations."""
    text = "Hotel Booking System"
    assert "Hotel" in text
    assert len(text) > 0
