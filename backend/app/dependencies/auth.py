from typing import List, Optional
import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config.config import settings
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.database.session import SessionLocal
from app.dependencies.db import get_db
from app.models.user import User, UserRole
from app.repositories.user import user_repository

# Standard OAuth2 scheme to extract token from headers
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise AuthenticationError("Authentication token is missing. Please log in.")
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if not user_id_str or token_type != "access":
            raise AuthenticationError("Invalid authentication token claims.")
            
        user_id = int(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise AuthenticationError("Could not decode or validate authentication token.")
        
    user = user_repository.get(db, id=user_id)
    if not user:
        raise AuthenticationError("Authenticated user does not exist in the database.")
        
    return user

def get_current_user_optional(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if not user_id_str or token_type != "access":
            return None
            
        user_id = int(user_id_str)
        return user_repository.get(db, id=user_id)
    except (jwt.PyJWTError, ValueError):
        return None

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenError(
                f"Action forbidden. User role must be one of: "
                f"{[r.value for r in self.allowed_roles]}."
            )
        return current_user
