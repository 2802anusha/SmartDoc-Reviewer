from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.database import create_db_and_tables
from app.routers.review import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup — creates database tables if they don't exist.
    """
    create_db_and_tables()
    print("Database tables created")
    yield
    print("Shutting down SmartDoc Reviewer")


app = FastAPI(
    title="SmartDoc Reviewer",
    description="AI-powered GitHub PR code review agent",
    version="1.0.0",
    lifespan=lifespan
)

# Register all routes
app.include_router(router)