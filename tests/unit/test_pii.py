from src.services.pii_service import redact_pii

def test_redacts_contact_details():
    result = redact_pii("Email me@example.com or call +91 98765 43210")
    assert "me@example.com" not in result and "98765" not in result
