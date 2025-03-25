#!/usr/bin/env python3
"""
Code Tool Example

This script demonstrates how to use the CodeTool for code generation, validation,
and execution across multiple languages.
"""

import os
import sys
import asyncio
import argparse
from loguru import logger

# Add the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.tools.code import CodeTool


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(result):
    """Print the result of a CodeTool operation."""
    if result.get("success", False):
        print(f"✅ Success: {result.get('message', 'Operation completed')}")
        
        # Print additional result information if available
        for key, value in result.items():
            if key not in ["success", "message"] and value is not None:
                # For stdout/stderr, only print if not empty
                if key in ["stdout", "stderr"] and not value.strip():
                    continue
                
                # Format multiline outputs
                if isinstance(value, str) and "\n" in value:
                    print(f"\n{key.capitalize()}:")
                    print("-" * len(key))
                    print(value)
                else:
                    print(f"{key.capitalize()}: {value}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Print stdout/stderr if available and not empty
        for key in ["stdout", "stderr"]:
            if key in result and result[key] and result[key].strip():
                print(f"\n{key.capitalize()}:")
                print("-" * len(key))
                print(result[key])


def generate_python_example():
    """Generate a simple Python example."""
    print_section("Generating Python Example")
    
    code = """
def greet(name):
    return f"Hello, {name}!"

def main():
    name = input("Enter your name: ")
    greeting = greet(name)
    print(greeting)

if __name__ == "__main__":
    main()
"""
    return {
        "language": "python",
        "code": code,
        "filename": "greeting.py"
    }


def generate_javascript_example():
    """Generate a simple JavaScript example."""
    print_section("Generating JavaScript Example")
    
    code = """
function greet(name) {
    return `Hello, ${name}!`;
}

// Read name from command line arguments
const name = process.argv[2] || "World";
const greeting = greet(name);
console.log(greeting);
"""
    return {
        "language": "javascript",
        "code": code,
        "filename": "greeting.js"
    }


def generate_go_example():
    """Generate a simple Go example."""
    print_section("Generating Go Example")
    
    code = """
package main

import (
    "fmt"
    "os"
)

func greet(name string) string {
    return fmt.Sprintf("Hello, %s!", name)
}

func main() {
    name := "World"
    if len(os.Args) > 1 {
        name = os.Args[1]
    }
    
    greeting := greet(name)
    fmt.Println(greeting)
}
"""
    return {
        "language": "go",
        "code": code,
        "filename": "greeting.go"
    }


def generate_c_example():
    """Generate a simple C example."""
    print_section("Generating C Example")
    
    code = """
#include <stdio.h>
#include <string.h>

void greet(const char* name, char* buffer, size_t buffer_size) {
    snprintf(buffer, buffer_size, "Hello, %s!", name);
}

int main(int argc, char* argv[]) {
    const char* name = argc > 1 ? argv[1] : "World";
    char greeting[100];
    
    greet(name, greeting, sizeof(greeting));
    printf("%s\\n", greeting);
    
    return 0;
}
"""
    return {
        "language": "c",
        "code": code,
        "filename": "greeting.c"
    }


def generate_broken_python_example():
    """Generate a broken Python example."""
    print_section("Generating Broken Python Example")
    
    code = """
def greet(name)
    return f"Hello, {name}!"  # Missing colon after function definition

def main():
    name = input("Enter your name: ")
    greeting = greet(name)
    print(greeting

if __name__ == "__main__":
    main()
"""  # Missing closing parenthesis on print
    
    return {
        "language": "python",
        "code": code,
        "filename": "broken_greeting.py"
    }


async def main():
    """Main function to run the example."""
    parser = argparse.ArgumentParser(description="Example script for using the CodeTool")
    parser.add_argument("--workspace", "-w", default="workspace/code_examples",
                        help="Workspace directory (default: workspace/code_examples)")
    
    args = parser.parse_args()
    
    # Ensure workspace directory exists
    os.makedirs(args.workspace, exist_ok=True)
    
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(os.path.join(args.workspace, "code_tool_example.log"), level="DEBUG")
    
    print_section("Code Tool Example")
    print(f"Workspace: {os.path.abspath(args.workspace)}")
    
    # Initialize the CodeTool
    code_tool = CodeTool(workspace_dir=args.workspace)
    
    # Display available languages
    print(f"\nAvailable languages: {', '.join(code_tool.available_languages)}")
    
    # Generate, validate, and run examples for available languages
    examples = [
        ("python", generate_python_example),
        ("javascript", generate_javascript_example),
        ("go", generate_go_example),
        ("c", generate_c_example)
    ]
    
    for lang, generator in examples:
        if lang in code_tool.available_languages:
            # Generate example code
            example = generator()
            
            # Generate the code file
            result = code_tool.generate_code(
                language=example["language"],
                code=example["code"],
                filename=example["filename"]
            )
            print_result(result)
            
            if result.get("success", False):
                file_path = result.get("file_path")
                
                # Validate the code
                print("\nValidating code...")
                validation_result = code_tool.validate_code(file_path=file_path)
                print_result(validation_result)
                
                if validation_result.get("success", False):
                    # Run the code
                    print("\nRunning code...")
                    args = []
                    
                    # Add command line args for languages that need them
                    if lang in ["javascript", "go", "c"]:
                        args = ["TestUser"]
                    
                    run_result = code_tool.run_code(file_path=file_path, args=args)
                    print_result(run_result)
                    
                # Generate a code summary
                print("\nGenerating code summary...")
                summary_result = code_tool.code_summary(file_path=file_path)
                print_result(summary_result)
    
    # Test the fix_code functionality with a broken example
    broken_example = generate_broken_python_example()
    
    # Generate the broken code file
    result = code_tool.generate_code(
        language=broken_example["language"],
        code=broken_example["code"],
        filename=broken_example["filename"]
    )
    print_result(result)
    
    if result.get("success", False):
        file_path = result.get("file_path")
        
        # Validate the broken code (should fail)
        print("\nValidating broken code...")
        validation_result = code_tool.validate_code(file_path=file_path)
        print_result(validation_result)
        
        # Get fix guidance
        if not validation_result.get("success", False):
            print("\nGetting fix guidance...")
            fix_result = code_tool.fix_code(
                file_path=file_path, 
                error_message=validation_result.get("stderr", "")
            )
            print_result(fix_result)
            
            print("\nFix guidance received. In a real scenario, an agent would:")
            print("1. Analyze the code and error messages")
            print("2. Make the necessary fixes")
            print("3. Generate a new fixed version of the code")
            print("4. Validate the fixed code again")
            
            # Example of a fixed version (for demonstration)
            print("\nExample of fixed code:")
            fixed_code = """
def greet(name):  # Added missing colon
    return f"Hello, {name}!"

def main():
    name = input("Enter your name: ")
    greeting = greet(name)
    print(greeting)  # Added missing parenthesis

if __name__ == "__main__":
    main()
"""
            print(fixed_code)


if __name__ == "__main__":
    asyncio.run(main()) 