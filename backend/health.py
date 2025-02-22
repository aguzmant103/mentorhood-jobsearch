import os
from fastapi import APIRouter
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "8000")
    }