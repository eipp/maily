"""
Example FastAPI application using standardized error handling.

This demonstrates how to set up and use the error handling package in a FastAPI application.
"""
from fastapi import FastAPI, Depends, Request
from pydantic import BaseModel, Field

from packages.error_handling.python.error import (
    MailyError,
    ValidationError,
    ResourceNotFoundError,
    UnauthorizedError,
    QuotaExceededError
)
from packages.error_handling.python.middleware import setup_error_handling

# Create FastAPI application
app = FastAPI(title="Error Handling Example")

# Set up standardized error handling
error_handler = setup_error_handling(
    app, 
    documentation_url_base="https://docs.maily.com/errors",
    include_debug_info=True
)

# Define request models
class UserRequest(BaseModel):
    username: str = Field(min_length=3, description="User's username")
    email: str = Field(description="User's email address")

# Define fake database
USERS = {
    "1": {"id": "1", "username": "john", "email": "john@example.com"},
    "2": {"id": "2", "username": "jane", "email": "jane@example.com"},
}

# Define dependency for authentication
def get_current_user(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != "valid_api_key":
        raise UnauthorizedError("Invalid API key")
    return {"api_key": api_key}

# Define API routes
@app.get("/")
def read_root():
    return {"message": "Error handling example API"}

@app.get("/users/{user_id}")
def read_user(user_id: str, current_user = Depends(get_current_user)):
    if user_id not in USERS:
        raise ResourceNotFoundError(
            f"User with ID {user_id} not found",
            details={"user_id": user_id}
        )
    return USERS[user_id]

@app.post("/users")
def create_user(user: UserRequest, current_user = Depends(get_current_user)):
    # Check if username already exists
    for existing_user in USERS.values():
        if existing_user["username"] == user.username:
            raise ValidationError(
                "Username already exists",
                details=[{
                    "code": "validation.unique",
                    "message": "This username is already taken",
                    "field": "username"
                }]
            )
    
    # Check if we've reached the user limit (for demo purposes)
    if len(USERS) >= 10:
        raise QuotaExceededError(
            "User limit reached. Please upgrade your plan.",
            details={"current_count": len(USERS), "limit": 10}
        )
    
    # Create the user
    user_id = str(len(USERS) + 1)
    USERS[user_id] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
    }
    return USERS[user_id]

@app.delete("/users/{user_id}")
def delete_user(user_id: str, current_user = Depends(get_current_user)):
    if user_id not in USERS:
        raise ResourceNotFoundError(
            f"User with ID {user_id} not found",
            details={"user_id": user_id}
        )
    
    deleted_user = USERS.pop(user_id)
    return {"message": f"User {deleted_user['username']} deleted"}

# Error triggering routes (for testing)
@app.get("/errors/validation")
def trigger_validation_error():
    raise ValidationError(
        "Validation error example",
        details=[{
            "code": "validation.required",
            "message": "This field is required",
            "field": "username"
        }]
    )

@app.get("/errors/not-found")
def trigger_not_found_error():
    raise ResourceNotFoundError("Resource not found example")

@app.get("/errors/unauthorized")
def trigger_unauthorized_error():
    raise UnauthorizedError("Unauthorized error example")

@app.get("/errors/server")
def trigger_server_error():
    # This will be caught by the error handler middleware
    raise Exception("Uncaught server error example")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)