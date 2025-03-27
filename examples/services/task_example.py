from pathlib import Path
import json
from loguru import logger
from roboco.core.task_manager import TaskManager
from roboco.core.project_fs import ProjectFS

# Get a logger instance with the module name
logger = logger.bind(module=__name__)

async def main():
    # Set up project directory
    project_name = "simple_calculator_app"
    project_dir = Path(project_name)
    
    # Initialize filesystem and task manager
    logger.info(f"Initializing project filesystem for: {project_dir}")
    fs = ProjectFS(project_dir=str(project_dir))
    task_manager = TaskManager(fs=fs)
    logger.info("Initialized TaskManager")
    
    # First, check if tasks.md exists in the project directory
    tasks_file = "tasks.md"
    
    # If tasks.md doesn't exist, we need to create the project repository first
    if not fs.exists_sync(tasks_file):
        logger.info("tasks.md doesn't exist.")
        return
    
    # Now load the tasks.md file from the project directory
    logger.info("Loading tasks from tasks.md")
    tasks = task_manager.load(tasks_file)
    
    if not tasks:
        logger.error("No tasks found in tasks.md")
        return
    
    logger.info(f"Found {len(tasks)} tasks in tasks.md")
    
    # Get the first task
    if not tasks:
        logger.error("No tasks found")
        return
    
    # Get the first task
    first_task = tasks[0]
    logger.info(f"First task: {first_task['description']}")
    
    # Execute the first task using the TaskManager
    logger.info(f"Executing task: {first_task['description']}")
    result = await task_manager.execute_task(first_task, tasks)
    
    # Print the execution result
    formatted_result = {
        "task": first_task['description'],
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
