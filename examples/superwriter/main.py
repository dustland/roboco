#!/usr/bin/env python3
"""
SuperWriter - Advanced Research Report Generation System

A comprehensive multi-agent system for generating long-form research reports.
Supports autonomous research, writing, and review cycles with real-time monitoring
and human intervention capabilities.

Features:
- Autonomous multi-agent collaboration (Planner → Researcher → Writer → Reviewer)
- Long-form content generation (50+ pages, 50k+ words)
- Real-time artifact monitoring via observability platform
- Human-in-the-loop intervention during generation
- Structured report compilation with sections, references, and appendices
- Progress tracking and quality assurance
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

# Add the src directory to Python path
sys.path.insert(0, str(project_root / "src"))

import agentx
from agentx.core.team import Team
from agentx.core.orchestrator import Orchestrator
from agentx.utils.logger import get_logger

logger = get_logger(__name__)


class SuperWriter:
    """Advanced research report generation system."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or str(Path(__file__).parent / "config" / "team.yaml")
        self.team: Optional[Team] = None
        self.orchestrator: Optional[Orchestrator] = None
        self.workspace_dir = Path(__file__).parent / "workspace"
        
    async def initialize(self):
        """Initialize the SuperWriter system."""
        # Initialize AgentX framework
        agentx.initialize()
        
        # Load team configuration
        self.team = Team.from_config(self.config_path)
        
        # Create orchestrator with workspace
        self.orchestrator = Orchestrator(self.team, max_rounds=150, timeout=10800)
        
        logger.info(f"SuperWriter initialized with team: {self.team.name}")
        logger.info(f"Workspace directory: {self.workspace_dir}")
        logger.info("Built-in context and planning tools automatically available to all agents")
    
    async def generate_research_report(
        self, 
        topic: str, 
        target_length: str = "50+ pages",
        streaming: bool = True,
        allow_intervention: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive research report on the given topic.
        
        Args:
            topic: Research topic (e.g., "Tesla auto driving")
            target_length: Target report length (e.g., "50+ pages", "50k+ words")
            streaming: Enable real-time streaming output
            allow_intervention: Allow human intervention during generation
            
        Returns:
            Dict with generation results and metadata
        """
        if not self.orchestrator:
            await self.initialize()
        
        # Create comprehensive research prompt
        research_prompt = self._create_research_prompt(topic, target_length)
        
        print("🚀 SuperWriter Research Report Generation")
        print("=" * 60)
        print(f"📝 Topic: {topic}")
        print(f"📏 Target Length: {target_length}")
        print(f"🔄 Streaming: {'Enabled' if streaming else 'Disabled'}")
        print(f"👤 Human Intervention: {'Allowed' if allow_intervention else 'Disabled'}")
        print(f"📁 Workspace: {self.workspace_dir}")
        print()
        
        # Start the task
        task_id = await self.orchestrator.start_task(
            prompt=research_prompt,
            initial_agent="consultant"
        )
        
        print(f"🎬 Starting research report generation (Task: {task_id})")
        print(f"🌐 Monitor progress at: http://localhost:8506/tasks/{task_id}")
        print()
        
        if streaming:
            return await self._execute_with_streaming(task_id, allow_intervention)
        else:
            return await self._execute_autonomous(task_id)
    
    def _create_research_prompt(self, topic: str, target_length: str) -> str:
        """Create a comprehensive research prompt for the given topic."""
        return f"""
# Research Report Generation Task

## Topic
{topic}

## Objective
Generate a comprehensive, professional research report that provides deep insights, analysis, and actionable information about {topic}.

## Requirements

### Content Requirements
- **Length**: {target_length} (approximately 50,000+ words)
- **Depth**: Comprehensive coverage with multiple perspectives
- **Quality**: Professional, well-researched, and authoritative
- **Structure**: Clear organization with logical flow
- **Sources**: Credible, recent, and diverse references

### Report Structure
1. **Executive Summary** (2-3 pages)
2. **Introduction and Background** (5-7 pages)
3. **Current State Analysis** (8-10 pages)
4. **Technical Deep Dive** (10-15 pages)
5. **Market Analysis** (8-10 pages)
6. **Competitive Landscape** (6-8 pages)
7. **Challenges and Limitations** (5-7 pages)
8. **Future Outlook and Trends** (8-10 pages)
9. **Recommendations** (3-5 pages)
10. **Conclusion** (2-3 pages)
11. **References and Bibliography**
12. **Appendices** (technical details, data tables, etc.)

### Quality Standards
- Each section should be thoroughly researched and well-documented
- Include relevant data, statistics, and expert opinions
- Maintain professional tone and academic rigor
- Ensure factual accuracy and cite all sources
- Create visual elements where appropriate (tables, charts, diagrams)

### Collaboration Workflow
1. **Planner**: Create detailed research plan and section outlines
2. **Researcher**: Conduct comprehensive research for each section
3. **Writer**: Draft sections with proper structure and flow
4. **Reviewer**: Quality assurance, fact-checking, and refinement

### Artifacts to Generate
- Research plan and methodology
- Section-by-section outlines
- Research notes and source compilation
- Draft sections for review
- Final compiled report
- Executive summary
- Reference bibliography
- Supporting appendices

## Success Criteria
- Report meets or exceeds target length requirement
- All sections are well-researched and professionally written
- Sources are credible, recent, and properly cited
- Content provides actionable insights and recommendations
- Report structure is logical and easy to navigate
- Quality meets professional publication standards

Begin with comprehensive planning and research methodology development.
"""
    
    async def _execute_with_streaming(
        self, 
        task_id: str, 
        allow_intervention: bool
    ) -> Dict[str, Any]:
        """Execute the task with real-time streaming and optional intervention."""
        
        # Track progress metrics
        metrics = {
            "total_chunks": 0,
            "agent_responses": {},
            "handoffs": [],
            "artifacts_created": [],
            "sections_completed": [],
            "word_count": 0,
            "intervention_points": []
        }
        
        print("📊 Real-time Progress Monitoring:")
        print("   • Agent responses will stream in real-time")
        print("   • Artifacts will be saved to workspace/")
        print("   • Monitor via observability platform")
        if allow_intervention:
            print("   • Type 'INTERVENE: <message>' to provide guidance")
        print()
        print("🔄 Starting autonomous research and writing process...")
        print("=" * 60)
        
        try:
            # Execute with streaming
            async for update in self.orchestrator.execute_task_streaming(task_id):
                update_type = update.get("type")
                
                if update_type == "agent_start":
                    agent_name = update["agent_name"]
                    print(f"\n🤖 {agent_name.upper()} is working...")
                    print(f"💭 ", end="", flush=True)
                    metrics["agent_responses"][agent_name] = ""
                    
                elif update_type == "response_chunk":
                    chunk = update["chunk"]
                    agent_name = update["agent_name"]
                    
                    # Print chunk in real-time
                    print(chunk, end="", flush=True)
                    
                    # Track metrics
                    metrics["agent_responses"][agent_name] += chunk
                    metrics["total_chunks"] += 1
                    metrics["word_count"] += len(chunk.split())
                    
                elif update_type == "agent_complete":
                    agent_name = update["agent_name"]
                    response_length = update["response_length"]
                    print(f"\n\n✅ {agent_name} completed ({response_length:,} characters)")
                    
                    # Check for artifacts
                    task_state = self.orchestrator.get_task_state(task_id)
                    if task_state and task_state.artifacts:
                        new_artifacts = [name for name in task_state.artifacts.keys() 
                                       if name not in metrics["artifacts_created"]]
                        if new_artifacts:
                            metrics["artifacts_created"].extend(new_artifacts)
                            print(f"📎 New artifacts: {', '.join(new_artifacts)}")
                    
                    # Show progress
                    self._show_progress_update(metrics)
                    
                elif update_type == "handoff":
                    from_agent = update["from_agent"]
                    to_agent = update["to_agent"]
                    handoff_desc = f"{from_agent} → {to_agent}"
                    metrics["handoffs"].append(handoff_desc)
                    
                    print(f"\n🔄 HANDOFF: {handoff_desc}")
                    print("=" * 50)
                    
                    # Check for intervention opportunity
                    if allow_intervention:
                        print("💡 Intervention opportunity - type 'INTERVENE: <message>' or press Enter to continue")
                        # Note: In a real implementation, you'd handle async input here
                    
                elif update_type == "task_complete":
                    total_steps = update["total_steps"]
                    print(f"\n🎉 Research report generation completed! ({total_steps} total steps)")
                    break
                    
                elif update_type == "error":
                    error = update["error"]
                    print(f"\n❌ Error: {error}")
                    return {"success": False, "error": error, "metrics": metrics}
            
            # Final summary
            return await self._generate_completion_summary(task_id, metrics)
            
        except Exception as e:
            logger.exception("Streaming execution failed")
            print(f"\n💥 Generation failed: {e}")
            return {"success": False, "error": str(e), "metrics": metrics}
    
    async def _execute_autonomous(self, task_id: str) -> Dict[str, Any]:
        """Execute the task autonomously without streaming."""
        print("🤖 Running in autonomous mode...")
        
        try:
            # Execute task to completion
            final_state = await self.orchestrator.execute_task(task_id)
            
            # Generate summary
            metrics = {
                "total_steps": len(final_state.history),
                "artifacts_created": list(final_state.artifacts.keys()),
                "word_count": self._estimate_word_count(final_state),
                "completion_status": "success" if final_state.is_complete else "incomplete"
            }
            
            return {"success": True, "task_id": task_id, "metrics": metrics}
            
        except Exception as e:
            logger.exception("Autonomous execution failed")
            return {"success": False, "error": str(e)}
    
    def _show_progress_update(self, metrics: Dict[str, Any]):
        """Show current progress metrics."""
        word_count = metrics["word_count"]
        target_words = 50000  # 50k words target
        progress_pct = min(100, (word_count / target_words) * 100)
        
        print(f"📈 Progress: {word_count:,} words ({progress_pct:.1f}% of 50k target)")
        print(f"📊 Agents active: {len(metrics['agent_responses'])}")
        print(f"🔄 Handoffs: {len(metrics['handoffs'])}")
        print(f"📎 Artifacts: {len(metrics['artifacts_created'])}")
    
    async def _generate_completion_summary(
        self, 
        task_id: str, 
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a comprehensive completion summary."""
        
        # Get final task state
        task_state = self.orchestrator.get_task_state(task_id)
        
        print("\n" + "=" * 60)
        print("🎊 RESEARCH REPORT GENERATION COMPLETE!")
        print("=" * 60)
        print()
        
        print("📊 Generation Summary:")
        print(f"   • Total words: {metrics['word_count']:,}")
        print(f"   • Total chunks: {metrics['total_chunks']:,}")
        print(f"   • Agents participated: {len(metrics['agent_responses'])}")
        print(f"   • Handoffs executed: {len(metrics['handoffs'])}")
        print(f"   • Artifacts created: {len(metrics['artifacts_created'])}")
        print()
        
        if metrics["artifacts_created"]:
            print("📎 Generated Artifacts:")
            for artifact in metrics["artifacts_created"]:
                print(f"   • {artifact}")
            print()
        
        print("🔄 Collaboration Flow:")
        for i, handoff in enumerate(metrics["handoffs"], 1):
            print(f"   {i}. {handoff}")
        print()
        
        print("📈 Agent Contributions:")
        for agent, response in metrics["agent_responses"].items():
            word_count = len(response.split())
            print(f"   • {agent}: {word_count:,} words")
        print()
        
        print(f"📁 Workspace: {self.workspace_dir}")
        print(f"🌐 View details: http://localhost:8506/tasks/{task_id}")
        print()
        
        # Check if target was met
        target_met = metrics["word_count"] >= 50000
        if target_met:
            print("✅ TARGET ACHIEVED: Report meets 50k+ word requirement!")
        else:
            remaining = 50000 - metrics["word_count"]
            print(f"⚠️  Target not fully met: {remaining:,} words remaining for 50k target")
        
        return {
            "success": True,
            "task_id": task_id,
            "metrics": metrics,
            "target_met": target_met,
            "workspace_path": str(self.workspace_dir),
            "artifacts": metrics["artifacts_created"]
        }
    
    def _estimate_word_count(self, task_state) -> int:
        """Estimate total word count from task state."""
        total_words = 0
        for step in task_state.history:
            for part in step.parts:
                if hasattr(part, 'text'):
                    total_words += len(part.text.split())
        return total_words
    
    # Context and planning are now handled by built-in tools
    # All agents automatically have access to:
    # - update_context() - Update project context with flexible JSON
    # - get_context() - Query context with natural language  
    # - create_plan() - Create execution plans with phases and tasks
    # - update_task_status() - Update task progress
    # - get_plan_status() - Get plan progress and status


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY"]
    found_keys = []
    
    print("🔍 Checking API keys...")
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ Found {var}")
            found_keys.append(var)
        else:
            print(f"❌ Missing {var}")
    
    if found_keys:
        print(f"✅ Environment ready with {len(found_keys)} API key(s)")
        return True
    else:
        print("❌ No API keys found. Please check your .env file.")
        return False


async def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="SuperWriter - Advanced Research Report Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Tesla auto driving technology"
  python main.py "AI in healthcare" --length "100 pages"
  python main.py "Climate change solutions" --no-streaming
  python main.py "Quantum computing" --no-intervention
        """
    )
    
    parser.add_argument(
        "topic", 
        help="Research topic for report generation"
    )
    parser.add_argument(
        "--length", 
        default="50+ pages", 
        help="Target report length (default: 50+ pages)"
    )
    parser.add_argument(
        "--no-streaming", 
        action="store_true", 
        help="Disable real-time streaming output"
    )
    parser.add_argument(
        "--no-intervention", 
        action="store_true", 
        help="Disable human intervention capabilities"
    )
    parser.add_argument(
        "--config", 
        help="Path to team configuration file"
    )
    
    args = parser.parse_args()
    
    # Check environment
    if not check_environment():
        return
    
    # Create SuperWriter instance
    superwriter = SuperWriter(config_path=args.config)
    
    try:
        # Generate research report
        result = await superwriter.generate_research_report(
            topic=args.topic,
            target_length=args.length,
            streaming=not args.no_streaming,
            allow_intervention=not args.no_intervention
        )
        
        if result["success"]:
            print("\n🎉 Research report generation completed successfully!")
            if result.get("target_met"):
                print("🏆 Target length requirement achieved!")
        else:
            print(f"\n❌ Generation failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Generation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.exception("Main execution error")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main())) 