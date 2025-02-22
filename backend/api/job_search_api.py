from fastapi import APIRouter, HTTPException, UploadFile, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import subprocess
import os
import csv
from pathlib import Path
import asyncio
import logging
from typing import Optional, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

# Store background tasks and their status
job_searches: Dict[str, dict] = {}

async def run_job_search(companies: list[str], task_id: str):
    try:
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
        else:
            job_searches[task_id]["status"] = "failed"
            job_searches[task_id]["error"] = stderr.decode()
            
    except Exception as e:
        job_searches[task_id]["status"] = "failed"
        job_searches[task_id]["error"] = str(e)
        logger.error(f"Error in job search task {task_id}: {str(e)}")

@router.post("/test/job")
async def start_job_search(
    request: Request,
    background_tasks: BackgroundTasks
):
    try:
        # Get companies from request body
        body = await request.json()
        companies = body.get("companies", ["Google"])  # Default to Google if not specified
        
        # Generate unique task ID
        task_id = os.urandom(8).hex()
        
        # Initialize task status
        job_searches[task_id] = {
            "status": "running",
            "companies": companies,
            "logs": "",
            "error": None
        }
        
        # Start background task
        background_tasks.add_task(run_job_search, companies, task_id)
        
        return {
            "task_id": task_id, 
            "status": "started",
            "message": f"Started job search for companies: {', '.join(companies)}"
        }
        
    except Exception as e:
        logger.error(f"Error starting job search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/job/{task_id}")
async def get_job_search_status(task_id: str):
    if task_id not in job_searches:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = job_searches[task_id]
    
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
        except Exception as e:
            logger.error(f"Error reading CSV: {str(e)}")
    
    return {
        "status": task_info["status"],
        "error": task_info.get("error"),
        "logs": task_info.get("logs", ""),
        "companies": task_info["companies"],
        "jobs": jobs if jobs else None
    }

@router.delete("/test/job/{task_id}")
async def cleanup_job_search(task_id: str):
    if task_id not in job_searches:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Remove task from memory
        del job_searches[task_id]
        return {"status": "cleaned", "message": f"Task {task_id} cleaned up successfully"}
        
    except Exception as e:
        logger.error(f"Error cleaning up: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 