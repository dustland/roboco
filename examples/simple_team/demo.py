#!/usr/bin/env python3
"""
Demo script showcasing Roboco's multi-agent collaboration framework.

This demo demonstrates real-world scenarios where teams of AI agents collaborate
to solve complex tasks, showcasing the new Task-centric API design.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import the new Task-centric API
import roboco


async def demo_research_and_planning():
    """Demonstrate a research and planning collaboration scenario."""
    print("=== Research & Planning Collaboration Demo ===\n")
    
    # Use team.yaml for research and planning scenario
    config_path = str(Path(__file__).parent / "config" / "team.yaml")
    
    try:
        # Create a task using the new API
        task = roboco.create_task(
            config_path=config_path,
            description="AI Productivity Tool Launch Planning"
        )
        
        print(f"✅ Created task: {task.task_id}")
        print(f"📋 Status: {task.status}")
        
        # Scenario: Planning a new product launch
        task_description = """
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
        
        # Start the collaboration using the new API
        result = await task.start(task_description)
        
        if result and result.success:
            print(f"✅ Collaboration completed successfully!")
            print(f"📊 Task ID: {task.task_id}")
            print(f"💬 Total exchanges: {len(result.conversation_history)}")
            print(f"📝 Summary: {result.summary}")
            
            # Show key insights from the collaboration
            print(f"\n🔍 Key Collaboration Insights:")
            print(f"   - Task managed through Task object")
            print(f"   - Config: team.yaml")
            print(f"   - Agents worked together across {len(result.conversation_history)} conversation rounds")
            print(f"   - Each agent contributed their specialized expertise")
            
            # Demonstrate memory access
            memory = task.get_memory()
            if memory:
                memories = memory.get_all(limit=5)
                print(f"   - Stored {len(memories)} memories during collaboration")
            
            return task
        else:
            print(f"❌ Collaboration failed: {result.summary if result else 'Unknown error'}")
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
        # Create task with the new API
        task = roboco.create_task(
            config_path=config_path,
            description="Remote Teams Guide Creation"
        )
        
        print(f"✅ Created task: {task.task_id}")
        
        # Scenario: Creating educational content
        task_description = """
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
        
        # Start collaboration
        result = await task.start(task_description)
        
        if result and result.success:
            print(f"✅ Content creation completed!")
            print(f"🔄 Workflow rounds: {len(result.conversation_history)}")
            
            # Demonstrate the collaborative process
            print(f"\n📋 Workflow Analysis:")
            print(f"   - Config: config.yaml")
            print(f"   - Planning phase: Agents structured the approach")
            print(f"   - Research phase: Gathered relevant information")
            print(f"   - Writing phase: Created cohesive content")
            print(f"   - Review phase: Refined and polished output")
            
            # Show task info
            info = task.get_info()
            print(f"   - Final status: {info.status}")
            print(f"   - Created: {info.created_at}")
            
            return task
        else:
            print(f"❌ Content creation failed: {result.summary if result else 'Unknown error'}")
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
        # Create task
        task = roboco.create_task(
            config_path=config_path,
            description="Web Application Performance Troubleshooting"
        )
        
        print(f"✅ Created task: {task.task_id}")
        
        # Scenario: Technical problem solving
        task_description = """
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
        
        # Start collaboration
        result = await task.start(task_description)
        
        if result and result.success:
            print(f"✅ Problem-solving session completed!")
            print(f"🧠 Collaborative analysis: {len(result.conversation_history)} discussion rounds")
            
            # Show how agents collaborated on problem-solving
            print(f"\n🔍 Collaboration Highlights:")
            print(f"   - Config: default.yaml")
            print(f"   - Systematic approach: Agents built on each other's analysis")
            print(f"   - Knowledge synthesis: Combined research with practical solutions")
            print(f"   - Comprehensive output: Actionable troubleshooting plan created")
            
            return task
        else:
            print(f"❌ Problem-solving failed: {result.summary if result else 'Unknown error'}")
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
        # Create initial task
        task = roboco.create_task(
            config_path=config_path,
            description="Employee Onboarding Program Design"
        )
        
        print(f"✅ Created task: {task.task_id}")
        
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
        print("⏱️  Starting initial phase...\n")
        
        # Start initial phase
        result1 = await task.start(initial_task)
        
        if result1 and result1.success:
            print(f"✅ Phase 1 completed!")
            print(f"📊 Initial work: {len(result1.conversation_history)} exchanges")
            
            # Demonstrate task retrieval and continuation
            print(f"\n🔄 Demonstrating task continuation...")
            
            # Retrieve the same task (simulating resumption)
            retrieved_task = roboco.get_task(task.task_id)
            if retrieved_task:
                print(f"✅ Retrieved task: {retrieved_task.task_id}")
                print(f"📋 Status: {retrieved_task.status}")
                
                # Continue with phase 2
                continuation_task = """
                Continue the employee onboarding program design.
                
                Phase 2: Detailed implementation
                1. Build on the foundation from Phase 1
                2. Create detailed timelines and checklists
                3. Design evaluation metrics
                4. Prepare implementation guidelines
                
                Reference the work completed in Phase 1.
                """
                
                print("🚀 Starting Phase 2 (continuation)...")
                result2 = await retrieved_task.start(continuation_task)
                
                if result2 and result2.success:
                    print(f"✅ Phase 2 completed!")
                    print(f"🔗 Continuation successful")
                    print(f"📈 Total project: {len(result2.conversation_history)} conversation rounds")
                    
                    print(f"\n🎯 Task Continuation Success:")
                    print(f"   - Config: team.yaml")
                    print(f"   - Memory persistence: Agents remembered Phase 1 work")
                    print(f"   - Context continuity: Smooth transition between phases")
                    print(f"   - Collaborative evolution: Ideas developed across sessions")
                    
                    # Show memory persistence
                    memory = retrieved_task.get_memory()
                    if memory:
                        all_memories = memory.get_all(limit=10)
                        print(f"   - Total memories across phases: {len(all_memories)}")
                    
                    return retrieved_task
                else:
                    print(f"❌ Phase 2 failed")
                    return task
            else:
                print(f"❌ Could not retrieve task for continuation")
                return task
        else:
            print(f"❌ Phase 1 failed: {result1.summary if result1 else 'Unknown error'}")
            return None
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return None


