from src.takedown import Enforcer

def test_enforcer_lookup():
    enforcer = Enforcer()
    result = enforcer.lookup_domain("sketchy-broker.com")
    
    assert result["domain"] == "sketchy-broker.com"
    assert "abuse_email" in result
