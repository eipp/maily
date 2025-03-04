from packages.error_handling.python.errors import ValidationError

def test_validation_error():
    """Test that our standardized error system works."""
    error = ValidationError(
        message="Test validation error",
        details={"field": "email", "error": "Invalid email format"}
    )
    
    # Verify error properties
    assert error.message == "Test validation error"
    assert error.status_code == 422
    assert "field" in error.details
    
    # Verify serialization
    response = error.to_response()
    assert response["error"] == True
    assert response["error_code"] == "validation_error"
    assert response["status_code"] == 422
    
    print("Validation error test passed\!")

if __name__ == "__main__":
    test_validation_error()

