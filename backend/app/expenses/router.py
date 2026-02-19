from fastapi import APIRouter, Depends
from typing import List
from ..auth.router import read_users_me
from .schemas import ExpenseSummary, MonthlyExpense, CategoryExpense, PaymentMethod, TimelineData, StardustData
from . import service

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.get("/summary", response_model=ExpenseSummary)
async def get_expenses_summary(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    return service.get_summary(user_id, username)

@router.get("/monthly", response_model=List[MonthlyExpense])
async def get_monthly_expenses(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    return service.get_monthly(user_id, username)

@router.get("/categories", response_model=List[CategoryExpense])
async def get_category_expenses(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    return service.get_categories(user_id, username)

@router.get("/payment-methods", response_model=List[PaymentMethod])
async def get_payment_method_expenses(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    return service.get_payment_methods(user_id, username)

@router.get("/timeline", response_model=List[TimelineData])
async def get_expenses_timeline(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    return service.get_timeline(user_id, username)


@router.get("/stardust", response_model=StardustData)
async def get_expenses_stardust(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    return service.get_stardust(user_id, username)
