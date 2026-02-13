# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.expenses import router as expenses_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API Routers
api_router = FastAPI()
api_router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
api_router.include_router(expenses_router.router, prefix="/expenses", tags=["expenses"])

app.include_router(api_router, prefix="/api")

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
