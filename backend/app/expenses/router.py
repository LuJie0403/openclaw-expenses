# backend/app/expenses/router.py
from fastapi import APIRouter, Depends
from typing import List, Dict
from . import schemas, service
from app.auth.service import get_current_user

router = APIRouter()

@router.get("/summary", response_model=schemas.ExpenseSummary)
async def get_expenses_summary(current_user: Dict = Depends(get_current_user)):
    return service.get_summary(current_user)

@router.get("/monthly", response_model=List[schemas.MonthlyExpense])
async def get_monthly_expenses(current_user: Dict = Depends(get_current_user)):
    return service.get_monthly(current_user)

@router.get("/categories", response_model=List[schemas.CategoryExpense])
async def get_category_expenses(current_user: Dict = Depends(get_current_user)):
    return service.get_categories(current_user)

@router.get("/payment-methods", response_model=List[schemas.PaymentMethod])
async def get_payment_method_expenses(current_user: Dict = Depends(get_current_user)):
    return service.get_payment_methods(current_user)

@router.get("/timeline", response_model=List[schemas.TimelineData])
async def get_expenses_timeline(current_user: Dict = Depends(get_current_user)):
    return service.get_timeline(current_user)

@router.get("/stardust")
async def get_expenses_stardust(current_user: Dict = Depends(get_current_user)):
    return service.get_stardust_data(current_user)
