from pathlib import Path
import json
from loguru import logger
from roboco.core.task_manager import TaskManager
from roboco.core.fs import ProjectFS
from roboco.utils.id_generator import generate_short_id
from roboco.db.service import get_tasks_by_project, get_task

# Get a logger instance with the module name
logger = logger.bind(module=__name__)

async def main():
    # Set up project directory
    project_id = generate_short_id()
    
    # Initialize filesystem and task manager
    logger.info(f"Initializing project filesystem for: {project_id}")
    fs = ProjectFS(project_id=project_id)
    task_manager = TaskManager(fs=fs)
    logger.info("Initialized TaskManager")
    
    # Load tasks from the database for this project
    logger.info(f"Loading tasks from database for project: {project_id}")
    tasks = get_tasks_by_project(project_id)
    
    if not tasks:
        logger.error(f"No tasks found in database for project {project_id}")
        return
    
    logger.info(f"Found {len(tasks)} tasks in database")
    
    # Get the first task
    first_task = tasks[0]
    logger.info(f"First task: {first_task.title}")
    
    # Execute the first task using the TaskManager
    logger.info(f"Executing task: {first_task.title}")
    result = await task_manager.execute_task(first_task, tasks)
    
    # Print the execution result
    formatted_result = {
        "task": first_task.title,
        "status": result.get("status", "completed"),
    }
    
    if "response" in result:
        response = result["response"]
        if hasattr(response, "summary"):
            formatted_result["summary"] = str(response.summary)
    
    print(json.dumps(formatted_result, indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
