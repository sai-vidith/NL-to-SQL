"""
Custom exception classes for the NL-to-SQL platform.
All exceptions inherit from a base NexusError for unified error handling.
"""

from __future__ import annotations

from typing import Any


class NexusError(Exception):
    """Base exception for all Nexus platform errors."""

    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


# ── Authentication Errors ────────────────────────────────────────

class AuthenticationError(NexusError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class InvalidTokenError(AuthenticationError):
    """Raised when a JWT token is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message=message)


class InsufficientPermissionsError(NexusError):
    """Raised when user lacks required role/permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=403)


# ── User Errors ──────────────────────────────────────────────────

class UserAlreadyExistsError(NexusError):
    """Raised when registering with an existing username/email."""

    def __init__(self, field: str = "email"):
        super().__init__(
            message=f"A user with this {field} already exists",
            status_code=409,
        )


class UserNotFoundError(NexusError):
    """Raised when a user is not found."""

    def __init__(self, message: str = "User not found"):
        super().__init__(message=message, status_code=404)


# ── Query Errors ─────────────────────────────────────────────────

class QueryValidationError(NexusError):
    """Raised when generated SQL fails validation (dangerous operations, etc.)."""

    def __init__(self, message: str, details: Any = None):
        super().__init__(
            message=message,
            status_code=400,
            details=details,
        )


class QueryExecutionError(NexusError):
    """Raised when SQL execution fails."""

    def __init__(self, message: str = "Query execution failed", details: Any = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details,
        )


class QueryTimeoutError(NexusError):
    """Raised when SQL execution exceeds timeout."""

    def __init__(self, timeout_seconds: int = 10):
        super().__init__(
            message=f"Query execution exceeded {timeout_seconds}s timeout",
            status_code=408,
        )


class SQLGenerationError(NexusError):
    """Raised when the LLM fails to generate valid SQL."""

    def __init__(self, message: str = "Failed to generate SQL from your question"):
        super().__init__(message=message, status_code=422)


# ── Rate Limiting ────────────────────────────────────────────────

class RateLimitExceededError(NexusError):
    """Raised when rate limit is exceeded."""

    def __init__(self, limit: int = 50):
        super().__init__(
            message=f"Rate limit exceeded. Maximum {limit} requests per minute.",
            status_code=429,
        )


# ── Resource Errors ──────────────────────────────────────────────

class ResourceNotFoundError(NexusError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", resource_id: str | None = None):
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=msg, status_code=404)


# ── LLM Errors ───────────────────────────────────────────────────

class LLMError(NexusError):
    """Raised when the LLM API call fails."""

    def __init__(self, message: str = "LLM service unavailable"):
        super().__init__(message=message, status_code=503)
