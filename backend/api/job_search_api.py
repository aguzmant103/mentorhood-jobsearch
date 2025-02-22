from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import subprocess
import os
import csv
import asyncio
import logging
import traceback
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create router with explicit prefix
router = APIRouter(
    tags=["job-search"],
    responses={404: {"description": "Not found"}},
)

# Store background tasks and their status
job_searches: Dict[str, dict] = {}

async def run_job_search(companies: list[str], task_id: str):
    try:
        logger.info(f"Starting job search for companies: {companies}")
        # Run the job search script
        process = await asyncio.create_subprocess_exec(
            "python", 
            "backend/job-search.py",
            "--companies", ",".join(companies),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Update task status
        if process.returncode == 0:
            job_searches[task_id]["status"] = "completed"
            job_searches[task_id]["logs"] = stdout.decode() + stderr.decode()
            logger.info(f"Job search completed for task {task_id}")
        else:
            job_searches[task_id]["status"] = "failed"
            job_searches[task_id]["error"] = stderr.decode()
            logger.error(f"Job search failed for task {task_id}: {stderr.decode()}")
            
    except Exception as e:
        job_searches[task_id]["status"] = "failed"
        job_searches[task_id]["error"] = str(e)
        logger.error(f"Error in job search task {task_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

@router.post("/test/job")
async def start_job_search(
    request: Request,
    background_tasks: BackgroundTasks
):
    try:
        logger.info(f"Received request to {request.url}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Get companies from request body
        body = await request.json()
        logger.info(f"Request body: {body}")
        
        companies = body.get("companies", ["Google"])
        logger.info(f"Processing job search request for companies: {companies}")
        
        # Generate unique task ID
        task_id = os.urandom(8).hex()
        logger.info(f"Generated task ID: {task_id}")
        
        # Initialize task status
        job_searches[task_id] = {
            "status": "running",
            "companies": companies,
            "logs": "",
            "error": None
        }
        
        # Start background task
        background_tasks.add_task(run_job_search, companies, task_id)
        logger.info(f"Started background task for {task_id}")
        
        return {
            "task_id": task_id, 
            "status": "started",
            "message": f"Started job search for companies: {', '.join(companies)}"
        }
        
    except Exception as e:
        error_msg = f"Error starting job search: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "traceback": traceback.format_exc(),
                "request_info": {
                    "url": str(request.url),
                    "method": request.method,
                    "headers": dict(request.headers)
                }
            }
        )

@router.get("/test/job/{task_id}")
async def get_job_search_status(task_id: str):
    logger.info(f"Checking status for task {task_id}")
    
    if task_id not in job_searches:
        error_msg = f"Task not found: {task_id}"
        logger.error(error_msg)
        raise HTTPException(status_code=404, detail=error_msg)
    
    task_info = job_searches[task_id]
    logger.info(f"Task info: {task_info}")
    
    # Read CSV file if task is completed
    jobs = []
    if task_info["status"] == "completed":
        try:
            csv_file = "jobs.csv"
            if os.path.exists(csv_file):
                with open(csv_file, "r") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        jobs.append({
                            "title": row[0],
                            "company": row[1],
                            "link": row[2],
                            "salary": row[3],
                            "location": row[4]
                        })
                logger.info(f"Found {len(jobs)} jobs for task {task_id}")
        except Exception as e:
            error_msg = f"Error reading CSV: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    return {
        "status": task_info["status"],
        "error": task_info.get("error"),
        "logs": task_info.get("logs", ""),
        "companies": task_info["companies"],
        "jobs": jobs if jobs else None
    }

@router.delete("/test/job/{task_id}")
async def cleanup_job_search(task_id: str):
    logger.info(f"Cleaning up task {task_id}")
    
    if task_id not in job_searches:
        error_msg = f"Task not found: {task_id}"
        logger.error(error_msg)
        raise HTTPException(status_code=404, detail=error_msg)
    
    try:
        # Remove task from memory
        del job_searches[task_id]
        logger.info(f"Successfully cleaned up task {task_id}")
        return {"status": "cleaned", "message": f"Task {task_id} cleaned up successfully"}
        
    except Exception as e:
        error_msg = f"Error cleaning up task {task_id}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/debug-routes")
async def debug_routes():
    """Helper endpoint to debug available routes"""
    routes = []
    for route in router.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": route.methods
        })
    logger.info(f"Available routes in job_search_router: {routes}")
    return {
        "routes": routes,
        "prefix": router.prefix,
        "tags": router.tags
    } 