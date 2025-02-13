"""Main FastAPI application for RoboCo."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from roboco.core.logging import setup_logging
from roboco.api.routes import agents

# Configure logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="RoboCo API",
    description="API for RoboCo - Multi-Agent System for Humanoid Robot Development",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 