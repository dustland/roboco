from pydantic import BaseModel
from typing import Any, Dict, List

class TaskRequest(BaseModel):
    """Request model for submitting a task to the workflow."""
    task: str
    
class TaskResponse(BaseModel):
    """Response model for the result of a workflow task."""
    summary: str
    chat_history: List[Dict[str, Any]]
    cost: float
