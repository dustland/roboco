"""
Progress Tracker for GAIA Benchmark

Tracks progress, handles checkpoints, and provides real-time statistics.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


logger = logging.getLogger(__name__)


class TaskTracker:
    """Track progress and manage checkpoints for benchmark execution."""
    
    def __init__(self, output_dir: Path):
        """Initialize the task tracker."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.checkpoint_file = self.output_dir / "checkpoint.json"
        self.progress_file = self.output_dir / "progress.json"
        
        # Progress tracking
        self.start_time = None
        self.total_questions = 0
        self.completed_questions = 0
        self.successful_questions = 0
        self.failed_questions = 0
        self.timeout_questions = 0
        
        # Timing statistics
        self.processing_times = []
        self.level_stats = {
            "1": {"completed": 0, "successful": 0, "total": 0},
            "2": {"completed": 0, "successful": 0, "total": 0},
            "3": {"completed": 0, "successful": 0, "total": 0},
            "unknown": {"completed": 0, "successful": 0, "total": 0}
        }
        
        # Configuration
        self.team_name = ""
        self.split = ""
        
        # Load existing checkpoint if available
        self._load_checkpoint()
    
    def initialize(self, total_questions: int, team_name: str, split: str):
        """Initialize the tracker with run parameters."""
        self.total_questions = total_questions
        self.team_name = team_name
        self.split = split
        self.start_time = time.time()
        
        # Count questions by level for accurate tracking
        # This would need to be called with the actual questions
        self._save_checkpoint()
        
        logger.info(f"Initialized tracker for {total_questions} questions")
    
    def update_progress(self, result: Dict[str, Any]):
        """Update progress with a completed question result."""
        self.completed_questions += 1
        
        # Update status counts
        status = result.get("status", "unknown")
        if status == "completed":
            self.successful_questions += 1
        elif status == "timeout":
            self.timeout_questions += 1
        else:
            self.failed_questions += 1
        
        # Update timing
        processing_time = result.get("processing_time", 0)
        if processing_time > 0:
            self.processing_times.append(processing_time)
        
        # Update level statistics
        level = str(result.get("level", "unknown"))
        if level in self.level_stats:
            self.level_stats[level]["completed"] += 1
            if status == "completed":
                self.level_stats[level]["successful"] += 1
        
        # Update progress file
        self._update_progress_file()
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        # Calculate rates
        completion_rate = self.completed_questions / self.total_questions if self.total_questions > 0 else 0
        success_rate = self.successful_questions / self.completed_questions if self.completed_questions > 0 else 0
        
        # Calculate ETA
        if self.completed_questions > 0 and completion_rate > 0:
            eta_seconds = elapsed_time / completion_rate - elapsed_time
            eta_formatted = self._format_time(eta_seconds)
        else:
            eta_formatted = "Unknown"
        
        # Calculate average processing time
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        
        return {
            "team": self.team_name,
            "split": self.split,
            "total_questions": self.total_questions,
            "completed_questions": self.completed_questions,
            "successful_questions": self.successful_questions,
            "failed_questions": self.failed_questions,
            "timeout_questions": self.timeout_questions,
            "completion_rate": completion_rate,
            "success_rate": success_rate,
            "elapsed_time": elapsed_time,
            "elapsed_time_formatted": self._format_time(elapsed_time),
            "eta": eta_formatted,
            "avg_processing_time": avg_processing_time,
            "level_stats": self.level_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_success_rate(self) -> float:
        """Get current success rate as percentage."""
        if self.completed_questions == 0:
            return 0.0
        return (self.successful_questions / self.completed_questions) * 100
    
    def save_checkpoint(self):
        """Save current progress to checkpoint file."""
        self._save_checkpoint()
        logger.debug("Checkpoint saved")
    
    def finalize(self):
        """Finalize tracking and save final statistics."""
        final_summary = self.get_progress_summary()
        
        # Save final summary
        final_file = self.output_dir / "final_summary.json"
        with open(final_file, 'w') as f:
            json.dump(final_summary, f, indent=2)
        
        # Remove checkpoint file as run is complete
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        
        logger.info("Task tracking finalized")
    
    def _load_checkpoint(self):
        """Load existing checkpoint if available."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                
                self.start_time = data.get("start_time")
                self.total_questions = data.get("total_questions", 0)
                self.completed_questions = data.get("completed_questions", 0)
                self.successful_questions = data.get("successful_questions", 0)
                self.failed_questions = data.get("failed_questions", 0)
                self.timeout_questions = data.get("timeout_questions", 0)
                self.processing_times = data.get("processing_times", [])
                self.level_stats = data.get("level_stats", self.level_stats)
                self.team_name = data.get("team_name", "")
                self.split = data.get("split", "")
                
                logger.info(f"Loaded checkpoint: {self.completed_questions}/{self.total_questions} completed")
                
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
    
    def _save_checkpoint(self):
        """Save current state to checkpoint file."""
        data = {
            "start_time": self.start_time,
            "total_questions": self.total_questions,
            "completed_questions": self.completed_questions,
            "successful_questions": self.successful_questions,
            "failed_questions": self.failed_questions,
            "timeout_questions": self.timeout_questions,
            "processing_times": self.processing_times,
            "level_stats": self.level_stats,
            "team_name": self.team_name,
            "split": self.split,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def _update_progress_file(self):
        """Update the progress file with current statistics."""
        progress_data = self.get_progress_summary()
        
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update progress file: {e}")
    
    def _format_time(self, seconds: float) -> str:
        """Format time duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def print_progress(self):
        """Print current progress to console."""
        summary = self.get_progress_summary()
        
        print(f"\n{'='*50}")
        print(f"PROGRESS REPORT - {summary['team'].upper()}")
        print(f"{'='*50}")
        print(f"Completed: {summary['completed_questions']}/{summary['total_questions']} "
              f"({summary['completion_rate']*100:.1f}%)")
        print(f"Success Rate: {summary['success_rate']*100:.1f}%")
        print(f"Successful: {summary['successful_questions']}")
        print(f"Failed: {summary['failed_questions']}")
        print(f"Timeouts: {summary['timeout_questions']}")
        print(f"Elapsed: {summary['elapsed_time_formatted']}")
        print(f"ETA: {summary['eta']}")
        print(f"Avg Time/Question: {summary['avg_processing_time']:.1f}s")
        
        print(f"\nLevel Breakdown:")
        for level, stats in summary['level_stats'].items():
            if stats['completed'] > 0:
                success_rate = (stats['successful'] / stats['completed']) * 100
                print(f"  Level {level}: {stats['successful']}/{stats['completed']} ({success_rate:.1f}%)")
        
        print(f"{'='*50}\n") 