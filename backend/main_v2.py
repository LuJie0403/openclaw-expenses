from fastapi import FastAPI, HTTPException, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pymysql
import json
from datetime import datetime, date
from decimal import Decimal
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="OpenClaw Expenses API", 
    version="1.0.0",
    description="个人支出数据管理RESTful API",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要具体配置
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '120.27.250.73'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'openclaw_aws'),
    'password': os.getenv('DB_PASSWORD', '9!wQSw@12sq'),
    'database': os.getenv('DB_NAME', 'iterlife4openclaw'),
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"数据库连接错误: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

# 请求/响应模型
class ExpenseFilter(BaseModel):
    start_date: Optional[str] = Field(None, description="开始日期(YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期(YYYY-MM-DD)")
    category: Optional[str] = Field(None, description="消费类别")
    sub_category: Optional[str] = Field(None, description="消费子类别")
    pay_account: Optional[str] = Field(None, description="支付账户")
    min_amount: Optional[float] = Field(None, ge=0, description="最小金额")
    max_amount: Optional[float] = Field(None, ge=0, description="最大金额")

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页条数")

class ApiResponse(BaseModel):
    code: int = Field(..., description="响应代码：0成功，其他失败")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    timestamp: str = Field(..., description="时间戳")

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# 工具函数
def create_response(code: int = 0, message: str = "success", data: Any = None) -> ApiResponse:
    """创建统一响应格式"""
    return ApiResponse(
        code=code,
        message=message,
        data=data,
        timestamp=datetime.now().isoformat()
    )

def create_error_response(message: str, code: int = 1) -> ApiResponse:
    """创建错误响应"""
    return create_response(code=code, message=message, data=None)

# API路由
@app.get("/api/v1/health", response_model=ApiResponse, tags=["Health"])
async def health_check():
    """
    健康检查
    
    GET /api/v1/health
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        conn.close()
        
        health_data = {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
            "service": "openclaw-expenses-api",
            "version": "1.0.0"
        }
        
        return create_response(data=health_data)
    except Exception as e:
        error_data = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "service": "openclaw-expenses-api"
        }
        return create_response(data=error_data, code=1, message="服务异常")

@app.get("/api/v1/expenses", response_model=ApiResponse, tags=["Expenses"])
async def get_expenses(
    filter_params: ExpenseFilter = Depends(),
    pagination: PaginationParams = Depends(),
    sort_by: str = Query("trans_datetime", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向: asc/desc")
):
    """
    获取支出列表 - 支持过滤、分页、排序
    
    GET /api/v1/expenses?start_date=2024-01-01&end_date=2024-12-31&page=1&page_size=20
    """
    conn = get_db_connection()
    try:
        # 构建查询条件
        conditions = []
        params = []
        
        if filter_params.start_date:
            conditions.append("trans_datetime >= %s")
            params.append(filter_params.start_date)
            
        if filter_params.end_date:
            conditions.append("trans_datetime <= %s")
            params.append(filter_params.end_date + " 23:59:59")
            
        if filter_params.category:
            conditions.append("t.trans_type_name = %s")
            params.append(filter_params.category)
            
        if filter_params.sub_category:
            conditions.append("t.trans_sub_type_name = %s")
            params.append(filter_params.sub_category)
            
        if filter_params.pay_account:
            conditions.append("f.pay_account = %s")
            params.append(filter_params.pay_account)
            
        if filter_params.min_amount is not None:
            conditions.append("f.trans_amount >= %s")
            params.append(filter_params.min_amount)
            
        if filter_params.max_amount is not None:
            conditions.append("f.trans_amount <= %s")
            params.append(filter_params.max_amount)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 排序
        sort_order_sql = "ASC" if sort_order.lower() == "asc" else "DESC"
        order_by = f"{sort_by} {sort_order_sql}"
        
        # 获取总数
        count_sql = f"""
        SELECT COUNT(*)
        FROM personal_expenses_final f
        JOIN personal_expenses_type t ON f.trans_code = t.trans_code AND f.trans_sub_code = t.trans_sub_code
        WHERE {where_clause}
        """
        
        with conn.cursor() as cursor:
            cursor.execute(count_sql, params)
            total = cursor.fetchone()[0]
            
            # 获取分页数据
            offset = (pagination.page - 1) * pagination.page_size
            
            data_sql = f"""
            SELECT 
                f.id,
                f.trans_datetime,
                f.trans_year,
                f.trans_month,
                f.trans_date,
                f.trans_time,
                f.trans_amount,
                f.trans_event,
                f.product_desc,
                f.pay_type,
                f.pay_account,
                f.bill_remark,
                t.trans_type_name,
                t.trans_sub_type_name
            FROM personal_expenses_final f
            JOIN personal_expenses_type t ON f.trans_code = t.trans_code AND f.trans_sub_code = t.trans_sub_code
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
            """
            
            params.extend([pagination.page_size, offset])
            cursor.execute(data_sql, params)
            results = cursor.fetchall()
            
            items = []
            for row in results:
                items.append({
                    "id": row[0],
                    "trans_datetime": row[1].strftime('%Y-%m-%d %H:%M:%S') if row[1] else '',
                    "trans_year": row[2],
                    "trans_month": row[3],
                    "trans_date": row[4],
                    "trans_time": row[5],
                    "trans_amount": float(row[6]),
                    "trans_event": row[7],
                    "product_desc": row[8],
                    "pay_type": row[9],
                    "pay_account": row[10],
                    "bill_remark": row[11],
                    "trans_type_name": row[12],
                    "trans_sub_type_name": row[13]
                })
            
            total_pages = (total + pagination.page_size - 1) // pagination.page_size
            
            paginated_data = PaginatedResponse(
                items=items,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=total_pages
            )
            
            return create_response(data=paginated_data.dict())
            
    finally:
        conn.close()

@app.get("/api/v1/expenses/summary", response_model=ApiResponse, tags=["Expenses"])
async def get_expenses_summary():
    """
    获取支出总览统计
    
    GET /api/v1/expenses/summary
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT 
                COUNT(*) as total_records,
                MIN(trans_datetime) as earliest_date,
                MAX(trans_datetime) as latest_date,
                SUM(trans_amount) as total_amount,
                AVG(trans_amount) as avg_amount
            FROM personal_expenses_final
            """
            cursor.execute(sql)
            result = cursor.fetchone()
            
            summary_data = {
                "total_amount": float(result[3]) if result[3] else 0,
                "total_count": int(result[0]) if result[0] else 0,
                "avg_amount": float(result[4]) if result[4] else 0,
                "earliest_date": result[1].strftime('%Y-%m-%d') if result[1] else '',
                "latest_date": result[2].strftime('%Y-%m-%d') if result[2] else ''
            }
            
            return create_response(data=summary_data)
    finally:
        conn.close()

@app.get("/api/v1/expenses/categories", response_model=ApiResponse, tags=["Expenses"])
async def get_expense_categories():
    """
    获取支出分类统计
    
    GET /api/v1/expenses/categories
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT 
                t.trans_type_name,
                t.trans_sub_type_name,
                COUNT(*) as count,
                SUM(f.trans_amount) as total_amount,
                AVG(f.trans_amount) as avg_amount
            FROM personal_expenses_final f
            JOIN personal_expenses_type t ON f.trans_code = t.trans_code AND f.trans_sub_code = t.trans_sub_code
            GROUP BY t.trans_type_name, t.trans_sub_type_name
            ORDER BY total_amount DESC
            LIMIT 20
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            categories = []
            for row in results:
                categories.append({
                    "trans_type_name": row[0],
                    "trans_sub_type_name": row[1],
                    "count": int(row[2]),
                    "total_amount": float(row[3]),
                    "avg_amount": float(row[4])
                })
            
            return create_response(data=categories)
    finally:
        conn.close()

