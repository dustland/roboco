"""
Output Manager for GAIA Benchmark

Manages file organization, result storage, and checkpoint handling.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set


logger = logging.getLogger(__name__)


class OutputManager:
    """Manage benchmark output files and organization."""
    
    def __init__(self, base_dir: str, run_id: str):
        """Initialize the output manager."""
        self.base_dir = Path(base_dir)
        self.run_id = run_id
        self.run_dir = self.base_dir / run_id
        
        # Create directory structure
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "questions").mkdir(exist_ok=True)
        (self.run_dir / "logs").mkdir(exist_ok=True)
        
        # Track saved questions
        self._saved_questions: Set[str] = set()
        
        # Initialize run metadata
        self._save_run_metadata()
        
        logger.info(f"Initialized output manager for run: {run_id}")
    
    @classmethod
    def from_checkpoint(cls, checkpoint_dir: str) -> 'OutputManager':
        """Create output manager from existing checkpoint directory."""
        checkpoint_path = Path(checkpoint_dir)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint directory not found: {checkpoint_dir}")
        
        # Extract run_id from directory name
        run_id = checkpoint_path.name
        base_dir = checkpoint_path.parent
        
        manager = cls(str(base_dir), run_id)
        manager._load_existing_questions()
        
        logger.info(f"Loaded output manager from checkpoint: {checkpoint_dir}")
        return manager
    
    def save_question_result(self, question_id: str, result: Dict[str, Any]):
        """Save individual question result."""
        try:
            question_file = self.run_dir / "questions" / f"{question_id}.json"
            
            with open(question_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self._saved_questions.add(question_id)
            
        except Exception as e:
            logger.error(f"Failed to save question result {question_id}: {e}")
    
    def save_final_results(self, results: List[Dict[str, Any]]):
        """Save final consolidated results."""
        try:
            # Save complete results
            results_file = self.run_dir / "results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            # Save summary statistics
            summary = self._calculate_summary_stats(results)
            summary_file = self.run_dir / "summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # Save results in JSONL format for easy processing
            jsonl_file = self.run_dir / "results.jsonl"
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
            
            logger.info(f"Saved final results: {len(results)} questions")
            
        except Exception as e:
            logger.error(f"Failed to save final results: {e}")
    
    def save_evaluation_results(self, evaluation: Dict[str, Any]):
        """Save evaluation results and metrics."""
        try:
            eval_file = self.run_dir / "evaluation.json"
            with open(eval_file, 'w', encoding='utf-8') as f:
                json.dump(evaluation, f, indent=2, ensure_ascii=False)
            
            # Save human-readable report
            if 'team_name' in evaluation:
                from .evaluator import GAIAEvaluator
                evaluator = GAIAEvaluator()
                report = evaluator.generate_report(evaluation, evaluation['team_name'])
                
                report_file = self.run_dir / "report.txt"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
            
            logger.info("Saved evaluation results")
            
        except Exception as e:
            logger.error(f"Failed to save evaluation results: {e}")
    
    def save_cost_summary(self, cost_summary: Dict[str, Any]):
        """Save cost tracking summary."""
        try:
            cost_file = self.run_dir / "cost_summary.json"
            with open(cost_file, 'w', encoding='utf-8') as f:
                json.dump(cost_summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved cost summary: ${cost_summary.get('total_cost', 0):.4f}")
            
        except Exception as e:
            logger.error(f"Failed to save cost summary: {e}")
    
    def get_completed_question_ids(self) -> Set[str]:
        """Get set of question IDs that have been completed."""
        return self._saved_questions.copy()
    
    def _save_run_metadata(self):
        """Save metadata about the current run."""
        metadata = {
            "run_id": self.run_id,
            "start_time": datetime.now().isoformat(),
            "base_dir": str(self.base_dir),
            "run_dir": str(self.run_dir)
        }
        
        try:
            metadata_file = self.run_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save run metadata: {e}")
    
    def _load_existing_questions(self):
        """Load existing question results from checkpoint."""
        questions_dir = self.run_dir / "questions"
        if not questions_dir.exists():
            return
        
        for question_file in questions_dir.glob("*.json"):
            question_id = question_file.stem
            self._saved_questions.add(question_id)
        
        logger.info(f"Loaded {len(self._saved_questions)} existing question results")
    
    def _calculate_summary_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for results."""
        if not results:
            return {"total_questions": 0}
        
        total = len(results)
        completed = len([r for r in results if r.get("status") == "completed"])
        errors = len([r for r in results if r.get("status") == "error"])
        timeouts = len([r for r in results if r.get("status") == "timeout"])
        
        # Calculate processing times
        processing_times = [r.get("processing_time", 0) for r in results if r.get("processing_time", 0) > 0]
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
        total_time = sum(processing_times)
        
        # Level breakdown
        level_stats = {}
        for level in ["1", "2", "3", "unknown"]:
            level_results = [r for r in results if str(r.get("level", "unknown")) == level]
            if level_results:
                level_completed = len([r for r in level_results if r.get("status") == "completed"])
                level_stats[f"level_{level}"] = {
                    "total": len(level_results),
                    "completed": level_completed,
                    "completion_rate": (level_completed / len(level_results)) * 100
                }
        
        return {
            "total_questions": total,
            "completed": completed,
            "errors": errors,
            "timeouts": timeouts,
            "completion_rate": (completed / total) * 100 if total > 0 else 0,
            "error_rate": (errors / total) * 100 if total > 0 else 0,
            "timeout_rate": (timeouts / total) * 100 if total > 0 else 0,
            "avg_processing_time": avg_time,
            "total_processing_time": total_time,
            "level_stats": level_stats,
            "generated_at": datetime.now().isoformat()
        }
    
    def create_comparative_report(self, team_results: Dict[str, Dict[str, Any]]) -> str:
        """Create a comparative report across multiple teams."""
        if not team_results:
            return "No team results to compare."
        
        report = f"""
GAIA Benchmark Comparative Report
{'='*40}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TEAM COMPARISON
{'='*15}
"""
        
        # Create comparison table
        teams = list(team_results.keys())
        metrics = ["overall_accuracy", "level_1_accuracy", "level_2_accuracy", "level_3_accuracy", "success_rate"]
        
        # Header
        report += f"{'Metric':<20}"
        for team in teams:
            report += f"{team:<15}"
        report += "\n" + "-" * (20 + 15 * len(teams)) + "\n"
        
        # Metrics rows
        for metric in metrics:
            metric_name = metric.replace("_", " ").title()
            report += f"{metric_name:<20}"
            
            for team in teams:
                value = team_results[team].get(metric, 0)
                if "accuracy" in metric or "rate" in metric:
                    report += f"{value:>13.1f}%"
                else:
                    report += f"{value:>13.1f} "
            report += "\n"
        
        # Best performers
        report += f"\nBEST PERFORMERS\n{'='*15}\n"
        for metric in metrics:
            best_team = max(teams, key=lambda t: team_results[t].get(metric, 0))
            best_value = team_results[best_team].get(metric, 0)
            metric_name = metric.replace("_", " ").title()
            report += f"{metric_name}: {best_team} ({best_value:.1f}%)\n"
        
        return report
    
    def export_for_submission(self, results: List[Dict[str, Any]], team_name: str) -> str:
        """Export results in format suitable for GAIA leaderboard submission."""
        submission_data = []
        
        for result in results:
            if result.get("status") == "completed":
                submission_entry = {
                    "task_id": result.get("question_id", result.get("id")),
                    "model_answer": result.get("predicted_answer", ""),
                }
                submission_data.append(submission_entry)
        
        # Save submission file
        submission_file = self.run_dir / f"submission_{team_name}.json"
        try:
            with open(submission_file, 'w', encoding='utf-8') as f:
                json.dump(submission_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported submission file: {submission_file}")
            return str(submission_file)
            
        except Exception as e:
            logger.error(f"Failed to export submission file: {e}")
            return "" 