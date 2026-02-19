from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .auth import router as auth_router
from .expenses import router as expenses_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_health_payload():
    return {
        "status": "ok",
        "service": "openclaw-expenses-api",
        "version": app.version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/health")
async def health_check_root():
    return get_health_payload()


@app.get("/api/health")
async def health_check_api():
    return get_health_payload()


# Include business routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(expenses_router.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to OpenClaw Expenses API"}