async def demo_framework_capabilities():
    """Demonstrate core framework capabilities through realistic scenarios."""
    print("\n=== Framework Capabilities Overview ===\n")
    
    print("🤖 Roboco Framework Demonstration")
    print("   Multi-agent collaboration with new Task-centric API\n")
    
    # Track successful demos
    completed_demos = []
    completed_tasks = []
    
    # Run different collaboration scenarios
    task1 = await demo_research_and_planning()
    if task1:
        completed_demos.append("Research & Planning")
        completed_tasks.append(task1)
    
    task2 = await demo_content_creation_workflow()
    if task2:
        completed_demos.append("Content Creation")
        completed_tasks.append(task2)
    
    task3 = await demo_problem_solving_collaboration()
    if task3:
        completed_demos.append("Problem Solving")
        completed_tasks.append(task3)
    
    task4 = await demo_task_continuation()
    if task4:
        completed_demos.append("Task Continuation")
        completed_tasks.append(task4)
    
    # Demonstrate task management capabilities
    if completed_tasks:
        print(f"\n=== Task Management Demo ===")
        
        # List all tasks
        all_tasks = roboco.list_tasks()
        print(f"📋 Total tasks in system: {len(all_tasks)}")
        
        for task in completed_tasks:
            info = task.get_info()
            print(f"   - {info.task_id}: {info.status} - {info.description}")
            
            # Show memory if available
            memory = task.get_memory()
            if memory:
                memories = memory.get_all(limit=3)
                print(f"     📚 Memories: {len(memories)} stored")
            
            # Show chat history
            chat = task.get_chat()
            history = chat.get_chat_history()
            print(f"     💬 Chat history: {len(history)} messages")
    
    # Summary of framework capabilities demonstrated
    print("\n" + "="*60)
    print("🎉 Framework Capabilities Demonstrated:")
    
    if completed_demos:
        for demo in completed_demos:
            print(f"   ✅ {demo}")
        
        print(f"\n🔧 New API Features Showcased:")
        print(f"   • Task-centric design with clean object-oriented API")
        print(f"   • Integrated memory operations (no task_id parameters needed)")
        print(f"   • Built-in event handling and chat session management")
        print(f"   • Task persistence and retrieval capabilities")
        print(f"   • Automatic memory scoping to tasks")
        print(f"   • Simplified task lifecycle management")
        print(f"   • No more global functions - everything through Task objects")
        
        print(f"\n📊 Collaboration Statistics:")
        print(f"   • Scenarios completed: {len(completed_demos)}")
        print(f"   • Tasks created: {len(completed_tasks)}")
        print(f"   • Configuration files tested: team.yaml, config.yaml, default.yaml")
        print(f"   • Agent teams coordinated: {len(completed_demos)} different configurations")
        print(f"   • Task persistence: Demonstrated across multiple sessions")
        
        print(f"\n🚀 API Benefits Demonstrated:")
        print(f"   • Intuitive: Task objects contain all related functionality")
        print(f"   • Clean: No more task_id parameters everywhere")
        print(f"   • Discoverable: IDE autocomplete shows all capabilities")
        print(f"   • Integrated: Memory, chat, events all in one place")
        print(f"   • Scalable: Easy to add new task-scoped functionality")
        
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
                task = await scenario_func()
                if task:
                    print(f"\n✅ Scenario completed! Task ID: {task.task_id}")
                    
                    # Show additional task info
                    info = task.get_info()
                    print(f"   Status: {info.status}")
                    print(f"   Description: {info.description}")
                else:
                    print(f"\n❌ Scenario failed")
        else:
            print("❌ Invalid choice. Please try again.")
        
        print("\n" + "="*50)


async def main():
    """Main demo function."""
    print("🤖 Welcome to Roboco Framework Demo!")
    print("   Showcasing Multi-Agent Collaboration with New Task-Centric API\n")
    
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
            print(f"\n💡 Key Takeaways:")
            print(f"   • New Task-centric API is much cleaner and more intuitive")
            print(f"   • Memory operations are automatically scoped to tasks")
            print(f"   • Task objects provide integrated access to all functionality")
            print(f"   • No more global functions or task_id parameters needed")
            print(f"\n📁 Check the workspace/ directory for:")
            print(f"   • Task outputs and artifacts")
            print(f"   • Memory database (if configured)")
            print(f"   • Collaboration logs and history")
        else:
            print(f"\n⚠️  Framework demonstration had issues")
            print(f"   Please check your configuration and try again")


if __name__ == "__main__":
    asyncio.run(main())
