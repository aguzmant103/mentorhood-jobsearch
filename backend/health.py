from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/")
async def root():
    return {"message": "Job Search API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/test/jobs", response_model=JobSearchResponse)
async def test_jobs():
    """Test endpoint that returns sample job listings"""
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