#!/usr/bin/env python3
"""
GAIA Benchmark Runner for AgentX Framework

A comprehensive benchmark implementation for evaluating agent teams on the 
GAIA (General AI Assistant) dataset using the AgentX multi-agent framework.
"""

import asyncio
import argparse
import sys
import traceback
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import AgentX core functions
from agentx import start_task, set_log_level

# Import benchmark utilities
from .utils.data_loader import GAIADataLoader
from .utils.progress_tracker import TaskTracker
from .utils.evaluator import GAIAEvaluator
from .utils.output_manager import OutputManager
from .utils.cost_calculator import CostCalculator


# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run GAIA benchmark with AgentX framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with team1 configuration
  python main.py --team team1

  # Run limited test with verbose output
  python main.py --team team3 --limit 10 --verbose

  # Resume from checkpoint
  python main.py --team team1 --resume --checkpoint-dir results/team1_20231201_120000
        """
    )
    
    parser.add_argument(
        "--team", 
        required=True,
        help="Team configuration to use (e.g., team1, team2, team3)"
    )
    parser.add_argument(
        "--limit", 
        type=int,
        help="Limit number of questions for testing"
    )
    parser.add_argument(
        "--concurrent", 
        type=int, 
        default=3,
        help="Number of concurrent tasks (default: 3)"
    )
    parser.add_argument(
        "--split", 
        default="validation",
        choices=["validation", "test"],
        help="Dataset split to use (default: validation)"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=300,
        help="Timeout per question in seconds (default: 300)"
    )
    parser.add_argument(
        "--resume", 
        action="store_true",
        help="Resume from checkpoint"
    )
    parser.add_argument(
        "--checkpoint-dir",
        help="Checkpoint directory to resume from"
    )
    parser.add_argument(
        "--output-dir", 
        default="results",
        help="Output directory for results (default: results)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def process_question(
    question: Dict[str, Any],
    team_config_path: str,
    output_manager: OutputManager,
    cost_calculator: CostCalculator,
    timeout: int = 300,
    verbose: bool = False
) -> Dict[str, Any]:
    """Process a single GAIA question with the specified team."""
    question_id = question.get("task_id", question.get("id", "unknown"))
    
    try:
        # Prepare the question as a task
        task_content = f"""
Question: {question['Question']}

