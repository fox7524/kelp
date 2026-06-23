from src.scanner import Scanner

def test_scanner_finds_exposures():
    scanner = Scanner()
    target_data = {"email": "test@example.com"}
    results = scanner.scan(target_data)
    
    assert len(results) > 0
    assert "url" in results[0]
    assert "type" in results[0]
