from datetime import datetime, timedelta, timezone
import hashlib
from typing import Optional, Tuple
from sqlalchemy.orm import Session
import jwt
from app.config.config import settings
from app.core import security
from app.core.exceptions import AuthenticationError, BadRequestError
from app.models.user import User
from app.models.token import RefreshToken
from app.repositories.user import user_repository
from app.schemas.auth import UserRegister, UserLogin, Token, UserOut

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

class AuthService:
    def register_user(self, db: Session, user_in: UserRegister) -> User:
        existing_user = user_repository.get_by_email(db, email=user_in.email)
        if existing_user:
            raise BadRequestError("Email address is already registered.")
            
        hashed_password = security.get_password_hash(user_in.password)
        db_user = User(
            name=user_in.name,
            email=user_in.email,
            password_hash=hashed_password,
            phone=user_in.phone,
            role=user_in.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate_user(self, db: Session, login_in: UserLogin) -> Token:
        user = user_repository.get_by_email(db, email=login_in.email)
        if not user or not security.verify_password(login_in.password, user.password_hash):
            raise AuthenticationError("Incorrect email or password credentials.")
            
        access_token = security.create_access_token(subject=user.id, role=user.role.value)
        refresh_token = security.create_refresh_token(subject=user.id, role=user.role.value)
        
        # Save refresh token record to DB as naive UTC
        token_hash = _hash_token(refresh_token)
        expiry_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=expiry_days)
        
        db_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()
        
        user_out = UserOut.model_validate(user)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_out
        )

    def refresh_access_token(self, db: Session, refresh_token: str) -> str:
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type.")
            user_id = payload.get("sub")
            role = payload.get("role")
        except jwt.PyJWTError:
            raise AuthenticationError("Could not decode refresh token.")
            
        token_hash = _hash_token(refresh_token)
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False
        ).first()
        
        current_time_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        if not db_token or db_token.expires_at < current_time_naive:
            raise AuthenticationError("Refresh token is expired, revoked or invalid.")
            
        # Generate new access token
        new_access_token = security.create_access_token(subject=user_id, role=role)
        return new_access_token

    def revoke_refresh_token(self, db: Session, refresh_token: str) -> None:
        token_hash = _hash_token(refresh_token)
        db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if db_token:
            db_token.revoked = True
            db.commit()

auth_service = AuthService()
