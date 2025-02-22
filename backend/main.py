from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.job_search_api import router as job_search_router
from health import router as health_router
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Job Search API",
    description="API for automated job searching and application",
    version="1.0.0",
    docs_url="/docs",   # Enable Swagger UI
    redoc_url="/redoc"  # Enable ReDoc
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
app.include_router(health_router)  # Mount health router at root
app.include_router(
    job_search_router,
    prefix="/api",  # Add /api prefix for job search routes
    tags=["job-search"]
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    logger.info(f"Available routes: {[route.path for route in app.routes]}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "traceback": traceback.format_exc()}
        )

@app.get("/")
async def root():
    routes = [{"path": route.path, "methods": route.methods} for route in app.routes]
    return {
        "status": "healthy",
        "message": "Job Search API is runninggss",
        "version": "1.0.0",
        "available_routes": routes
    }

# Log startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Job Search API")
    logger.info("Available routes:")
    for route in app.routes:
        logger.info(f"{route.methods} {route.path}") 