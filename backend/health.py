from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    port = os.getenv("PORT", 8000)
    logger.info(f"Starting application on port {port}")

# Define response models
class Job(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    link: Optional[str] = None

class JobSearchResponse(BaseModel):
    jobs: List[Job]
    message: str

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Job Search API is running"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

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