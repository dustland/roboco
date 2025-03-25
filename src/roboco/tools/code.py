"""
Code Tool Module

This module provides tools for code generation, validation, and execution
across multiple programming languages.
"""

import os
import sys
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Union, Any
from roboco.core.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

from roboco.core.tool import Tool, command


class CodeTool(Tool):
    """
    Tool for generating, validating, and executing code in multiple languages.
    
    This tool provides functionality to generate code, validate that it compiles,
    and execute it when needed. It supports multiple programming languages.
    """
    
    def __init__(
        self, 
        workspace_dir: str = "workspace", 
        name: str = "code", 
        description: str = "Generate, validate, and execute code in multiple languages"
    ):
        """
        Initialize the CodeTool.
        
        Args:
            workspace_dir: Directory to use for code files
            name: Name of the tool
            description: Description of the tool
        """
        super().__init__(name=name, description=description)
        self.workspace_dir = workspace_dir
        
        # Ensure workspace directory exists
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Dictionary of supported languages and their compilers/interpreters
        self.language_configs = {
            "python": {
                "extension": ".py",
                "compile_cmd": ["python", "-m", "py_compile"],
                "run_cmd": ["python"],
                "version_cmd": ["python", "--version"],
                "requires_compilation": False
            },
            "javascript": {
                "extension": ".js",
                "compile_cmd": ["node", "--check"],
                "run_cmd": ["node"],
                "version_cmd": ["node", "--version"],
                "requires_compilation": False
            },
            "typescript": {
                "extension": ".ts",
                "compile_cmd": ["tsc", "--noEmit"],
                "run_cmd": ["ts-node"],
                "version_cmd": ["tsc", "--version"],
                "requires_compilation": True
            },
            "java": {
                "extension": ".java",
                "compile_cmd": ["javac"],
                "run_cmd": ["java"],
                "version_cmd": ["java", "--version"],
                "requires_compilation": True
            },
            "c": {
                "extension": ".c",
                "compile_cmd": ["gcc", "-o"],
                "run_cmd": [],  # Filled in during compilation
                "version_cmd": ["gcc", "--version"],
                "requires_compilation": True
            },
            "cpp": {
                "extension": ".cpp",
                "compile_cmd": ["g++", "-o"],
                "run_cmd": [],  # Filled in during compilation
                "version_cmd": ["g++", "--version"],
                "requires_compilation": True
            },
            "go": {
                "extension": ".go",
                "compile_cmd": ["go", "build"],
                "run_cmd": ["go", "run"],
                "version_cmd": ["go", "version"],
                "requires_compilation": True
            },
            "rust": {
                "extension": ".rs",
                "compile_cmd": ["rustc"],
                "run_cmd": [],  # Filled in during compilation
                "version_cmd": ["rustc", "--version"],
                "requires_compilation": True
            },
            "shell": {
                "extension": ".sh",
                "compile_cmd": ["sh", "-n"],
                "run_cmd": ["sh"],
                "version_cmd": ["sh", "--version"],
                "requires_compilation": False
            }
        }
        
        # Check which languages are actually available
        self.available_languages = self._check_available_languages()
        
        logger.info(f"CodeTool initialized with {len(self.available_languages)} available languages")
        logger.debug(f"Available languages: {', '.join(self.available_languages)}")
    
    def _check_available_languages(self) -> List[str]:
        """
        Check which languages are available on the system.
        
        Returns:
            List of available language names
        """
        available = []
        
        for lang, config in self.language_configs.items():
            try:
                # Try to run the version command
                result = subprocess.run(
                    config["version_cmd"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                
                if result.returncode == 0:
                    available.append(lang)
            except (subprocess.SubprocessError, FileNotFoundError):
                # Language is not available
                continue
        
        return available
    
    @command
    def generate_code(self, language: str, code: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a code file in the specified language.
        
        Args:
            language: Programming language to use
            code: The actual code content
            filename: Optional filename (will be generated if not provided)
            
        Returns:
            Dictionary with file path and status
        """
        language = language.lower()
        
        # Validate language
        if language not in self.language_configs:
            return {
                "success": False,
                "error": f"Unsupported language: {language}. Supported languages are: {', '.join(self.language_configs.keys())}"
            }
        
        # Get file extension for this language
        extension = self.language_configs[language]["extension"]
        
        # Generate filename if not provided
        if not filename:
            import uuid
            filename = f"generated_{uuid.uuid4().hex[:8]}{extension}"
        elif not filename.endswith(extension):
            filename = f"{filename}{extension}"
        
        # Full path to save the file
        file_path = os.path.join(self.workspace_dir, filename)
        
        try:
            # Write code to file
            with open(file_path, "w") as f:
                f.write(code)
            
            logger.info(f"Generated code saved to {file_path}")
            
            return {
                "success": True,
                "file_path": file_path,
                "language": language,
                "message": f"Code successfully saved to {file_path}"
            }
        except Exception as e:
            logger.error(f"Error generating code file: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate code file: {str(e)}"
            }
    
    @command
    def validate_code(self, file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate that code compiles or passes syntax checking.
        
        Args:
            file_path: Path to the code file
            language: Optional language override (detected from file extension if not provided)
            
        Returns:
            Dictionary with validation results
        """
        # Make sure the file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # Detect language from file extension if not provided
        if not language:
            extension = os.path.splitext(file_path)[1]
            for lang, config in self.language_configs.items():
                if config["extension"] == extension:
                    language = lang
                    break
        
        if not language or language.lower() not in self.language_configs:
            return {
                "success": False,
                "error": f"Could not determine language for file: {file_path}. Please specify the language."
            }
        
        language = language.lower()
        
        # Check if language is available
        if language not in self.available_languages:
            return {
                "success": False,
                "error": f"Language {language} is not available on this system."
            }
        
        # Get the compilation command
        config = self.language_configs[language]
        
        # Skip validation for languages that don't require compilation
        if not config["requires_compilation"]:
            logger.info(f"Skipping compilation for {language}, checking syntax only")
        
        # Prepare compilation command
        compile_cmd = list(config["compile_cmd"])
        
        # Special handling for different languages
        if language == "c" or language == "cpp" or language == "rust":
            # For compiled languages, create a temp output file
            output_file = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(tempfile.gettempdir(), output_file)
            
            if language == "c" or language == "cpp":
                compile_cmd.append(output_path)
            
            compile_cmd.append(file_path)
            
            if language == "rust":
                compile_cmd.append("-o")
                compile_cmd.append(output_path)
        else:
            # For other languages, just add the file path
            compile_cmd.append(file_path)
        
        try:
            # Run compilation/validation
            logger.info(f"Validating {language} code: {' '.join(compile_cmd)}")
            
            result = subprocess.run(
                compile_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "language": language,
                    "message": f"Code validation successful for {file_path}"
                }
            else:
                return {
                    "success": False,
                    "language": language,
                    "error": f"Code validation failed: {result.stderr}",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Validation timed out after 30 seconds"
            }
        except Exception as e:
            logger.error(f"Error during code validation: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to validate code: {str(e)}"
            }
    
    @command
    def fix_code(self, file_path: str, language: Optional[str] = None, error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempt to fix code that failed validation.
        
        Args:
            file_path: Path to the code file
            language: Optional language override (detected from file extension if not provided)
            error_message: Optional error message from previous validation attempt
            
        Returns:
            Dictionary with fix results
        """
        # Make sure the file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # Read current code
        try:
            with open(file_path, "r") as f:
                current_code = f.read()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}"
            }
        
        # Detect language from file extension if not provided
        if not language:
            extension = os.path.splitext(file_path)[1]
            for lang, config in self.language_configs.items():
                if config["extension"] == extension:
                    language = lang
                    break
        
        if not language:
            return {
                "success": False,
                "error": f"Could not determine language for file: {file_path}. Please specify the language."
            }
        
        language = language.lower()
        
        # Format error message for fixing guidance
        fix_guidance = ""
        if error_message:
            fix_guidance = f"The code has the following errors:\n{error_message}\n\nPlease fix these issues."
        else:
            fix_guidance = "The code failed to compile. Please review it for any syntax or semantic errors."
        
        # The actual fixing is done by the agent using this tool through:
        # 1. Analyzing the current code
        # 2. Understanding the error message
        # 3. Applying a fix
        # 4. Testing the fixed code
        
        # Return the current code and guidance for the agent to make the fix
        return {
            "success": True,
            "language": language,
            "current_code": current_code,
            "guidance": fix_guidance,
            "file_path": file_path,
            "message": "The agent should analyze the code and error message, then generate a fixed version using the generate_code command."
        }
    
    @command
    def run_code(self, file_path: str, language: Optional[str] = None, args: List[str] = None) -> Dict[str, Any]:
        """
        Run code file and return the results.
        
        Args:
            file_path: Path to the code file
            language: Optional language override (detected from file extension if not provided)
            args: Optional list of command line arguments
            
        Returns:
            Dictionary with execution results
        """
        # Make sure the file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # Detect language from file extension if not provided
        if not language:
            extension = os.path.splitext(file_path)[1]
            for lang, config in self.language_configs.items():
                if config["extension"] == extension:
                    language = lang
                    break
        
        if not language or language.lower() not in self.language_configs:
            return {
                "success": False,
                "error": f"Could not determine language for file: {file_path}. Please specify the language."
            }
        
        language = language.lower()
        
        # Check if language is available
        if language not in self.available_languages:
            return {
                "success": False,
                "error": f"Language {language} is not available on this system."
            }
        
        config = self.language_configs[language]
        args = args or []
        
        # For compiled languages that need to be compiled first
        if config["requires_compilation"] and (language == "c" or language == "cpp" or language == "rust"):
            # Compile first
            validation_result = self.validate_code(file_path, language)
            
            if not validation_result["success"]:
                return {
                    "success": False,
                    "error": f"Cannot run code that failed validation: {validation_result.get('error', 'Unknown error')}"
                }
            
            # For compiled languages, create the executable path
            output_file = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(tempfile.gettempdir(), output_file)
            
            # Run the compiled executable
            run_cmd = [output_path] + args
        else:
            # For interpreted languages, just run with the interpreter
            run_cmd = list(config["run_cmd"]) + [file_path] + args
        
        try:
            logger.info(f"Running code: {' '.join(run_cmd)}")
            
            result = subprocess.run(
                run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "language": language,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": "Code execution completed" if result.returncode == 0 else "Code execution failed"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timed out after 30 seconds"
            }
        except Exception as e:
            logger.error(f"Error running code: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to run code: {str(e)}"
            }
    
    @command
    def code_summary(self, file_path: str) -> Dict[str, Any]:
        """
        Generate a summary of a code file.
        
        Args:
            file_path: Path to the code file
            
        Returns:
            Dictionary with code summary information
        """
        # Make sure the file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        try:
            # Read the file content
            with open(file_path, "r") as f:
                content = f.read()
            
            # Get basic file information
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            
            # Count lines
            lines = content.splitlines()
            line_count = len(lines)
            non_blank_line_count = sum(1 for line in lines if line.strip())
            
            # Try to detect language from file extension
            extension = os.path.splitext(file_path)[1]
            language = None
            
            for lang, config in self.language_configs.items():
                if config["extension"] == extension:
                    language = lang
                    break
            
            return {
                "success": True,
                "file_path": file_path,
                "file_size_bytes": file_size,
                "line_count": line_count,
                "non_blank_line_count": non_blank_line_count,
                "detected_language": language,
                "message": f"Code summary generated for {file_path}"
            }
        except Exception as e:
            logger.error(f"Error generating code summary: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate code summary: {str(e)}"
            } 