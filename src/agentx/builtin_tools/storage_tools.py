"""
Storage Tools - Clean LLM-facing tools that use the storage layer.

These tools provide a clean interface for LLM agents to interact with storage
without directly manipulating the filesystem.
"""

from typing import Annotated, Optional, Dict, Any
from ..tool.models import Tool, tool, ToolResult
from ..storage.factory import StorageFactory, WorkspaceStorage
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StorageTool(Tool):
    """Storage tools that use the storage layer for clean file operations."""
    
    def __init__(self, workspace_storage: WorkspaceStorage):
        super().__init__()
        self.workspace = workspace_storage
        logger.info(f"StorageTool initialized with workspace: {self.workspace.get_workspace_path()}")
    
    @tool(description="Read the contents of a file")
    async def read_file(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Path to the file to read (relative to workspace)"]
    ) -> str:
        """Read file contents safely within workspace."""
        try:
            content = await self.workspace.file_storage.read_text(path)
            logger.info(f"Read file: {path}")
            return f"📄 Contents of {path}:\n\n{content}"
            
        except FileNotFoundError:
            return f"❌ File not found: {path}"
        except IsADirectoryError:
            return f"❌ Path is not a file: {path}"
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"
    
    @tool(description="Write content to a file")
    async def write_file(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Path to the file to write (relative to workspace)"],
        content: Annotated[str, "Content to write to the file"]
    ) -> str:
        """Write content to file safely within workspace."""
        try:
            result = await self.workspace.file_storage.write_text(path, content)
            
            if result.success:
                logger.info(f"Wrote file: {path}")
                return f"✅ Successfully wrote {len(content)} characters ({result.size} bytes) to {path}"
            else:
                return f"❌ Failed to write file: {result.error}"
                
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error writing file: {str(e)}"
    
    @tool(description="Append content to a file")
    async def append_file(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Path to the file to append to (relative to workspace)"],
        content: Annotated[str, "Content to append to the file"]
    ) -> str:
        """Append content to file safely within workspace."""
        try:
            result = await self.workspace.file_storage.append_text(path, content)
            
            if result.success:
                logger.info(f"Appended to file: {path}")
                return f"✅ Successfully appended {len(content)} characters to {path} (total size: {result.size} bytes)"
            else:
                return f"❌ Failed to append to file: {result.error}"
                
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error appending to file: {str(e)}"
    
    @tool(description="List the contents of a directory")
    async def list_directory(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Directory path to list (relative to workspace)"] = "."
    ) -> str:
        """List directory contents safely within workspace."""
        try:
            files = await self.workspace.file_storage.list_directory(path)
            
            if not files:
                return f"📂 Directory {path} is empty"
            
            items = []
            for file_info in files:
                if file_info.path.endswith('/') or '/' not in file_info.path:
                    # It's a directory or file in current directory
                    if file_info.size == 0 and file_info.path.endswith('/'):
                        items.append(f"📁 {file_info.path}")
                    else:
                        items.append(f"📄 {file_info.path} ({file_info.size} bytes)")
            
            logger.info(f"Listed directory: {path}")
            return f"📂 Contents of {path}:\n\n" + "\n".join(items)
            
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error listing directory: {str(e)}"
    
    @tool(description="Check if a file or directory exists")
    async def file_exists(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Path to check (relative to workspace)"]
    ) -> str:
        """Check if a file or directory exists within workspace."""
        try:
            exists = await self.workspace.file_storage.exists(path)
            
            if exists:
                info = await self.workspace.file_storage.get_info(path)
                if info:
                    logger.info(f"Path exists: {path}")
                    return f"✅ Path exists: {path} ({info.size} bytes, modified: {info.modified_at.strftime('%Y-%m-%d %H:%M:%S')})"
                else:
                    logger.info(f"Path exists: {path}")
                    return f"✅ Path exists: {path}"
            else:
                return f"❌ Path does not exist: {path}"
                
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error checking path: {str(e)}"
    
    @tool(description="Create a directory")
    async def create_directory(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Directory path to create (relative to workspace)"]
    ) -> str:
        """Create a directory safely within workspace."""
        try:
            result = await self.workspace.file_storage.create_directory(path)
            
            if result.success:
                if result.metadata and result.metadata.get("already_exists"):
                    logger.info(f"Directory already exists: {path}")
                    return f"ℹ️ Directory already exists: {path}"
                else:
                    logger.info(f"Successfully created directory: {path}")
                    return f"✅ Successfully created directory: {path}"
            else:
                return f"❌ Failed to create directory: {result.error}"
                
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error creating directory: {str(e)}"
    
    @tool(description="Delete a file")
    async def delete_file(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Path to the file to delete (relative to workspace)"]
    ) -> str:
        """Delete a file safely within workspace."""
        try:
            result = await self.workspace.file_storage.delete(path)
            
            if result.success:
                logger.info(f"Deleted file: {path}")
                return f"✅ Successfully deleted file: {path}"
            else:
                return f"❌ Failed to delete file: {result.error}"
                
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error deleting file: {str(e)}"


