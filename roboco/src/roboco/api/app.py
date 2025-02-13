import os
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="RoboCo API",
    description="API for RoboCo service",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to RoboCo API"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

def start():
    """Start the RoboCo service."""
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    uvicorn.run(
        "roboco.api.app:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload
    ) 