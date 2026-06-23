from src.legal import LegalEngine
import os

def test_generate_email():
    engine = LegalEngine(templates_dir="templates")
    
    target_data = {"name": "John Doe", "email": "john@example.com", "phone": "555-0100"}
    exposure = {"url": "http://bad.com/john", "domain": "bad.com", "type": "data_broker"}
    enforcement = {"host_provider": "BadHost", "abuse_email": "abuse@bad.com"}
    
    email_content = engine.draft_email(target_data, exposure, enforcement)
    
    assert "Right to Deletion Request - John Doe" in email_content
    assert "http://bad.com/john" in email_content
