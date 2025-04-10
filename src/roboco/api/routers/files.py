"""
Files router.

This module defines the FastAPI routes for file system operations.
It provides endpoints to list directory contents and get file content.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel
import os
from pathlib import Path as FilePath

from roboco.core.fs import ProjectFS
from roboco.api.dependencies import get_api_service
from roboco.services.api_service import ApiService
from loguru import logger

router = APIRouter(
    tags=["files"]
)

class FileInfo(BaseModel):
    """Model for file information."""
    name: str
    path: str
    type: str  # "file" or "directory"
    size: Optional[int] = None
    modified: Optional[str] = None

class FileContent(BaseModel):
    """Model for file content."""
    name: str
    path: str
    content: str
    type: str  # file extension
    size: int

class FileCreateRequest(BaseModel):
    """Model for file creation request."""
    path: str
    content: str

class DirectoryCreateRequest(BaseModel):
    """Model for directory creation request."""
    path: str

class FileResponse(BaseModel):
    """Model for file operation response."""
    path: str
    success: bool
    message: str

@router.get("/projects/{project_id}/files", response_model=List[FileInfo])
async def list_directory(
    project_id: str,
    path: str = Query("", description="Directory path relative to project root"),
    api_service: ApiService = Depends(get_api_service)
):
    """
    List directory contents for a project.
    
    Args:
        project_id: Project ID
        path: Directory path relative to project root (default: "")
        
    Returns:
        List of file information objects
    """
    try:
        # Handle empty path correctly
        if not path.strip():
            path = ""
            
        # Normalize path and ensure it doesn't escape project directory
        norm_path = os.path.normpath(path) if path else ""
        if norm_path.startswith(".."):
            raise HTTPException(status_code=400, detail="Invalid path")
            
        # Create filesystem for the project
        fs = ProjectFS(project_id=project_id)
        
        # Check if path exists
        if not fs.exists_sync(norm_path):
            # For root directory, create it if it doesn't exist
            if norm_path == "":
                fs.mkdir_sync("")
            else:
                logger.error(f"Path not found: {norm_path}")
                raise HTTPException(status_code=404, detail=f"Path not found: {norm_path}")
            
        # Check if path is a directory
        if not fs.is_dir_sync(norm_path):
            logger.error(f"Path is not a directory: {norm_path}")
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {norm_path}")
            
        # List directory contents
        items = fs.list_sync(norm_path)
        
        # Get detailed information about each item
        file_infos = []
        for item in items:
            item_path = os.path.join(norm_path, item)
            is_dir = fs.is_dir_sync(item_path)
            
            # Get file stats
            stats = None
            try:
                stats = fs.stat_sync(item_path)
            except:
                # If stat fails, still include the file but without size/modified info
                pass
                
            file_info = FileInfo(
                name=item,
                path=item_path,
                type="directory" if is_dir else "file",
                size=None if is_dir else stats.get("size") if stats else None,
                modified=stats.get("modified") if stats else None
            )
            file_infos.append(file_info)
            
        return file_infos
        
    except HTTPException as he:
        # Re-raise HTTP exceptions directly
        raise he
    except Exception as e:
        logger.error(f"Error listing directory {path} for project {project_id}: {str(e)}")
        # Include stack trace for better debugging
        import traceback
        logger.debug(f"Stack trace: {traceback.format_exc()}")
        
        # Provide a more helpful error message to the client
        error_detail = str(e)
        if "FileNotFoundError" in error_detail:
            raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
        elif "PermissionError" in error_detail:
            raise HTTPException(status_code=403, detail=f"Permission denied accessing directory: {path}")
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list directory: {error_detail}"
            )

@router.get("/projects/{project_id}/files/content", response_model=FileContent)
async def get_file_content(
    project_id: str,
    path: str = Query(..., description="File path relative to project root"),
    api_service: ApiService = Depends(get_api_service)
):
    """
    Get file content for a project.
    
    Args:
        project_id: Project ID
        path: File path relative to project root
        
    Returns:
        File content object
    """
    try:
        # Handle empty path
        if not path:
            raise HTTPException(status_code=400, detail="File path cannot be empty")
            
        # Normalize path and ensure it doesn't escape project directory
        norm_path = os.path.normpath(path)
        if norm_path.startswith(".."):
            raise HTTPException(status_code=400, detail="Invalid path")
            
        # Create filesystem for the project
        fs = ProjectFS(project_id=project_id)
        
        # Check if file exists
        if not fs.exists_sync(norm_path):
            raise HTTPException(status_code=404, detail=f"File not found: {norm_path}")
            
        # Check if path is a file
        if fs.is_dir_sync(norm_path):
            raise HTTPException(status_code=400, detail=f"Path is a directory, not a file: {norm_path}")
            
        # Read file content
        content = fs.read_sync(norm_path)
        
        # Get file stats
        stats = fs.stat_sync(norm_path)
        
        # Get file extension
        _, ext = os.path.splitext(norm_path)
        file_type = ext[1:] if ext else ""  # Remove the dot from extension
        
        return FileContent(
            name=os.path.basename(norm_path),
            path=norm_path,
            content=content,
            type=file_type,
            size=stats.get("size", 0)
        )
        
    except Exception as e:
        logger.error(f"Error reading file {path} for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )

@router.post("/projects/{project_id}/files", response_model=FileResponse)
async def create_file(
    project_id: str,
    request: FileCreateRequest,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Create or update a file in a project.
    
    Args:
        project_id: Project ID
        request: File creation request with path and content
        
    Returns:
        File operation response
    """
    try:
        # Normalize path and ensure it doesn't escape project directory
        norm_path = os.path.normpath(request.path)
        if norm_path.startswith(".."):
            raise HTTPException(status_code=400, detail="Invalid path")
            
        # Create filesystem for the project
        fs = ProjectFS(project_id=project_id)
        
        # Create parent directories if needed
        parent_dir = os.path.dirname(norm_path)
        if parent_dir and not fs.exists_sync(parent_dir):
            fs.mkdir_sync(parent_dir)
        
        # Write the file
        success = fs.write_sync(norm_path, request.content)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write file")
            
        return FileResponse(
            path=norm_path,
            success=True,
            message=f"File {norm_path} created/updated successfully"
        )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions directly
        raise he
    except Exception as e:
        logger.error(f"Error creating file {request.path} for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create file: {str(e)}"
        )

