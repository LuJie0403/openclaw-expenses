# backend/app/auth/service.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Dict

from app.core.database import get_db_connection
from app.core.security import ALGORITHM, SECRET_KEY, verify_password
from . import schemas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_user_by_username(username: str) -> Dict | None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, username, email, hashed_password, full_name, is_active, created_at FROM expenses_user WHERE username = %s"
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()
            return user_data if user_data else None
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> Dict | None:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user['hashed_password']):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(username)
    if user is None or user['id'] != user_id:
        raise credentials_exception
    return user