class ArtifactTool(Tool):
    """Artifact management tools for versioned content storage."""
    
    def __init__(self, workspace_storage: WorkspaceStorage):
        super().__init__()
        self.workspace = workspace_storage
        logger.info(f"ArtifactTool initialized with workspace: {self.workspace.get_workspace_path()}")
    
    @tool(description="Store content as a versioned artifact")
    async def store_artifact(
        self,
        task_id: str,
        agent_id: str,
        name: Annotated[str, "Name of the artifact"],
        content: Annotated[str, "Content to store"],
        description: Annotated[str, "Description of the artifact"] = ""
    ) -> str:
        """Store content as a versioned artifact."""
        try:
            metadata = {
                "description": description,
                "created_by": agent_id,
                "task_id": task_id
            }
            
            result = await self.workspace.store_artifact(name, content, "text/plain", metadata)
            
            if result.success:
                logger.info(f"Stored artifact: {name}")
                version = result.data.get("version", "unknown")
                return f"✅ Artifact '{name}' stored successfully (version: {version}, size: {result.size} bytes)"
            else:
                return f"❌ Failed to store artifact: {result.error}"
                
        except Exception as e:
            return f"❌ Error storing artifact: {str(e)}"
    
    @tool(description="Retrieve an artifact by name")
    async def get_artifact(
        self,
        task_id: str,
        agent_id: str,
        name: Annotated[str, "Name of the artifact"],
        version: Annotated[str, "Specific version to retrieve (optional)"] = ""
    ) -> str:
        """Retrieve an artifact by name and optional version."""
        try:
            version_param = version if version else None
            content = await self.workspace.get_artifact(name, version_param)
            
            if content is not None:
                version_info = f" (version: {version})" if version else " (latest version)"
                logger.info(f"Retrieved artifact: {name}{version_info}")
                return f"📄 Artifact '{name}'{version_info}:\n\n{content}"
            else:
                return f"❌ Artifact not found: {name}"
                
        except Exception as e:
            return f"❌ Error retrieving artifact: {str(e)}"
    
    @tool(description="List all stored artifacts")
    async def list_artifacts(
        self,
        task_id: str,
        agent_id: str
    ) -> str:
        """List all stored artifacts with their metadata."""
        try:
            artifacts = await self.workspace.list_artifacts()
            
            if not artifacts:
                return "📂 No artifacts found in workspace"
            
            items = []
            for artifact in artifacts:
                name = artifact.get("name", "unknown")
                version = artifact.get("version", "unknown")
                size = artifact.get("size", 0)
                created_at = artifact.get("created_at", "unknown")
                description = artifact.get("metadata", {}).get("description", "")
                
                item = f"📄 {name} (v{version}, {size} bytes, {created_at[:10]})"
                if description:
                    item += f" - {description}"
                items.append(item)
            
            logger.info("Listed artifacts")
            return f"📂 Stored artifacts ({len(artifacts)} total):\n\n" + "\n".join(items)
            
        except Exception as e:
            return f"❌ Error listing artifacts: {str(e)}"
    
    @tool(description="Get all versions of an artifact")
    async def get_artifact_versions(
        self,
        task_id: str,
        agent_id: str,
        name: Annotated[str, "Name of the artifact"]
    ) -> str:
        """Get all versions of an artifact."""
        try:
            versions = await self.workspace.get_artifact_versions(name)
            
            if not versions:
                return f"❌ No versions found for artifact: {name}"
            
            logger.info(f"Retrieved versions for artifact: {name}")
            return f"📋 Versions of '{name}': {', '.join(versions)}"
            
        except Exception as e:
            return f"❌ Error getting artifact versions: {str(e)}"
    
    @tool(description="Delete an artifact or specific version")
    async def delete_artifact(
        self,
        task_id: str,
        agent_id: str,
        name: Annotated[str, "Name of the artifact"],
        version: Annotated[str, "Specific version to delete (optional, deletes all if not specified)"] = ""
    ) -> str:
        """Delete an artifact or specific version."""
        try:
            version_param = version if version else None
            result = await self.workspace.delete_artifact(name, version_param)
            
            if result.success:
                if version:
                    logger.info(f"Deleted version {version} of artifact: {name}")
                    return f"✅ Successfully deleted version {version} of artifact '{name}'"
                else:
                    logger.info(f"Deleted artifact: {name}")
                    return f"✅ Successfully deleted artifact '{name}' (all versions)"
            else:
                return f"❌ Failed to delete artifact: {result.error}"
                
        except Exception as e:
            return f"❌ Error deleting artifact: {str(e)}"


def create_storage_tools(workspace_path: str) -> tuple[StorageTool, ArtifactTool]:
    """
    Create storage tools for a workspace.
    
    Args:
        workspace_path: Path to the workspace directory
        
    Returns:
        Tuple of (StorageTool, ArtifactTool)
    """
    workspace = StorageFactory.create_workspace_storage(workspace_path)
    storage_tool = StorageTool(workspace)
    artifact_tool = ArtifactTool(workspace)
    
    logger.info(f"Created storage tools for workspace: {workspace_path}")
    return storage_tool, artifact_tool 