@router.post("/projects/{project_id}/directories", response_model=FileResponse)
async def create_directory(
    project_id: str,
    request: DirectoryCreateRequest,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Create a directory in a project.
    
    Args:
        project_id: Project ID
        request: Directory creation request with path
        
    Returns:
        File operation response
    """
    try:
        # Normalize path and ensure it doesn't escape project directory
        norm_path = os.path.normpath(request.path)
        if norm_path.startswith(".."):
            raise HTTPException(status_code=400, detail="Invalid path")
            
        # Create filesystem for the project
        fs = ProjectFS(project_id=project_id)
        
        # Create the directory (and parent directories if needed)
        success = fs.mkdir_sync(norm_path)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create directory")
            
        return FileResponse(
            path=norm_path,
            success=True,
            message=f"Directory {norm_path} created successfully"
        )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions directly
        raise he
    except Exception as e:
        logger.error(f"Error creating directory {request.path} for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create directory: {str(e)}"
        )

@router.post("/projects/{project_id}/ensure_root", response_model=FileResponse)
async def ensure_project_root(
    project_id: str,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Ensure that the project root directory exists.
    
    Args:
        project_id: Project ID
        
    Returns:
        File operation response
    """
    try:
        # Create filesystem for the project
        fs = ProjectFS(project_id=project_id)
        
        # Ensure root directory exists
        success = fs.mkdir_sync("")
        
        return FileResponse(
            path="/",
            success=True,
            message="Project root directory created/verified successfully"
        )
        
    except Exception as e:
        logger.error(f"Error ensuring root directory for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ensure root directory: {str(e)}"
        ) 