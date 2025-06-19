"""
GAIA Benchmark Evaluator

Evaluates results against GAIA benchmark criteria and calculates metrics.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


logger = logging.getLogger(__name__)


class GAIAEvaluator:
    """Evaluate GAIA benchmark results and calculate metrics."""
    
    def __init__(self):
        """Initialize the evaluator."""
        pass
    
    def evaluate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate benchmark results and calculate comprehensive metrics.
        
        Args:
            results: List of question results
            
        Returns:
            Dictionary containing evaluation metrics
        """
        if not results:
            return self._empty_evaluation()
        
        # Separate results by status and level
        completed_results = [r for r in results if r.get("status") == "completed"]
        level_results = defaultdict(list)
        
        for result in results:
            level = str(result.get("level", "unknown"))
            level_results[level].append(result)
        
        # Calculate overall metrics
        total_questions = len(results)
        successful_questions = len(completed_results)
        success_rate = (successful_questions / total_questions) * 100 if total_questions > 0 else 0
        
        # Calculate accuracy (correct answers among completed)
        correct_answers = 0
        for result in completed_results:
            if self._is_answer_correct(result.get("predicted_answer", ""), 
                                     result.get("ground_truth", "")):
                correct_answers += 1
        
        overall_accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Calculate level-specific accuracies
        level_accuracies = {}
        for level in ["1", "2", "3"]:
            level_questions = level_results.get(level, [])
            if level_questions:
                level_correct = 0
                for result in level_questions:
                    if (result.get("status") == "completed" and 
                        self._is_answer_correct(result.get("predicted_answer", ""), 
                                              result.get("ground_truth", ""))):
                        level_correct += 1
                
                level_accuracy = (level_correct / len(level_questions)) * 100
                level_accuracies[f"level_{level}_accuracy"] = level_accuracy
            else:
                level_accuracies[f"level_{level}_accuracy"] = 0.0
        
        # Calculate timing statistics
        processing_times = [r.get("processing_time", 0) for r in results if r.get("processing_time", 0) > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        total_processing_time = sum(processing_times)
        
        # Calculate error statistics
        error_count = len([r for r in results if r.get("status") == "error"])
        timeout_count = len([r for r in results if r.get("status") == "timeout"])
        
        # Build comprehensive evaluation results
        evaluation = {
            "overall_accuracy": overall_accuracy,
            "success_rate": success_rate,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "successful_questions": successful_questions,
            "error_count": error_count,
            "timeout_count": timeout_count,
            
            # Level-specific accuracies
            **level_accuracies,
            
            # Timing statistics
            "avg_processing_time": avg_processing_time,
            "total_processing_time": total_processing_time,
            "min_processing_time": min(processing_times) if processing_times else 0,
            "max_processing_time": max(processing_times) if processing_times else 0,
            
            # Detailed breakdowns
            "level_breakdown": self._calculate_level_breakdown(level_results),
            "error_analysis": self._analyze_errors(results),
            "performance_distribution": self._calculate_performance_distribution(processing_times),
            
            # Metadata
            "evaluation_timestamp": json.dumps({"timestamp": "now"}),  # Placeholder
            "total_evaluated": len(results)
        }
        
        return evaluation
    
    def _is_answer_correct(self, predicted: str, ground_truth: str) -> bool:
        """
        Check if predicted answer matches ground truth.
        
        Uses GAIA's exact matching criteria with some normalization.
        """
        if not predicted or not ground_truth:
            return False
        
        # Normalize both answers
        predicted_norm = self._normalize_answer(predicted)
        ground_truth_norm = self._normalize_answer(ground_truth)
        
        # Exact match
        if predicted_norm == ground_truth_norm:
            return True
        
        # Check if predicted answer contains the ground truth (for cases where agent provides more context)
        if ground_truth_norm in predicted_norm:
            return True
        
        # Numeric comparison for numeric answers
        if self._is_numeric(predicted_norm) and self._is_numeric(ground_truth_norm):
            try:
                pred_num = float(predicted_norm.replace(",", ""))
                gt_num = float(ground_truth_norm.replace(",", ""))
                return abs(pred_num - gt_num) < 1e-6
            except ValueError:
                pass
        
        return False
    
    def _normalize_answer(self, answer: str) -> str:
        """Normalize answer for comparison."""
        if not answer:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = answer.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common punctuation at the end
        normalized = re.sub(r'[.!?]+$', '', normalized)
        
        # Remove quotes
        normalized = normalized.strip('"\'')
        
        return normalized
    
    def _is_numeric(self, text: str) -> bool:
        """Check if text represents a number."""
        try:
            float(text.replace(",", ""))
            return True
        except ValueError:
            return False
    
    def _calculate_level_breakdown(self, level_results: Dict[str, List]) -> Dict[str, Any]:
        """Calculate detailed breakdown by level."""
        breakdown = {}
        
        for level, results in level_results.items():
            if not results:
                continue
            
            total = len(results)
            completed = len([r for r in results if r.get("status") == "completed"])
            errors = len([r for r in results if r.get("status") == "error"])
            timeouts = len([r for r in results if r.get("status") == "timeout"])
            
            correct = 0
            for result in results:
                if (result.get("status") == "completed" and 
                    self._is_answer_correct(result.get("predicted_answer", ""), 
                                          result.get("ground_truth", ""))):
                    correct += 1
            
            accuracy = (correct / total) * 100 if total > 0 else 0
            success_rate = (completed / total) * 100 if total > 0 else 0
            
            breakdown[f"level_{level}"] = {
                "total_questions": total,
                "completed": completed,
                "correct": correct,
                "errors": errors,
                "timeouts": timeouts,
                "accuracy": accuracy,
                "success_rate": success_rate
            }
        
        return breakdown
    
    def _analyze_errors(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error patterns and types."""
        errors = [r for r in results if r.get("status") == "error"]
        timeouts = [r for r in results if r.get("status") == "timeout"]
        
        # Categorize error types
        error_types = defaultdict(int)
        for error in errors:
            error_msg = error.get("error", "Unknown error")
            if "timeout" in error_msg.lower():
                error_types["timeout"] += 1
            elif "api" in error_msg.lower() or "rate limit" in error_msg.lower():
                error_types["api_error"] += 1
            elif "parsing" in error_msg.lower() or "json" in error_msg.lower():
                error_types["parsing_error"] += 1
            else:
                error_types["other"] += 1
        
        return {
            "total_errors": len(errors),
            "total_timeouts": len(timeouts),
            "error_types": dict(error_types),
            "error_rate": (len(errors) / len(results)) * 100 if results else 0,
            "timeout_rate": (len(timeouts) / len(results)) * 100 if results else 0
        }
    
    def _calculate_performance_distribution(self, processing_times: List[float]) -> Dict[str, Any]:
        """Calculate performance distribution statistics."""
        if not processing_times:
            return {"count": 0}
        
        processing_times_sorted = sorted(processing_times)
        n = len(processing_times_sorted)
        
        return {
            "count": n,
            "mean": sum(processing_times) / n,
            "median": processing_times_sorted[n // 2],
            "p25": processing_times_sorted[n // 4],
            "p75": processing_times_sorted[3 * n // 4],
            "p90": processing_times_sorted[int(0.9 * n)],
            "p95": processing_times_sorted[int(0.95 * n)],
            "min": min(processing_times),
            "max": max(processing_times),
            "std": self._calculate_std(processing_times)
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _empty_evaluation(self) -> Dict[str, Any]:
        """Return empty evaluation results."""
        return {
            "overall_accuracy": 0.0,
            "level_1_accuracy": 0.0,
            "level_2_accuracy": 0.0,
            "level_3_accuracy": 0.0,
            "success_rate": 0.0,
            "total_questions": 0,
            "correct_answers": 0,
            "successful_questions": 0,
            "error_count": 0,
            "timeout_count": 0,
            "avg_processing_time": 0.0,
            "total_processing_time": 0.0,
            "min_processing_time": 0.0,
            "max_processing_time": 0.0,
            "level_breakdown": {},
            "error_analysis": {},
            "performance_distribution": {"count": 0},
            "total_evaluated": 0
        }
    
    def compare_teams(self, team_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare results across multiple teams.
        
        Args:
            team_results: Dictionary mapping team names to their evaluation results
            
        Returns:
            Comparison analysis
        """
        if not team_results:
            return {"teams": [], "comparison": {}}
        
        comparison = {
            "teams": list(team_results.keys()),
            "metrics": {},
            "rankings": {},
            "best_performers": {}
        }
        
        # Key metrics to compare
        key_metrics = [
            "overall_accuracy",
            "level_1_accuracy", 
            "level_2_accuracy", 
            "level_3_accuracy",
            "success_rate",
            "avg_processing_time"
        ]
        
        for metric in key_metrics:
            metric_values = {}
            for team, results in team_results.items():
                metric_values[team] = results.get(metric, 0)
            
            comparison["metrics"][metric] = metric_values
            
            # Create ranking (higher is better for accuracy/success, lower is better for time)
            if "time" in metric:
                # Lower is better for time metrics
                sorted_teams = sorted(metric_values.items(), key=lambda x: x[1])
            else:
                # Higher is better for accuracy/success metrics
                sorted_teams = sorted(metric_values.items(), key=lambda x: x[1], reverse=True)
            
            comparison["rankings"][metric] = [team for team, _ in sorted_teams]
            comparison["best_performers"][metric] = sorted_teams[0][0] if sorted_teams else None
        
        return comparison
    
    def generate_report(self, evaluation: Dict[str, Any], team_name: str) -> str:
        """Generate a human-readable evaluation report."""
        report = f"""
GAIA Benchmark Evaluation Report
{'='*50}

Team: {team_name}
Total Questions: {evaluation['total_questions']}
Evaluation Date: {evaluation.get('evaluation_timestamp', 'Unknown')}

ACCURACY RESULTS
{'='*20}
Overall Accuracy: {evaluation['overall_accuracy']:.2f}%
Level 1 Accuracy: {evaluation['level_1_accuracy']:.2f}%
Level 2 Accuracy: {evaluation['level_2_accuracy']:.2f}%
Level 3 Accuracy: {evaluation['level_3_accuracy']:.2f}%

COMPLETION STATISTICS
{'='*25}
Success Rate: {evaluation['success_rate']:.2f}%
Correct Answers: {evaluation['correct_answers']}/{evaluation['total_questions']}
Successful Completions: {evaluation['successful_questions']}/{evaluation['total_questions']}
Errors: {evaluation['error_count']}
Timeouts: {evaluation['timeout_count']}

PERFORMANCE METRICS
{'='*20}
Average Processing Time: {evaluation['avg_processing_time']:.2f}s
Total Processing Time: {evaluation['total_processing_time']:.2f}s
Min Processing Time: {evaluation['min_processing_time']:.2f}s
Max Processing Time: {evaluation['max_processing_time']:.2f}s

LEVEL BREAKDOWN
{'='*15}
"""
        
        level_breakdown = evaluation.get('level_breakdown', {})
        for level_key, level_data in level_breakdown.items():
            if level_data['total_questions'] > 0:
                report += f"{level_key.upper()}: {level_data['correct']}/{level_data['total_questions']} "
                report += f"({level_data['accuracy']:.1f}% accuracy)\n"
        
        return report 