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
# Allow all origins for simplicity in this deployment context, or use settings
origins = settings.BACKEND_CORS_ORIGINS if settings.BACKEND_CORS_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(expenses_router.router, prefix="/api/expenses", tags=["expenses"])

# Health Check Endpoint
@app.get("/api/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": settings.PROJECT_VERSION, "app": "openclaw-expenses"}

@app.get("/")
async def root():
    return {"message": "OpenClaw Expenses API is running. Visit /docs for documentation."}
