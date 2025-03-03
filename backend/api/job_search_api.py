from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import subprocess
import os
import csv
import asyncio
import logging
import traceback
from typing import Dict, List
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["job-search"],
    responses={404: {"description": "Not found"}},
)

# Store background tasks and their status
job_searches: Dict[str, dict] = {}

async def run_job_search(cv_path: str, task_id: str):
    try:
        logger.info(f"Starting job search with CV: {cv_path}")
        
        # Create process with pipe for real-time output
        process = await asyncio.create_subprocess_exec(
            "python", 
            "backend/job-search.py",
            "--cv", cv_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={
                **os.environ,
                "PYTHONUNBUFFERED": "1"
            }
        )
        
        # Handle output streams asynchronously
        async def read_stream(stream, is_error: bool):
            while True:
                line = await stream.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                if line_str:
                    # Update logs in real-time
                    current_logs = job_searches[task_id].get("logs", "")
                    prefix = "ERROR: " if is_error else "INFO: "
                    job_searches[task_id]["logs"] = current_logs + prefix + line_str + "\n"
                    if is_error:
                        logger.error(line_str)
                    else:
                        logger.info(line_str)

        # Create tasks for reading stdout and stderr
        stdout_task = asyncio.create_task(read_stream(process.stdout, False))
        stderr_task = asyncio.create_task(read_stream(process.stderr, True))
        
        try:
            # Wait for process to complete with timeout
            await asyncio.wait_for(process.wait(), timeout=300.0)  # 5 minute timeout
            
            # Wait for output reading to complete
            await stdout_task
            await stderr_task
            
            # Update final status
            if process.returncode == 0:
                job_searches[task_id]["status"] = "completed"
                logger.info(f"Job search completed for task {task_id}")
            else:
                job_searches[task_id]["status"] = "failed"
                job_searches[task_id]["error"] = f"Process failed with code {process.returncode}"
                logger.error(f"Job search failed for task {task_id}")
                
        except asyncio.TimeoutError:
            # Kill the process if it times out
            try:
                process.kill()
                stdout_task.cancel()
                stderr_task.cancel()
            except:
                pass
            job_searches[task_id]["status"] = "failed"
            job_searches[task_id]["error"] = "Job search timed out after 5 minutes"
            logger.error(f"Job search timed out for task {task_id}")
            
    except Exception as e:
        job_searches[task_id]["status"] = "failed"
        job_searches[task_id]["error"] = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
        logger.error(f"Error in job search task {task_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

class JobSearchRequest(BaseModel):
    cv_path: str

@router.post("/search")
async def start_job_search(
    request: JobSearchRequest,
    background_tasks: BackgroundTasks
):
    try:
        logger.info(f"Starting job search with CV: {request.cv_path}")
        
        if not os.path.exists(request.cv_path):
            raise HTTPException(status_code=400, detail=f"CV file not found at {request.cv_path}")
        
        # Generate unique task ID
        task_id = os.urandom(8).hex()
        logger.info(f"Generated task ID: {task_id}")
        
        # Initialize task status
        job_searches[task_id] = {
            "status": "running",
            "cv_path": request.cv_path,
            "logs": "",
            "error": None
        }
        
        # Start background task
        background_tasks.add_task(run_job_search, request.cv_path, task_id)
        logger.info(f"Started background task for {task_id}")
        
        return {
            "task_id": task_id, 
            "status": "started",
            "message": f"Started job search with CV: {request.cv_path}"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        error_msg = f"Error starting job search: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{task_id}")
async def get_job_search_status(task_id: str):
    logger.info(f"Checking status for task {task_id}")
    
    if task_id not in job_searches:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
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
            logger.error(f"Error reading CSV: {str(e)}")
    
    return {
        "status": task_info["status"],
        "error": task_info.get("error"),
        "logs": task_info.get("logs", ""),
        "cv_path": task_info["cv_path"],
        "jobs": jobs if jobs else None
    } 