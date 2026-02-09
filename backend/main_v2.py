#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Depends, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import pymysql
import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import settings

load_dotenv()

app = FastAPI(
    title="OpenClaw Expenses API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_db_connection():
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(UserBase):
    id: str
    created_at: datetime

class ExpenseSummary(BaseModel):
    total_amount: float
    total_count: int
    avg_amount: float
    earliest_date: Optional[str]
    latest_date: Optional[str]

class MonthlyExpense(BaseModel):
    year: str
    month: str
    transaction_count: int
    monthly_total: float
    avg_transaction: float

class CategoryExpense(BaseModel):
    trans_type_name: Optional[str] # From personal_expenses_type
    trans_sub_type_name: Optional[str] # From personal_expenses_type
    count: int
    total_amount: float
    avg_amount: float

class PaymentMethod(BaseModel):
    pay_account: str
    usage_count: int
    total_spent: float
    avg_per_transaction: float

class TimelineData(BaseModel):
    date: str
    daily_total: float
    transaction_count: int

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    # Ensure password is not too long for bcrypt
    if len(plain_password) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Ensure password is not too long for bcrypt
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def get_user_by_username(username: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, username, email, hashed_password, full_name, is_active, created_at FROM expenses_user WHERE username = %s"
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()
            if user_data:
                return {
                    "id": user_data['id'],  # Corrected from user_data[0]
                    "username": user_data['username'], # Corrected from user_data[1]
                    "email": user_data['email'], # Corrected from user_data[2]
                    "hashed_password": user_data['hashed_password'], # Corrected from user_data[3]
                    "full_name": user_data['full_name'], # Corrected from user_data[4]
                    "is_active": user_data['is_active'], # Corrected from user_data[5]
                    "created_at": user_data['created_at'], # Corrected from user_data[6]
                }
            return None
    finally:
        conn.close()

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user['hashed_password']):
        return False
    return user

# --- Authentication Routes ---
@api_router.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    user = authenticate_user(form_data.username, form_data.password)
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

@api_router.get("/auth/me", response_model=UserResponse)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Fetch user data from DB by username to ensure it's active
    user_data = get_user_by_username(username)
    if not user_data or user_data['id'] != user_id:
        raise HTTPException(status_code=404, detail="User not found or token mismatch")
    
    return user_data

# --- Expenses Data Routes ---
@api_router.get("/expenses/summary", response_model=ExpenseSummary)
async def get_expenses_summary(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                COALESCE(SUM(trans_amount), 0) AS total_amount,
                COALESCE(COUNT(id), 0) AS total_count,
                COALESCE(AVG(trans_amount), 0) AS avg_amount,
                MIN(trans_datetime) AS earliest_date,
                MAX(trans_datetime) AS latest_date
            FROM personal_expenses_final
            WHERE created_by = %s
            """
            cursor.execute(sql, (str(user_id),))
            result = cursor.fetchone()
            if result and result['earliest_date']:
                result['earliest_date'] = result['earliest_date'].strftime("%Y-%m-%d")
            if result and result['latest_date']:
                result['latest_date'] = result['latest_date'].strftime("%Y-%m-%d")
            return result
    finally:
        conn.close()

@api_router.get("/expenses/monthly", response_model=List[MonthlyExpense])
async def get_monthly_expenses(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                trans_year AS year,
                trans_month AS month,
                COUNT(id) AS transaction_count,
                SUM(trans_amount) AS monthly_total,
                AVG(trans_amount) AS avg_transaction
            FROM personal_expenses_final
            WHERE created_by = %s
            GROUP BY trans_year, trans_month
            ORDER BY trans_year DESC, trans_month DESC
            """
            cursor.execute(sql, (str(user_id),))
            return cursor.fetchall()
    finally:
        conn.close()

@api_router.get("/expenses/categories", response_model=List[CategoryExpense])
async def get_category_expenses(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                pet.trans_type_name,
                pet.trans_sub_type_name,
                COUNT(pef.id) AS count,
                SUM(pef.trans_amount) AS total_amount,
                AVG(pef.trans_amount) AS avg_amount
            FROM personal_expenses_final AS pef
            JOIN personal_expenses_type AS pet
                ON pef.trans_code = pet.trans_code AND pef.trans_sub_code = pet.trans_sub_code
            WHERE pef.created_by = %s
            GROUP BY pet.trans_type_name, pet.trans_sub_type_name
            ORDER BY total_amount DESC
            """
            cursor.execute(sql, (str(user_id),))
            return cursor.fetchall()
    finally:
        conn.close()

@api_router.get("/expenses/payment-methods", response_model=List[PaymentMethod])
async def get_payment_method_expenses(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                pay_account,
                COUNT(id) AS usage_count,
                SUM(trans_amount) AS total_spent,
                AVG(trans_amount) AS avg_per_transaction
            FROM personal_expenses_final
            WHERE created_by = %s
            GROUP BY pay_account
            ORDER BY total_spent DESC
            """
            cursor.execute(sql, (str(user_id),))
            return cursor.fetchall()
    finally:
        conn.close()

@api_router.get("/expenses/timeline", response_model=List[TimelineData])
async def get_expenses_timeline(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                trans_date AS date,
                SUM(trans_amount) AS daily_total,
                COUNT(id) AS transaction_count
            FROM personal_expenses_final
            WHERE created_by = %s
            GROUP BY trans_date
            ORDER BY trans_date ASC
            """
            cursor.execute(sql, (str(user_id),))
            return cursor.fetchall()
    finally:
        conn.close()

# Include the router in the app
app.include_router(api_router)
