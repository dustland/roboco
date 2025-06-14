"""
Tests for basic tools functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from roboco.tools.basic_tools import BasicTool


class TestBasicTool:
    """Test BasicTool class."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def basic_tool(self, temp_workspace):
        """Create a BasicTool instance with temporary workspace."""
        return BasicTool(workspace_path=str(temp_workspace))
    
    def test_basic_tool_initialization(self, temp_workspace):
        """Test BasicTool initialization."""
        tool = BasicTool(workspace_path=str(temp_workspace))
        
        assert tool.workspace_path == temp_workspace.resolve()
        assert tool.workspace_path.exists()
        assert tool.workspace_path.is_dir()
    
    def test_basic_tool_initialization_creates_workspace(self):
        """Test BasicTool creates workspace if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir) / "new_workspace"
            assert not workspace_path.exists()
            
            tool = BasicTool(workspace_path=str(workspace_path))
            
            assert tool.workspace_path.exists()
            assert tool.workspace_path.is_dir()
    
    def test_resolve_path_valid(self, basic_tool):
        """Test resolving valid paths within workspace."""
        # Test relative path
        resolved = basic_tool._resolve_path("test.txt")
        expected = basic_tool.workspace_path / "test.txt"
        assert resolved == expected.resolve()
        
        # Test subdirectory path
        resolved = basic_tool._resolve_path("subdir/file.txt")
        expected = basic_tool.workspace_path / "subdir" / "file.txt"
        assert resolved == expected.resolve()
    
    def test_resolve_path_security_violation(self, basic_tool):
        """Test security check prevents access outside workspace."""
        # Test parent directory access
        with pytest.raises(PermissionError, match="outside workspace"):
            basic_tool._resolve_path("../outside.txt")
        
        # Test absolute path outside workspace
        with pytest.raises(PermissionError, match="outside workspace"):
            basic_tool._resolve_path("/etc/passwd")
        
        # Test symlink-like traversal
        with pytest.raises(PermissionError, match="outside workspace"):
            basic_tool._resolve_path("../../etc/passwd")
    
    @pytest.mark.asyncio
    async def test_echo_message_basic(self, basic_tool):
        """Test basic echo message functionality."""
        result = await basic_tool.echo_message("task1", "agent1", "Hello World")
        assert result == "Hello World"
    
    @pytest.mark.asyncio
    async def test_echo_message_with_prefix(self, basic_tool):
        """Test echo message with prefix."""
        result = await basic_tool.echo_message("task1", "agent1", "Hello World", "INFO")
        assert result == "INFO: Hello World"
    
    @pytest.mark.asyncio
    async def test_echo_message_empty_prefix(self, basic_tool):
        """Test echo message with empty prefix."""
        result = await basic_tool.echo_message("task1", "agent1", "Hello World", "")
        assert result == "Hello World"
    
    @pytest.mark.asyncio
    async def test_write_and_read_file(self, basic_tool):
        """Test writing and reading a file."""
        content = "This is test content\nWith multiple lines"
        
        # Write file
        write_result = await basic_tool.write_file("task1", "agent1", "test.txt", content)
        assert "✅ Successfully wrote" in write_result
        assert "test.txt" in write_result
        
        # Read file
        read_result = await basic_tool.read_file("task1", "agent1", "test.txt")
        assert "📄 Contents of test.txt:" in read_result
        assert content in read_result
    
    @pytest.mark.asyncio
    async def test_write_file_creates_directories(self, basic_tool):
        """Test writing file creates parent directories."""
        content = "Test content"
        
        write_result = await basic_tool.write_file("task1", "agent1", "subdir/nested/file.txt", content)
        assert "✅ Successfully wrote" in write_result
        
        # Verify directory structure was created
        file_path = basic_tool.workspace_path / "subdir" / "nested" / "file.txt"
        assert file_path.exists()
        assert file_path.read_text() == content
    
    @pytest.mark.asyncio
    async def test_read_file_not_found(self, basic_tool):
        """Test reading non-existent file."""
        result = await basic_tool.read_file("task1", "agent1", "nonexistent.txt")
        assert "❌ File not found: nonexistent.txt" in result
    
    @pytest.mark.asyncio
    async def test_read_file_is_directory(self, basic_tool):
        """Test reading a directory instead of file."""
        # Create a directory
        dir_path = basic_tool.workspace_path / "testdir"
        dir_path.mkdir()
        
        result = await basic_tool.read_file("task1", "agent1", "testdir")
        assert "❌ Path is not a file: testdir" in result
    
    @pytest.mark.asyncio
    async def test_read_file_encoding_fallback(self, basic_tool):
        """Test reading file with encoding fallback."""
        # Create file with non-UTF-8 content
        file_path = basic_tool.workspace_path / "binary.txt"
        file_path.write_bytes(b'\xff\xfe\x00\x00')  # Invalid UTF-8
        
        with patch.object(Path, 'read_text') as mock_read:
            # First call (UTF-8) raises UnicodeDecodeError
            # Second call (latin-1) succeeds
            mock_read.side_effect = [UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid'), "decoded content"]
            
            result = await basic_tool.read_file("task1", "agent1", "binary.txt")
            assert "📄 Contents of binary.txt:" in result
            assert "decoded content" in result
            
            # Verify both encodings were tried
            assert mock_read.call_count == 2
            calls = mock_read.call_args_list
            assert calls[0][1]['encoding'] == 'utf-8'
            assert calls[1][1]['encoding'] == 'latin-1'
    
    @pytest.mark.asyncio
    async def test_list_directory_empty(self, basic_tool):
        """Test listing empty directory."""
        result = await basic_tool.list_directory("task1", "agent1", ".")
        assert "📂 Directory . is empty" in result
    
    @pytest.mark.asyncio
    async def test_list_directory_with_files(self, basic_tool):
        """Test listing directory with files."""
        # Create test files and directories
        (basic_tool.workspace_path / "file1.txt").write_text("content1")
        (basic_tool.workspace_path / "file2.txt").write_text("content2")
        (basic_tool.workspace_path / "subdir").mkdir()
        
        result = await basic_tool.list_directory("task1", "agent1", ".")
        
        assert "📂 Contents of .:" in result
        assert "📄 file1.txt" in result
        assert "📄 file2.txt" in result
        assert "📁 subdir/" in result
    
    @pytest.mark.asyncio
    async def test_list_directory_not_found(self, basic_tool):
        """Test listing non-existent directory."""
        result = await basic_tool.list_directory("task1", "agent1", "nonexistent")
        assert "❌ Directory not found: nonexistent" in result
    
    @pytest.mark.asyncio
    async def test_list_directory_is_file(self, basic_tool):
        """Test listing a file instead of directory."""
        # Create a file
        (basic_tool.workspace_path / "test.txt").write_text("content")
        
        result = await basic_tool.list_directory("task1", "agent1", "test.txt")
        assert "❌ Path is not a directory: test.txt" in result
    
    @pytest.mark.asyncio
    async def test_file_exists_file(self, basic_tool):
        """Test checking if file exists."""
        # Create test file
        test_file = basic_tool.workspace_path / "test.txt"
        test_file.write_text("content")
        
        result = await basic_tool.file_exists("task1", "agent1", "test.txt")
        assert "✅ File exists: test.txt" in result
        assert "bytes)" in result
    
    @pytest.mark.asyncio
    async def test_file_exists_directory(self, basic_tool):
        """Test checking if directory exists."""
        # Create test directory with some files
        test_dir = basic_tool.workspace_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content")
        (test_dir / "file2.txt").write_text("content")
        
        result = await basic_tool.file_exists("task1", "agent1", "testdir")
        assert "✅ Directory exists: testdir" in result
        assert "(2 items)" in result
    
    @pytest.mark.asyncio
    async def test_file_exists_not_found(self, basic_tool):
        """Test checking non-existent path."""
        result = await basic_tool.file_exists("task1", "agent1", "nonexistent")
        assert "❌ Path does not exist: nonexistent" in result
    
    @pytest.mark.asyncio
    async def test_create_directory_new(self, basic_tool):
        """Test creating new directory."""
        result = await basic_tool.create_directory("task1", "agent1", "newdir")
        assert "✅ Successfully created directory: newdir" in result
        
        # Verify directory was created
        dir_path = basic_tool.workspace_path / "newdir"
        assert dir_path.exists()
        assert dir_path.is_dir()
    
    @pytest.mark.asyncio
    async def test_create_directory_nested(self, basic_tool):
        """Test creating nested directory structure."""
        result = await basic_tool.create_directory("task1", "agent1", "parent/child/grandchild")
        assert "✅ Successfully created directory: parent/child/grandchild" in result
        
        # Verify nested structure was created
        dir_path = basic_tool.workspace_path / "parent" / "child" / "grandchild"
        assert dir_path.exists()
        assert dir_path.is_dir()
    
    @pytest.mark.asyncio
    async def test_create_directory_already_exists(self, basic_tool):
        """Test creating directory that already exists."""
        # Create directory first
        dir_path = basic_tool.workspace_path / "existing"
        dir_path.mkdir()
        
        result = await basic_tool.create_directory("task1", "agent1", "existing")
        assert "ℹ️ Directory already exists: existing" in result
    
    @pytest.mark.asyncio
    async def test_create_directory_file_exists(self, basic_tool):
        """Test creating directory where file exists."""
        # Create file first
        file_path = basic_tool.workspace_path / "existing.txt"
        file_path.write_text("content")
        
        result = await basic_tool.create_directory("task1", "agent1", "existing.txt")
        assert "❌ Path exists but is not a directory: existing.txt" in result
    
    @pytest.mark.asyncio
    async def test_security_violations_in_tools(self, basic_tool):
        """Test security violations are caught in tool methods."""
        # Test read_file with path traversal
        result = await basic_tool.read_file("task1", "agent1", "../outside.txt")
        assert "❌ Permission denied:" in result
        assert "outside workspace" in result
        
        # Test write_file with path traversal
        result = await basic_tool.write_file("task1", "agent1", "../outside.txt", "content")
        assert "❌ Permission denied:" in result
        assert "outside workspace" in result
        
        # Test list_directory with path traversal
        result = await basic_tool.list_directory("task1", "agent1", "../")
        assert "❌ Permission denied:" in result
        assert "outside workspace" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_in_tools(self, basic_tool):
        """Test error handling in tool methods."""
        # Mock file operations to raise exceptions
        with patch('pathlib.Path.read_text', side_effect=OSError("Disk error")):
            result = await basic_tool.read_file("task1", "agent1", "test.txt")
            assert "❌ Error reading file: Disk error" in result
        
        with patch('pathlib.Path.write_text', side_effect=OSError("Disk full")):
            result = await basic_tool.write_file("task1", "agent1", "test.txt", "content")
            assert "❌ Error writing file: Disk full" in result
        
        with patch('pathlib.Path.iterdir', side_effect=OSError("Access denied")):
            result = await basic_tool.list_directory("task1", "agent1", ".")
            assert "❌ Error listing directory: Access denied" in result 