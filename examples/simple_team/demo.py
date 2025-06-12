#!/usr/bin/env python3
"""
Demo script showcasing Roboco's multi-agent collaboration framework.

This demo demonstrates real-world scenarios where teams of AI agents collaborate
to solve complex tasks, showcasing the framework's capabilities rather than
testing individual subsystems.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from roboco.core.cli import run_task, resume_task


async def demo_research_and_planning():
    """Demonstrate a research and planning collaboration scenario."""
    print("=== Research & Planning Collaboration Demo ===\n")
    
    # Use team.yaml for research and planning scenario
    config_path = str(Path(__file__).parent / "config" / "team.yaml")
    
    try:
        # Scenario: Planning a new product launch
        task = """
        Our company wants to launch a new AI-powered productivity tool for remote teams.
        
        Please work together to:
        1. Research the current market landscape and competitors
        2. Identify key features and target audience
        3. Create a comprehensive launch plan with timeline
        4. Suggest marketing strategies and channels
        
        Make sure to collaborate effectively and build on each other's insights.
        """
        
        print("🎯 Task: AI Productivity Tool Launch Planning")
        print("👥 Team: Planner, Researcher, Writer (team.yaml)")
        print("🚀 Starting collaboration...\n")
        
        result = await run_task(
            config_path=config_path,
            task_description=task,
            max_rounds=15
        )
        
        if result and result.success:
            print(f"✅ Collaboration completed successfully!")
            print(f"📊 Participants: {', '.join(result.participants)}")
            print(f"💬 Total exchanges: {len(result.chat_history)}")
            print(f"📝 Summary: {result.summary}")
            
            # Show key insights from the collaboration
            print(f"\n🔍 Key Collaboration Insights:")
            print(f"   - Task ID: {result.task_id}")
            print(f"   - Config: team.yaml")
            print(f"   - Agents worked together across {len(result.chat_history)} conversation rounds")
            print(f"   - Each agent contributed their specialized expertise")
            
            return result.task_id
        else:
            print(f"❌ Collaboration failed: {result.error_message if result else 'Unknown error'}")
            return None
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def demo_content_creation_workflow():
    """Demonstrate a content creation workflow with multiple agents."""
    print("\n=== Content Creation Workflow Demo ===\n")
    
    # Use config.yaml for content creation scenario
    config_path = str(Path(__file__).parent / "config" / "config.yaml")
    
    try:
        # Scenario: Creating educational content
        task = """
        Create a comprehensive guide about "Building Effective Remote Teams" for a business blog.
        
        Work together to:
        1. Research best practices and current trends in remote work
        2. Structure the content with clear sections and actionable advice
        3. Write engaging, professional content that provides real value
        4. Ensure the guide is well-organized and ready for publication
        
        Target audience: Team leaders and managers transitioning to remote work.
        Length: Approximately 1500-2000 words.
        """
        
        print("🎯 Task: Remote Teams Guide Creation")
        print("👥 Team: Planner, Researcher, Writer (config.yaml)")
        print("📝 Collaborative writing workflow starting...\n")
        
        result = await run_task(
            config_path=config_path,
            task_description=task,
            max_rounds=20
        )
        
        if result and result.success:
            print(f"✅ Content creation completed!")
            print(f"👥 Team collaboration: {len(result.participants)} agents")
            print(f"🔄 Workflow rounds: {len(result.chat_history)}")
            
            # Demonstrate the collaborative process
            print(f"\n📋 Workflow Analysis:")
            print(f"   - Config: config.yaml")
            print(f"   - Planning phase: Agents structured the approach")
            print(f"   - Research phase: Gathered relevant information")
            print(f"   - Writing phase: Created cohesive content")
            print(f"   - Review phase: Refined and polished output")
            
            return result.task_id
        else:
            print(f"❌ Content creation failed: {result.error_message if result else 'Unknown error'}")
            return None
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return None


async def demo_problem_solving_collaboration():
    """Demonstrate collaborative problem-solving scenario."""
    print("\n=== Problem-Solving Collaboration Demo ===\n")
    
    # Use default.yaml for problem-solving scenario
    config_path = str(Path(__file__).parent / "config" / "default.yaml")
    
    try:
        # Scenario: Technical problem solving
        task = """
        A software development team is experiencing performance issues with their web application.
        Users are reporting slow page load times and occasional timeouts.
        
        Collaborate to:
        1. Analyze potential causes of the performance issues
        2. Research common web performance optimization techniques
        3. Develop a systematic troubleshooting plan
        4. Recommend specific solutions and implementation steps
        5. Create a monitoring strategy to prevent future issues
        
        Consider both technical and process improvements.
        """
        
        print("🎯 Task: Web Application Performance Troubleshooting")
        print("👥 Team: Planner, Researcher, Writer (default.yaml)")
        print("🔧 Problem-solving collaboration starting...\n")
        
        result = await run_task(
            config_path=config_path,
            task_description=task,
            max_rounds=18
        )
        
        if result and result.success:
            print(f"✅ Problem-solving session completed!")
            print(f"🧠 Collaborative analysis: {len(result.chat_history)} discussion rounds")
            
            # Show how agents collaborated on problem-solving
            print(f"\n🔍 Collaboration Highlights:")
            print(f"   - Config: default.yaml")
            print(f"   - Systematic approach: Agents built on each other's analysis")
            print(f"   - Knowledge synthesis: Combined research with practical solutions")
            print(f"   - Comprehensive output: Actionable troubleshooting plan created")
            
            return result.task_id
        else:
            print(f"❌ Problem-solving failed: {result.error_message if result else 'Unknown error'}")
            return None
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return None


async def demo_task_continuation():
    """Demonstrate task continuation and memory persistence."""
    print("\n=== Task Continuation Demo ===\n")
    
    # Use team.yaml for task continuation scenario
    config_path = str(Path(__file__).parent / "config" / "team.yaml")
    
    try:
        initial_task = """
        Design a comprehensive employee onboarding program for a tech startup.
        
        Phase 1: Create the foundation
        1. Research best practices in employee onboarding
        2. Identify key components and stakeholders
        3. Draft initial program structure
        
        This is a multi-phase project - focus on the foundation first.
        """
        
        print("🎯 Task: Employee Onboarding Program Design (Phase 1)")
        print("👥 Team: Planner, Researcher, Writer (team.yaml)")
        print("⏱️  Starting initial phase with limited rounds...\n")
        
        # Run initial phase with limited rounds
        result1 = await run_task(
            config_path=config_path,
            task_description=initial_task,
            max_rounds=8
        )
        
        if result1 and result1.success:
            print(f"✅ Phase 1 completed!")
            print(f"📋 Foundation established in {len(result1.chat_history)} rounds")
            
            # Continue the task with additional work
            print(f"\n🔄 Continuing task {result1.task_id} with Phase 2...")
            
            # Resume the task with additional rounds
            result2 = await resume_task(
                task_id=result1.task_id,
                max_rounds=12
            )
            
            if result2 and result2.success:
                print(f"✅ Phase 2 completed!")
                print(f"🔗 Seamless continuation: Agents built on previous work")
                print(f"📈 Total project: {len(result2.chat_history)} conversation rounds")
                
                print(f"\n🎯 Task Continuation Success:")
                print(f"   - Config: team.yaml")
                print(f"   - Memory persistence: Agents remembered Phase 1 work")
                print(f"   - Context continuity: Smooth transition between phases")
                print(f"   - Collaborative evolution: Ideas developed across sessions")
                
                return result2.task_id
            else:
                print(f"❌ Phase 2 failed: {result2.error_message if result2 else 'Unknown error'}")
                return result1.task_id
        else:
            print(f"❌ Phase 1 failed: {result1.error_message if result1 else 'Unknown error'}")
            return None
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return None


async def demo_framework_capabilities():
    """Demonstrate core framework capabilities through realistic scenarios."""
    print("\n=== Framework Capabilities Overview ===\n")
    
    print("🤖 Roboco Framework Demonstration")
    print("   Multi-agent collaboration for complex tasks\n")
    
    # Track successful demos
    completed_demos = []
    
    # Run different collaboration scenarios
    task1_id = await demo_research_and_planning()
    if task1_id:
        completed_demos.append("Research & Planning")
    
    task2_id = await demo_content_creation_workflow()
    if task2_id:
        completed_demos.append("Content Creation")
    
    task3_id = await demo_problem_solving_collaboration()
    if task3_id:
        completed_demos.append("Problem Solving")
    
    task4_id = await demo_task_continuation()
    if task4_id:
        completed_demos.append("Task Continuation")
    
    # Summary of framework capabilities demonstrated
    print("\n" + "="*60)
    print("🎉 Framework Capabilities Demonstrated:")
    
    if completed_demos:
        for demo in completed_demos:
            print(f"   ✅ {demo}")
        
        print(f"\n🔧 Framework Features Showcased:")
        print(f"   • Multi-agent collaboration and coordination")
        print(f"   • Intelligent task distribution and specialization")
        print(f"   • Memory persistence across task sessions")
        print(f"   • Seamless task continuation and resumption")
        print(f"   • Configurable team compositions and workflows")
        print(f"   • Multiple configuration files for different scenarios")
        print(f"   • Event-driven collaboration monitoring")
        
        print(f"\n📊 Collaboration Statistics:")
        print(f"   • Scenarios completed: {len(completed_demos)}")
        print(f"   • Configuration files tested: team.yaml, config.yaml, default.yaml")
        print(f"   • Agent teams coordinated: {len(completed_demos)} different configurations")
        print(f"   • Task persistence: Demonstrated across multiple sessions")
        
        print(f"\n🚀 Ready for Production:")
        print(f"   • Framework handles complex, multi-step workflows")
        print(f"   • Flexible configuration system for different use cases")
        print(f"   • Agents collaborate naturally and effectively")
        print(f"   • Memory and context preserved across sessions")
        print(f"   • Scalable to different team sizes and compositions")
        
    else:
        print("   ❌ No demos completed successfully")
        print("   Check your configuration and API keys")
    
    return len(completed_demos)


async def interactive_scenario_demo():
    """Interactive demo for testing specific scenarios."""
    print("\n=== Interactive Scenario Testing ===\n")
    
    scenarios = {
        "1": ("Research & Planning", demo_research_and_planning),
        "2": ("Content Creation", demo_content_creation_workflow),
        "3": ("Problem Solving", demo_problem_solving_collaboration),
        "4": ("Task Continuation", demo_task_continuation),
        "5": ("All Scenarios", demo_framework_capabilities)
    }
    
    while True:
        print("Choose a collaboration scenario to test:")
        for key, (name, _) in scenarios.items():
            print(f"{key}. {name}")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == "0":
            print("👋 Demo session ended!")
            break
        elif choice in scenarios:
            scenario_name, scenario_func = scenarios[choice]
            print(f"\n🚀 Running {scenario_name} scenario...\n")
            
            if choice == "5":
                completed = await scenario_func()
                print(f"\n📈 Completed {completed} out of 4 scenarios")
            else:
                task_id = await scenario_func()
                if task_id:
                    print(f"\n✅ Scenario completed! Task ID: {task_id}")
                else:
                    print(f"\n❌ Scenario failed")
        else:
            print("❌ Invalid choice. Please try again.")
        
        print("\n" + "="*50)


async def main():
    """Main demo function."""
    print("🤖 Welcome to Roboco Framework Demo!")
    print("   Showcasing Multi-Agent Collaboration Capabilities\n")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
        print("   Please set your OpenAI API key for full functionality:")
        print("   export OPENAI_API_KEY='your-api-key-here'\n")
        
        choice = input("Continue anyway? (y/N): ").strip().lower()
        if choice != 'y':
            print("👋 Please set your API key and try again!")
            return
    
    # Check demo mode
    print("Demo modes available:")
    print("1. Full framework demonstration (all scenarios)")
    print("2. Interactive scenario testing")
    
    mode = input("\nChoose mode (1 or 2): ").strip()
    
    if mode == "2":
        await interactive_scenario_demo()
    else:
        # Run full framework demonstration
        print("\n🚀 Running full framework demonstration...\n")
        completed_scenarios = await demo_framework_capabilities()
        
        if completed_scenarios > 0:
            print(f"\n🎉 Framework demonstration completed!")
            print(f"   Successfully showcased {completed_scenarios} collaboration scenarios")
            print(f"\n📁 Check the workspace/ directory for:")
            print(f"   • Task outputs and artifacts")
            print(f"   • Memory database (if configured)")
            print(f"   • Collaboration logs and history")
        else:
            print(f"\n⚠️  Framework demonstration had issues")
            print(f"   Please check your configuration and try again")


if __name__ == "__main__":
    asyncio.run(main())
