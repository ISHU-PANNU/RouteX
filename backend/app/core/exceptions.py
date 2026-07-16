from typing import Any, Optional, Dict, List

class RouteXException(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or []
        super().__init__(message)

class EntityNotFoundError(RouteXException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=404,
            error_code="ENTITY_NOT_FOUND",
            message=message
        )

class VerificationFailedError(RouteXException):
    def __init__(self, message: str = "Verification criteria failed"):
        super().__init__(
            status_code=400,
            error_code="VERIFICATION_FAILED",
            message=message
        )

class AuthenticationError(RouteXException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            status_code=401,
            error_code="UNAUTHORIZED",
            message=message
        )

class ForbiddenError(RouteXException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=403,
            error_code="FORBIDDEN",
            message=message
        )

class BadRequestError(RouteXException):
    def __init__(self, message: str = "Invalid request action"):
        super().__init__(
            status_code=400,
            error_code="BAD_REQUEST",
            message=message
        )
