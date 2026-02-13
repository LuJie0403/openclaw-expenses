# backend/app/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from . import schemas, service
from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from typing import Dict

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: schemas.UserLogin):
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username'], "user_id": user['id']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: Dict = Depends(service.get_current_user)):
    return current_user
