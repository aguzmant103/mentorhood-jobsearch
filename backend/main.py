from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.job_search_api import router as job_search_router

app = FastAPI(
    title="Job Search API",
    description="API for automated job searching and application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(job_search_router)

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "message": "Job Search API is running",
        "version": "1.0.0"
    } 