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
from agentx import start_task

# Import benchmark utilities
from .utils.data_loader import GAIADataLoader
from .utils.progress_tracker import TaskTracker
from .utils.evaluator import GAIAEvaluator
from .utils.output_manager import OutputManager


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    import logging
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


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
    timeout: int = 300
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
        
        # Start the task
        task = start_task(task_content, team_config_path)
        
        # Execute with timeout and collect response
        final_response_parts = []
        
        async def execute_with_timeout():
            print(f"\n🤖 Processing Question: {question_id}")
            print(f"📋 Question: {question['Question'][:100]}{'...' if len(question['Question']) > 100 else ''}")
            print("💭 Agent thinking...\n")
            
            async for result in task.step(stream=True):
                if result.get("type") == "content":
                    content = result.get("content", "")
                    print(content, end="", flush=True)  # Stream the response in real-time
                    final_response_parts.append(content)
                elif result.get("type") == "routing_decision" and result.get("action") == "COMPLETE":
                    break
            
            print("\n")  # Add newline after completion
            return "".join(final_response_parts).strip()
        
        final_answer = await asyncio.wait_for(
            execute_with_timeout(),
            timeout=timeout
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare result
        result_data = {
            "question_id": question_id,
            "question": question["Question"],
            "predicted_answer": final_answer,
            "ground_truth": question.get("answer", ""),  # Use correct field name
            "level": question.get("Level", "unknown"),
            "processing_time": processing_time,
            "status": "completed",
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save individual result
        output_manager.save_question_result(question_id, result_data)
        
        return result_data
        
    except asyncio.TimeoutError:
        return {
            "question_id": question_id,
            "question": question["Question"],
            "predicted_answer": "",
            "ground_truth": question.get("answer", ""),  # Use correct field name
            "level": question.get("Level", "unknown"),
            "processing_time": timeout,
            "status": "timeout",
            "error": "Task timed out",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "question_id": question_id,
            "question": question["Question"],
            "predicted_answer": "",
            "ground_truth": question.get("answer", ""),  # Use correct field name
            "level": question.get("Level", "unknown"),
            "processing_time": 0,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def run_benchmark(
    team: str,
    limit: Optional[int] = None,
    concurrent_limit: int = 3,
    split: str = "validation",
    resume: bool = False,
    checkpoint_dir: Optional[str] = None,
    output_dir: str = "results",
    timeout: int = 300
) -> None:
    """Run the GAIA benchmark with specified configuration."""
    
    # Setup paths
    config_dir = Path(__file__).parent / "config" / team
    team_config_path = config_dir / "team.yaml"
    
    if not team_config_path.exists():
        raise FileNotFoundError(f"Team configuration not found: {team_config_path}")
    
    # Initialize components
    data_loader = GAIADataLoader()
    
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
        
        # Initialize tracker
        tracker.initialize(len(questions), team, split)
        
        # Resume from checkpoint if specified
        if resume:
            completed_ids = output_manager.get_completed_question_ids()
            questions = [q for q in questions if q.get("task_id", q.get("id")) not in completed_ids]
            print(f"Resuming: {len(questions)} questions remaining")
        
        # Process questions concurrently
        semaphore = asyncio.Semaphore(concurrent_limit)
        results = []
        
        async def process_with_semaphore(question):
            async with semaphore:
                result = await process_question(
                    question, 
                    str(team_config_path), 
                    output_manager, 
                    timeout
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
            
            # Print progress
            completed = i + 1
            total = len(tasks)
            success_rate = tracker.get_success_rate()
            
            print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%) - "
                  f"Success rate: {success_rate:.1f}%")
            
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
        
        # Print summary
        print("\n" + "="*60)
        print("BENCHMARK COMPLETED")
        print("="*60)
        print(f"Team: {team}")
        print(f"Total questions: {len(results)}")
        print(f"Overall accuracy: {evaluation_results['overall_accuracy']:.2f}%")
        print(f"Level 1 accuracy: {evaluation_results['level_1_accuracy']:.2f}%")
        print(f"Level 2 accuracy: {evaluation_results['level_2_accuracy']:.2f}%")
        print(f"Level 3 accuracy: {evaluation_results['level_3_accuracy']:.2f}%")
        print(f"Average processing time: {evaluation_results['avg_processing_time']:.2f}s")
        print(f"Total processing time: {evaluation_results['total_processing_time']:.2f}s")
        print(f"Success rate: {evaluation_results['success_rate']:.2f}%")
        print(f"Results saved to: {output_manager.run_dir}")
        print("="*60)
        
    except Exception as e:
        print(f"Error running benchmark: {e}")
        traceback.print_exc()
        tracker.save_checkpoint()
        raise


def main():
    """Main entry point."""
    args = parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
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
            timeout=args.timeout
        ))
    except KeyboardInterrupt:
        print("\n🛑 Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
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