@app.get("/api/v1/expenses/monthly", response_model=ApiResponse, tags=["Expenses"])
async def get_monthly_expenses():
    """
    获取月度支出统计
    
    GET /api/v1/expenses/monthly
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT 
                trans_year,
                trans_month,
                COUNT(*) as transaction_count,
                SUM(trans_amount) as monthly_total,
                AVG(trans_amount) as avg_transaction
            FROM personal_expenses_final
            GROUP BY trans_year, trans_month
            ORDER BY trans_year DESC, trans_month DESC
            LIMIT 24
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            monthly_data = []
            for row in results:
                monthly_data.append({
                    "year": row[0],
                    "month": row[1],
                    "transaction_count": int(row[2]),
                    "monthly_total": float(row[3]),
                    "avg_transaction": float(row[4])
                })
            
            return create_response(data=monthly_data)
    finally:
        conn.close()

@app.get("/api/v1/expenses/payment-methods", response_model=ApiResponse, tags=["Expenses"])
async def get_payment_methods():
    """
    获取支付方式统计
    
    GET /api/v1/expenses/payment-methods
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT 
                pay_account,
                COUNT(*) as usage_count,
                SUM(trans_amount) as total_spent,
                AVG(trans_amount) as avg_per_transaction
            FROM personal_expenses_final
            GROUP BY pay_account
            ORDER BY usage_count DESC
            LIMIT 15
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            payment_data = []
            for row in results:
                payment_data.append({
                    "pay_account": row[0],
                    "usage_count": int(row[1]),
                    "total_spent": float(row[2]),
                    "avg_per_transaction": float(row[3])
                })
            
            return create_response(data=payment_data)
    finally:
        conn.close()

@app.get("/api/v1/expenses/timeline", response_model=ApiResponse, tags=["Expenses"])
async def get_expense_timeline():
    """
    获取支出时间线数据
    
    GET /api/v1/expenses/timeline
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT 
                DATE(trans_datetime) as date,
                SUM(trans_amount) as daily_total,
                COUNT(*) as transaction_count
            FROM personal_expenses_final
            GROUP BY DATE(trans_datetime)
            ORDER BY date DESC
            LIMIT 90
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            timeline_data = []
            for row in results:
                timeline_data.append({
                    "date": row[0].strftime('%Y-%m-%d'),
                    "daily_total": float(row[1]),
                    "transaction_count": int(row[2])
                })
            
            return create_response(data=timeline_data)
    finally:
        conn.close()

# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return create_error_response(exc.detail, exc.status_code)

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    return create_error_response(f"服务器内部错误: {str(exc)}", 500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)