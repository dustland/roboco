"""
Storage backend implementations.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import aiofiles
import aiofiles.os

from .interfaces import FileStorage, ArtifactStorage, StorageResult, FileInfo
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LocalFileStorage(FileStorage):
    """Local filesystem storage backend with security constraints."""
    
    def __init__(self, base_path: Union[str, Path]):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalFileStorage initialized: {self.base_path}")
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base path and validate security."""
        target_path = (self.base_path / path).resolve()
        
        # Security check: ensure path is within base directory
        try:
            target_path.relative_to(self.base_path)
        except ValueError:
            raise PermissionError(f"Access denied: Path '{path}' is outside storage area")
        
        return target_path
    
    async def exists(self, path: str) -> bool:
        """Check if a path exists."""
        try:
            file_path = self._resolve_path(path)
            return await aiofiles.os.path.exists(file_path)
        except Exception:
            return False
    
    async def get_info(self, path: str) -> Optional[FileInfo]:
        """Get information about a file/directory."""
        try:
            file_path = self._resolve_path(path)
            
            if not await aiofiles.os.path.exists(file_path):
                return None
            
            stat = await aiofiles.os.stat(file_path)
            
            return FileInfo(
                path=path,
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime)
            )
        except Exception as e:
            logger.error(f"Failed to get info for {path}: {e}")
            return None
    
    async def list_directory(self, path: str = ".") -> List[FileInfo]:
        """List contents of a directory."""
        try:
            dir_path = self._resolve_path(path)
            
            if not await aiofiles.os.path.exists(dir_path):
                return []
            
            if not await aiofiles.os.path.isdir(dir_path):
                return []
            
            items = []
            for entry in dir_path.iterdir():
                try:
                    stat = entry.stat()
                    relative_path = entry.relative_to(self.base_path)
                    
                    items.append(FileInfo(
                        path=str(relative_path),
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        modified_at=datetime.fromtimestamp(stat.st_mtime)
                    ))
                except Exception as e:
                    logger.warning(f"Failed to get info for {entry}: {e}")
                    continue
            
            return sorted(items, key=lambda x: x.path)
            
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
            return []
    
    async def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text content from a file."""
        file_path = self._resolve_path(path)
        
        if not await aiofiles.os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        if not await aiofiles.os.path.isfile(file_path):
            raise IsADirectoryError(f"Path is not a file: {path}")
        
        try:
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                return await f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 encoding
            async with aiofiles.open(file_path, 'r', encoding='latin-1') as f:
                return await f.read()
    
    async def write_text(self, path: str, content: str, encoding: str = "utf-8") -> StorageResult:
        """Write text content to a file."""
        try:
            file_path = self._resolve_path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
                await f.write(content)
            
            stat = await aiofiles.os.stat(file_path)
            
            return StorageResult(
                success=True,
                path=path,
                size=stat.st_size,
                metadata={"encoding": encoding}
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def read_bytes(self, path: str) -> bytes:
        """Read binary content from a file."""
        file_path = self._resolve_path(path)
        
        if not await aiofiles.os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def write_bytes(self, path: str, content: bytes) -> StorageResult:
        """Write binary content to a file."""
        try:
            file_path = self._resolve_path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            stat = await aiofiles.os.stat(file_path)
            
            return StorageResult(
                success=True,
                path=path,
                size=stat.st_size,
                metadata={"content_type": "application/octet-stream"}
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def append_text(self, path: str, content: str, encoding: str = "utf-8") -> StorageResult:
        """Append text content to a file."""
        try:
            file_path = self._resolve_path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'a', encoding=encoding) as f:
                await f.write(content)
            
            stat = await aiofiles.os.stat(file_path)
            
            return StorageResult(
                success=True,
                path=path,
                size=stat.st_size,
                metadata={"encoding": encoding, "operation": "append"}
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def delete(self, path: str) -> StorageResult:
        """Delete a file."""
        try:
            file_path = self._resolve_path(path)
            
            if not await aiofiles.os.path.exists(file_path):
                return StorageResult(
                    success=False,
                    error=f"File not found: {path}"
                )
            
            if not await aiofiles.os.path.isfile(file_path):
                return StorageResult(
                    success=False,
                    error=f"Path is not a file: {path}"
                )
            
            await aiofiles.os.remove(file_path)
            
            return StorageResult(
                success=True,
                path=path,
                metadata={"operation": "delete"}
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def create_directory(self, path: str) -> StorageResult:
        """Create a directory."""
        try:
            dir_path = self._resolve_path(path)
            
            if await aiofiles.os.path.exists(dir_path):
                if await aiofiles.os.path.isdir(dir_path):
                    return StorageResult(
                        success=True,
                        path=path,
                        metadata={"operation": "create_directory", "already_exists": True}
                    )
                else:
                    return StorageResult(
                        success=False,
                        error=f"Path exists but is not a directory: {path}"
                    )
            
            # Create directory and any necessary parent directories
            dir_path.mkdir(parents=True, exist_ok=True)
            
            return StorageResult(
                success=True,
                path=path,
                metadata={"operation": "create_directory"}
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                error=str(e)
            )
 