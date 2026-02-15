# backend/app/auth/service.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Dict, Optional

from app.core.database import get_db_connection
from app.core.security import ALGORITHM, SECRET_KEY, verify_password
from . import schemas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_user_by_username(username: str) -> Optional[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, username, email, hashed_password, full_name, is_active, created_at FROM expenses_user WHERE username = %s"
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()
            return user_data if user_data else None
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> Optional[Dict]:
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
        # Ensure user_id is treated as string if it's not None
        user_id_raw = payload.get("user_id")
        user_id: str = str(user_id_raw) if user_id_raw is not None else None
        
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    # Optional: Verify ID matches if needed, but username is unique
    if user_id and str(user['id']) != user_id:
         raise credentials_exception
         
    return user
