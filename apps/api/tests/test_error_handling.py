"""Tests for error handling middleware and custom errors."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ..errors import AIError, AuthError, DatabaseError, RateLimitError, ValidationError
from ..middleware.error_handler import error_handler_middleware, register_error_handlers

app = FastAPI()
register_error_handlers(app)


@app.get("/test-auth-error")
async def test_auth_error():
    raise AuthError("Invalid credentials")


@app.get("/test-validation-error")
async def test_validation_error():
    raise ValidationError("Invalid input data")


@app.get("/test-database-error")
async def test_database_error():
    raise DatabaseError("Database connection failed")


@app.get("/test-ai-error")
async def test_ai_error():
    raise AIError("AI model failed to process request")


@app.get("/test-rate-limit-error")
async def test_rate_limit_error():
    raise RateLimitError("Too many requests")


@app.get("/test-unhandled-error")
async def test_unhandled_error():
    raise Exception("Unexpected error")


client = TestClient(app)


def test_auth_error_handling():
    response = client.get("/test-auth-error")
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid credentials", "type": "AuthError"}


def test_validation_error_handling():
    response = client.get("/test-validation-error")
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid input data", "type": "ValidationError"}


def test_database_error_handling():
    response = client.get("/test-database-error")
    assert response.status_code == 500
    assert response.json() == {
        "error": "Database connection failed",
        "type": "DatabaseError",
    }


def test_ai_error_handling():
    response = client.get("/test-ai-error")
    assert response.status_code == 500
    assert response.json() == {
        "error": "AI model failed to process request",
        "type": "AIError",
    }


def test_rate_limit_error_handling():
    response = client.get("/test-rate-limit-error")
    assert response.status_code == 429
    assert response.json() == {"error": "Too many requests", "type": "RateLimitError"}


def test_unhandled_error_handling():
    response = client.get("/test-unhandled-error")
    assert response.status_code == 500
    assert response.json() == {
        "error": "An unexpected error occurred",
        "type": "InternalServerError",
    }
