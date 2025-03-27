from pathlib import Path
import json
from autogen import ChatResult
from loguru import logger
from roboco.core.task_manager import TaskManager
from roboco.core.project_fs import ProjectFS
from roboco.core.task_executor import TaskExecutor

async def main():
    # Set up project directory
    project_name = "simple_calculator_app"
    project_dir = Path(project_name)
    
    # Initialize filesystem and task manager
    logger.info(f"Initializing project filesystem for: {project_dir}")
    fs = ProjectFS(project_dir=str(project_dir))
    task_manager = TaskManager(fs=fs)
    
    # Initialize task executor with task manager
    task_executor = TaskExecutor(fs=fs, task_manager=task_manager)
    logger.info("Initialized TaskExecutor")
    
    # First, check if tasks.md exists in the project directory
    tasks_file = "tasks.md"
    
    # If tasks.md doesn't exist, we need to create the project repository first
    if not fs.exists_sync(tasks_file):
        logger.info("tasks.md doesn't exist.")
        return
    
    # Now load the tasks.md file from the project directory
    logger.info("Loading tasks from tasks.md")
    phases = task_manager.load(tasks_file)
    
    if not phases:
        logger.error("No phases found in tasks.md")
        return
    
    logger.info(f"Found {len(phases)} phases in tasks.md")
    
    # Get the first task from the first phase (Project Initialization)
    first_phase = phases[0]
    logger.info(f"First phase: {first_phase.name}")
    
    if not first_phase.tasks:
        logger.error(f"No tasks found in {first_phase.name} phase")
        return
    
    # Get the first task
    first_task = first_phase.tasks[0]
    logger.info(f"First task: {first_task.description}")
    
    # Execute the first task using the TaskExecutor
    logger.info(f"Executing task: {first_task.description}")
    result = await task_executor.execute_task(first_task, phases)
    
    # Print the execution result
    formatted_result = {
        "task": first_task.description,
        "status": result.get("status", "completed"),
    }
    
    if "response" in result:
        response = ChatResult(**result["response"])
        if hasattr(response, "summary"):
            formatted_result["summary"] = str(response.summary)
    
    print(json.dumps(formatted_result, indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
