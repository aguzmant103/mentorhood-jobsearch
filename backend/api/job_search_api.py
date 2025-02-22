from fastapi import APIRouter, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
import subprocess
import os
import io
import csv
from pathlib import Path
import asyncio
from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

# Store background tasks and their status
job_searches = {}

async def run_job_search(cv_path: str, task_id: str):
    try:
        # Create a temporary directory for logs
        log_file = f"job_search_{task_id}.log"
        
        # Run the job search script
        process = await asyncio.create_subprocess_exec(
            "python", 
            "backend/job-search.py",
            "--cv", cv_path,
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

@router.post("/job-search/start")
async def start_job_search(
    background_tasks: BackgroundTasks,
    cv_file: UploadFile
):
    try:
        # Generate unique task ID
        task_id = os.urandom(8).hex()
        
        # Save CV file temporarily
        cv_path = f"temp_cv_{task_id}.pdf"
        with open(cv_path, "wb") as f:
            f.write(await cv_file.read())
        
        # Initialize task status
        job_searches[task_id] = {
            "status": "running",
            "cv_path": cv_path,
            "logs": "",
            "error": None
        }
        
        # Start background task
        background_tasks.add_task(run_job_search, cv_path, task_id)
        
        return {"task_id": task_id, "status": "started"}
        
    except Exception as e:
        logger.error(f"Error starting job search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job-search/{task_id}/status")
async def get_job_search_status(task_id: str):
    if task_id not in job_searches:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "status": job_searches[task_id]["status"],
        "error": job_searches[task_id].get("error"),
        "logs": job_searches[task_id].get("logs", "")
    }

@router.get("/job-search/{task_id}/results")
async def get_job_search_results(task_id: str):
    if task_id not in job_searches:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if job_searches[task_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job search not completed")
    
    try:
        # Read CSV file
        csv_file = "jobs.csv"
        if not os.path.exists(csv_file):
            return {"jobs": []}
            
        jobs = []
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
        
        return {"jobs": jobs}
        
    except Exception as e:
        logger.error(f"Error reading results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/job-search/{task_id}")
async def cleanup_job_search(task_id: str):
    if task_id not in job_searches:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Clean up temporary files
        cv_path = job_searches[task_id]["cv_path"]
        if os.path.exists(cv_path):
            os.remove(cv_path)
            
        # Remove task from memory
        del job_searches[task_id]
        
        return {"status": "cleaned"}
        
    except Exception as e:
        logger.error(f"Error cleaning up: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 