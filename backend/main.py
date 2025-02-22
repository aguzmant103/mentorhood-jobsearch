from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.job_search_api import router as job_search_router

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(job_search_router, prefix="/api")

@app.get("/")
async def root():
    return {"status": "healthy"} 