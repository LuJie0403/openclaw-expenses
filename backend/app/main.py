
from fastapi import FastAPI
from .core.config import settings
from .auth import router as auth_router
from .expenses import router as expenses_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION
)

# Include routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(expenses_router.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to OpenClaw Expenses API"}
