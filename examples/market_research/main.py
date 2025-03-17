#!/usr/bin/env python3
"""
Embodied AI Market Research Example

This example demonstrates a scenario where a CEO asks about cutting-edge embodied AI
technologies, and a research team collaborates to create a comprehensive report.
"""

import os
import sys
import argparse
import io
import contextlib
from pathlib import Path
from datetime import datetime
from loguru import logger

# Configure logger and add project root to path
logger.remove()
logger.add(sys.stderr, level="INFO")
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root / "src"))

# Load environment variables
from roboco.core.config import load_env_variables
load_env_variables(project_root)

# Import the research team
from examples.market_research.team import ResearchTeam

def extract_report_from_output(output):
    """Extract the report content from the terminal output."""
    if "# Market Research Report" not in output:
        return None
    
    lines = output.split('\n')
    report_lines = []
    capturing = False
    
    for line in lines:
        if line.startswith("# Market Research Report"):
            capturing = True
            report_lines.append(line)
        elif capturing and line.startswith("--------------------------------------------------------------------------------"):
            break
        elif capturing:
            report_lines.append(line)
    
    return '\n'.join(report_lines) if report_lines else None

def run_research(query):
    """Run team-based research with swarm orchestration."""
    # Capture stdout to extract the report later
    stdout_buffer = io.StringIO()
    with contextlib.redirect_stdout(stdout_buffer):
        # Create research team and run the research
        team = ResearchTeam()
        team.run_research(query)
    
    # Get the captured output
    output = stdout_buffer.getvalue()
    
    # Extract report from the output
    report_content = extract_report_from_output(output)
    
    # Save report if found
    if report_content:
        os.makedirs("reports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"reports/embodied_ai_report_{timestamp}.md"
        with open(report_path, "w") as f:
            f.write(report_content)
        print(f"\n💾 Report saved to {report_path}")
    else:
        print("\n⚠️ No report content found to save")

def main():
    """Main entry point for the market research example."""
    parser = argparse.ArgumentParser(description="Run market research with AG2")
    parser.add_argument("--query", type=str, default="What are the latest developments in embodied AI?")
    args = parser.parse_args()
    
    print(f"\n🧠 Running team research on: {args.query}")
    run_research(args.query)

if __name__ == "__main__":
    main()