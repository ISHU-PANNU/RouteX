from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.schemas.auth import UserRegister, UserLogin, Token, TokenRefreshRequest, TokenRefreshResponse, UserOut
from app.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register", 
    response_model=UserOut, 
    status_code=status.HTTP_201_CREATED,
    summary="Register Account",
    description="Registers a new customer user profile. Passwords undergo bcrypt rounds encryption."
)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    return auth_service.register_user(db, user_in=user_in)

@router.post(
    "/login", 
    response_model=Token, 
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates credentials and returns access and refresh JWT tokens."
)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    return auth_service.authenticate_user(db, login_in=login_in)

@router.post(
    "/refresh", 
    response_model=TokenRefreshResponse, 
    status_code=status.HTTP_200_OK,
    summary="Token Refresh",
    description="Issues a fresh access JWT token using a valid, non-expired refresh JWT token."
)
def refresh(refresh_in: TokenRefreshRequest, db: Session = Depends(get_db)):
    access_token = auth_service.refresh_access_token(db, refresh_token=refresh_in.refresh_token)
    return TokenRefreshResponse(access_token=access_token)

@router.post(
    "/logout", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke Token / Logout",
    description="Blacklists/revokes the provided refresh token to invalidate active sessions."
)
def logout(refresh_in: TokenRefreshRequest, db: Session = Depends(get_db)):
    auth_service.revoke_refresh_token(db, refresh_token=refresh_in.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
