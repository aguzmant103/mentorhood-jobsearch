import logging
import os
import sys
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = FastAPI()
router = APIRouter()

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Job Search API is running"}

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "8000")
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )

# Define response models
class Job(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    link: Optional[str] = None

class JobSearchResponse(BaseModel):
    jobs: List[Job]
    message: str

@app.get("/test/jobs", response_model=JobSearchResponse)
async def test_jobs():
    logger.info("Test jobs endpoint called")
    try:
        sample_jobs = [
            Job(
                title="Software Engineer",
                company="Google",
                location="Remote",
                link="https://careers.google.com"
            ),
            Job(
                title="Solution Engineer",
                company="Microsoft",
                location="Remote US",
                link="https://careers.microsoft.com"
            )
        ]
        
        return JobSearchResponse(
            jobs=sample_jobs,
            message="Sample job listings retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error in test_jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 