Please provide a direct, factual answer. Be concise and specific.
"""
        
        # Add any attached files information if available
        if question.get("file_name"):
            task_content += f"\nAttached file: {question['file_name']}"
        
        # Track start time
        start_time = time.time()
        
        # Start the task and set up cost tracking
        task = start_task(task_content, team_config_path)
        
        # Set up usage tracking via Brain wrapping (simpler than callbacks)
        wrapped_agents = []
        try:
            if hasattr(task, 'task') and hasattr(task.task, 'agents'):
                agents = task.task.agents
                if verbose:
                    print(f"   Found {len(agents)} agents: {list(agents.keys())}")
                
                for agent_name, agent in agents.items():
                    if verbose:
                        print(f"   Agent {agent_name}: {type(agent)}")
                        print(f"     Has brain: {hasattr(agent, 'brain')}")
                    
                    if hasattr(agent, 'brain'):
                        cost_calculator.wrap_agent_brain(agent, agent_name)
                        wrapped_agents.append(agent_name)
                        if verbose:
                            print(f"{Colors.CYAN}💰 Set up cost tracking for agent: {agent_name}{Colors.RESET}")
            else:
                if verbose:
                    print(f"{Colors.YELLOW}⚠️  Could not access task.agents structure{Colors.RESET}")
        except Exception as e:
            if verbose:
                print(f"{Colors.YELLOW}⚠️  Could not set up brain wrapping: {e}{Colors.RESET}")
                import traceback
                traceback.print_exc()
        
        # Execute with timeout and collect response
        final_response_parts = []
        tool_calls_made = []
        
        async def execute_with_timeout():
            print(f"\n{Colors.BLUE}🤖 Processing Question: {question_id}{Colors.RESET}")
            print(f"{Colors.CYAN}📋 Question: {question['Question'][:100]}{'...' if len(question['Question']) > 100 else ''}{Colors.RESET}")
            print(f"{Colors.YELLOW}💭 Agent thinking...{Colors.RESET}\n")
            
            async for result in task.step(stream=True):
                if result.get("type") == "content":
                    content = result.get("content", "")
                    print(content, end="", flush=True)  # Stream the response in real-time
                    final_response_parts.append(content)
                elif result.get("type") == "tool_call":
                    # Tool call data is directly in result, not nested under "tool_call"
                    tool_name = result.get("name", "unknown")
                    tool_args = result.get("arguments", {})
                    tool_calls_made.append({"name": tool_name, "arguments": tool_args})
                    print(f"\n{Colors.MAGENTA}🔧 Tool Call: {tool_name}{Colors.RESET}")
                    if verbose and tool_args:
                        print(f"{Colors.MAGENTA}   Args: {tool_args}{Colors.RESET}")
                elif result.get("type") == "tool_result":
                    # Tool result data is directly in result, not nested under "tool_result"
                    tool_name = result.get("name", "unknown")
                    success = result.get("success", False)
                    if success:
                        print(f"{Colors.GREEN}✅ Tool completed: {tool_name}{Colors.RESET}")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        print(f"{Colors.RED}❌ Tool failed: {tool_name} - {error_msg}{Colors.RESET}")
                elif result.get("type") == "routing_decision" and result.get("action") == "COMPLETE":
                    break
            
            print("\n")  # Add newline after completion
            return "".join(final_response_parts).strip()
        
        final_answer = await asyncio.wait_for(
            execute_with_timeout(),
            timeout=timeout
        )
        
        # Clean up brain wrapping
        try:
            cost_calculator.unwrap_agents()
            if verbose and wrapped_agents:
                print(f"{Colors.CYAN}🧹 Cleaned up cost tracking for agents: {', '.join(wrapped_agents)}{Colors.RESET}")
        except Exception as e:
            if verbose:
                print(f"{Colors.YELLOW}⚠️  Error cleaning up wrapping: {e}{Colors.RESET}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare result
        result_data = {
            "question_id": question_id,
            "question": question["Question"],
            "predicted_answer": final_answer,
            "ground_truth": question.get("answer", ""),  # Use correct field name
            "level": question.get("Level", "unknown"),
            "tool_calls": tool_calls_made,
            "processing_time": processing_time,
            "status": "completed"
        }
        
        print(f"{Colors.GREEN}✅ Question {question_id} completed in {processing_time:.1f}s{Colors.RESET}")
        if verbose:
            current_cost = cost_calculator.get_total_cost()
            current_calls = cost_calculator.get_total_calls()
            print(f"{Colors.CYAN}💰 Current total cost: ${current_cost:.6f} ({current_calls} calls){Colors.RESET}")
        
        return result_data
        
    except asyncio.TimeoutError:
        print(f"{Colors.RED}⏰ Question {question_id} timed out after {timeout}s{Colors.RESET}")
        return {
            "question_id": question_id,
            "question": question["Question"],
            "predicted_answer": "",
            "ground_truth": question.get("answer", ""),
            "level": question.get("Level", "unknown"),
            "tool_calls": [],
            "processing_time": timeout,
            "status": "timeout",
            "error": f"Timeout after {timeout} seconds"
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"{Colors.RED}❌ Question {question_id} failed: {error_msg}{Colors.RESET}")
        return {
            "question_id": question_id,
            "question": question["Question"],
            "predicted_answer": "",
            "ground_truth": question.get("answer", ""),
            "level": question.get("Level", "unknown"),
            "tool_calls": [],
            "processing_time": 0,
            "status": "error",
            "error": error_msg
        }


async def run_benchmark(
    team: str,
    limit: Optional[int] = None,
    concurrent_limit: int = 3,
    split: str = "validation",
    resume: bool = False,
    checkpoint_dir: Optional[str] = None,
    output_dir: str = "results",
    timeout: int = 300,
    verbose: bool = False
) -> None:
    """Run the GAIA benchmark with specified configuration."""
    
    # Setup paths
    config_dir = Path(__file__).parent / "config" / team
    team_config_path = config_dir / "team.yaml"
    
    if not team_config_path.exists():
        raise FileNotFoundError(f"Team configuration not found: {team_config_path}")
    
    # Initialize components
    data_loader = GAIADataLoader()
    cost_calculator = CostCalculator()
    
    # Create output manager
    if resume and checkpoint_dir:
        output_manager = OutputManager.from_checkpoint(checkpoint_dir)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"{team}_{timestamp}"
        output_manager = OutputManager(output_dir, run_id)
    
    # Initialize tracker
    tracker = TaskTracker(output_manager.run_dir)
    
    try:
        # Load GAIA dataset
        print(f"Loading GAIA {split} dataset...")
        questions = data_loader.load_dataset(split=split)
        
        if limit:
            questions = questions[:limit]
            print(f"Limited to {limit} questions for testing")
        
        print(f"Loaded {len(questions)} questions")
        
        # Resume from checkpoint if specified
        if resume:
            completed_ids = output_manager.get_completed_question_ids()
            questions = [q for q in questions if q.get("task_id", q.get("id")) not in completed_ids]
            print(f"Resuming: {len(questions)} questions remaining")
        
        # Initialize tracker with the actual number of questions to process
        tracker.initialize(len(questions), team, split)
        
        # Process questions concurrently
        semaphore = asyncio.Semaphore(concurrent_limit)
        results = []
        
        async def process_with_semaphore(question):
            async with semaphore:
                result = await process_question(
                    question, 
                    str(team_config_path), 
                    output_manager,
                    cost_calculator,
                    timeout,
                    verbose
                )
                tracker.update_progress(result)
                return result
        
        # Create tasks for all questions
        tasks = [process_with_semaphore(q) for q in questions]
        
        print(f"Processing {len(tasks)} questions with {concurrent_limit} concurrent tasks...")
        
        # Process with progress tracking
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            
            # Print progress with result status
            completed = i + 1
            total = len(tasks)
            success_rate = tracker.get_success_rate()
            
            # Show result status with color
            status_color = Colors.GREEN if result["status"] == "completed" else Colors.RED
            status_symbol = "✅" if result["status"] == "completed" else "❌"
            
            print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%) - "
                  f"Success rate: {success_rate:.1f}% - "
                  f"{status_color}{status_symbol} Q{result['question_id']}: {result['status']}{Colors.RESET}")
            
            # Save checkpoint every 10 questions
            if completed % 10 == 0:
                tracker.save_checkpoint()
        
        # Save final results
        print("Saving final results...")
        output_manager.save_final_results(results)
        tracker.finalize()
        
        # Run evaluation
        print("Running evaluation...")
        evaluator = GAIAEvaluator()
        evaluation_results = evaluator.evaluate_results(results)
        
        output_manager.save_evaluation_results(evaluation_results)
        
        # Save cost summary
        cost_summary = cost_calculator.get_summary()
        output_manager.save_cost_summary(cost_summary)
        
        # Print detailed results for each question
        print(f"\n{Colors.BOLD}📊 DETAILED RESULTS{Colors.RESET}")
        print("=" * 80)
        
        for result in results:
            question_id = result["question_id"]
            status = result["status"]
            level = result["level"]
            
            # Determine if answer is correct
            if status == "completed":
                evaluator_instance = GAIAEvaluator()
                is_correct = evaluator_instance._is_answer_correct(
                    result["predicted_answer"], 
                    result["ground_truth"]
                )
                result_color = Colors.GREEN if is_correct else Colors.RED
                result_symbol = "✅ PASS" if is_correct else "❌ FAIL"
            else:
                result_color = Colors.RED
                result_symbol = f"❌ {status.upper()}"
            
            print(f"{result_color}{result_symbol}{Colors.RESET} Q{question_id} (Level {level}) - "
                  f"{result['processing_time']:.1f}s")
            
            if verbose:
                print(f"  Question: {result['question'][:100]}{'...' if len(result['question']) > 100 else ''}")
                if result['predicted_answer']:
                    print(f"  Predicted: {result['predicted_answer'][:100]}{'...' if len(result['predicted_answer']) > 100 else ''}")
                if result['ground_truth']:
                    print(f"  Expected: {result['ground_truth'][:100]}{'...' if len(result['ground_truth']) > 100 else ''}")
                if result['tool_calls']:
                    print(f"  Tools used: {', '.join([tc['name'] for tc in result['tool_calls']])}")
                if result.get('error'):
                    print(f"  Error: {result['error']}")
                print()
        
        # Print cost summary
        cost_calculator.print_summary()
        
        # Print summary with colors
        print(f"\n{Colors.BOLD}🎯 BENCHMARK COMPLETED{Colors.RESET}")
        print("=" * 60)
        print(f"Team: {Colors.CYAN}{team}{Colors.RESET}")
        print(f"Total questions: {len(results)}")
        
        # Color-code accuracy based on performance
        overall_acc = evaluation_results['overall_accuracy']
        acc_color = Colors.GREEN if overall_acc >= 70 else Colors.YELLOW if overall_acc >= 50 else Colors.RED
        print(f"Overall accuracy: {acc_color}{overall_acc:.2f}%{Colors.RESET}")
        
        # Level accuracies with colors
        for level in ["1", "2", "3"]:
            level_acc = evaluation_results.get(f'level_{level}_accuracy', 0)
            level_color = Colors.GREEN if level_acc >= 70 else Colors.YELLOW if level_acc >= 50 else Colors.RED
            print(f"Level {level} accuracy: {level_color}{level_acc:.2f}%{Colors.RESET}")
        
        print(f"Average processing time: {evaluation_results['avg_processing_time']:.2f}s")
        print(f"Total processing time: {evaluation_results['total_processing_time']:.2f}s")
        
        # Success rate with color
        success_rate = evaluation_results['success_rate']
        success_color = Colors.GREEN if success_rate >= 90 else Colors.YELLOW if success_rate >= 70 else Colors.RED
        print(f"Success rate: {success_color}{success_rate:.2f}%{Colors.RESET}")
        
        print(f"Results saved to: {Colors.BLUE}{output_manager.run_dir}{Colors.RESET}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error running benchmark: {e}")
        traceback.print_exc()
        tracker.save_checkpoint()
        raise


def main():
    """Main entry point."""
    args = parse_args()
    
    # Setup clean logging using the framework function
    # Use WARNING for clean output, INFO for verbose mode
    set_log_level("INFO" if args.verbose else "WARNING")
    
    # Validate team configuration exists
    config_dir = Path(__file__).parent / "config" / args.team
    if not config_dir.exists():
        print(f"Error: Team configuration directory not found: {config_dir}")
        print(f"Available teams: {[d.name for d in (Path(__file__).parent / 'config').iterdir() if d.is_dir()]}")
        sys.exit(1)
    
    # Run the benchmark
    try:
        asyncio.run(run_benchmark(
            team=args.team,
            limit=args.limit,
            concurrent_limit=args.concurrent,
            split=args.split,
            resume=args.resume,
            checkpoint_dir=args.checkpoint_dir,
            output_dir=args.output_dir,
            timeout=args.timeout,
            verbose=args.verbose
        ))
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Benchmark interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Benchmark failed: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main() 


# Convenience functions for pyproject.toml scripts
def team1():
    """Run benchmark with team1 configuration."""
    import sys
    sys.argv = ["benchmark", "--team", "team1"]
    main()


def team2():
    """Run benchmark with team2 configuration."""
    import sys
    sys.argv = ["benchmark", "--team", "team2"]
    main()


def team3():
    """Run benchmark with team3 configuration."""
    import sys
    sys.argv = ["benchmark", "--team", "team3"]
    main()


def quick_test():
    """Run a quick benchmark test with team3 and limited questions."""
    import sys
    sys.argv = ["benchmark", "--team", "team3", "--limit", "5", "--verbose"]
    main() 