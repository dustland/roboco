"""
GAIA Dataset Loader

Handles loading and preprocessing of the GAIA benchmark dataset.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


class GAIADataLoader:
    """Load and preprocess GAIA benchmark data."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the data loader."""
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "datasets" / "gaia"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_dataset(self, split: str = "validation") -> List[Dict[str, Any]]:
        """
        Load GAIA dataset.
        
        Args:
            split: Dataset split to load ("validation" or "test")
            
        Returns:
            List of questions
        """
        if split == "validation":
            file_path = self.data_dir / "dev.json"
        elif split == "test":
            file_path = self.data_dir / "test.json"
        else:
            raise ValueError(f"Invalid split: {split}. Must be 'validation' or 'test'")
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"Dataset file not found: {file_path}\n"
                f"Please ensure the GAIA dataset is available at {self.data_dir}"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different data formats
            if isinstance(data, list):
                questions = data
            elif isinstance(data, dict) and 'data' in data:
                questions = data['data']
            else:
                raise ValueError(f"Unexpected data format in {file_path}")
            
            logger.info(f"Loaded {len(questions)} questions from {split} split")
            
            # Process and validate questions
            processed_questions = []
            for i, question in enumerate(questions):
                try:
                    processed_question = self._process_question(question, i)
                    processed_questions.append(processed_question)
                except Exception as e:
                    logger.warning(f"Skipping question {i}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(processed_questions)} questions")
            return processed_questions
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading dataset: {e}")
    
    def _process_question(self, question: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Process and validate a single question."""
        # Required fields
        if "Question" not in question:
            raise ValueError(f"Missing 'Question' field in question {index}")
        
        # Create standardized question format
        processed = {
            "id": question.get("task_id", f"gaia_{index}"),
            "task_id": question.get("task_id", f"gaia_{index}"),
            "Question": question["Question"],
            "Level": question.get("Level", "unknown"),
            "answer": question.get("answer", ""),  # Ground truth answer
            "Final answer": question.get("Final answer", ""),  # Keep for compatibility
            "file_name": question.get("file_name"),
            "file_path": question.get("file_path"),
            "Annotator Metadata": question.get("Annotator Metadata", {}),
            "index": index
        }
        
        # Validate level
        if processed["Level"] not in ["1", "2", "3", 1, 2, 3, "unknown"]:
            logger.warning(f"Invalid level '{processed['Level']}' for question {index}")
            processed["Level"] = "unknown"
        
        # Ensure level is string
        processed["Level"] = str(processed["Level"])
        
        return processed
    
    def get_dataset_stats(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the dataset."""
        stats = {
            "total_questions": len(questions),
            "level_1": len([q for q in questions if q.get("Level") == "1"]),
            "level_2": len([q for q in questions if q.get("Level") == "2"]),
            "level_3": len([q for q in questions if q.get("Level") == "3"]),
            "unknown_level": len([q for q in questions if q.get("Level") == "unknown"]),
            "with_files": len([q for q in questions if q.get("file_name")]),
            "without_files": len([q for q in questions if not q.get("file_name")])
        }
        
        return stats
    
    def sample_questions(
        self, 
        questions: List[Dict[str, Any]], 
        n: int, 
        strategy: str = "random"
    ) -> List[Dict[str, Any]]:
        """
        Sample questions from the dataset.
        
        Args:
            questions: List of questions to sample from
            n: Number of questions to sample
            strategy: Sampling strategy ("random", "balanced", "level_balanced")
            
        Returns:
            Sampled questions
        """
        if n >= len(questions):
            return questions
        
        if strategy == "random":
            import random
            return random.sample(questions, n)
        
        elif strategy == "balanced":
            # Try to balance across levels
            level_counts = {}
            for q in questions:
                level = q.get("Level", "unknown")
                level_counts[level] = level_counts.get(level, 0) + 1
            
            # Calculate samples per level
            levels = list(level_counts.keys())
            samples_per_level = n // len(levels)
            
            sampled = []
            for level in levels:
                level_questions = [q for q in questions if q.get("Level") == level]
                level_sample_size = min(samples_per_level, len(level_questions))
                
                import random
                sampled.extend(random.sample(level_questions, level_sample_size))
            
            # Fill remaining slots randomly
            remaining = n - len(sampled)
            if remaining > 0:
                available = [q for q in questions if q not in sampled]
                if available:
                    import random
                    sampled.extend(random.sample(available, min(remaining, len(available))))
            
            return sampled
        
        else:
            raise ValueError(f"Unknown sampling strategy: {strategy}")
    
    def validate_dataset(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate the dataset and return validation results."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": self.get_dataset_stats(questions)
        }
        
        for i, question in enumerate(questions):
            question_id = question.get("id", f"question_{i}")
            
            # Check required fields
            if not question.get("Question"):
                validation_results["errors"].append(
                    f"Question {question_id}: Missing or empty 'Question' field"
                )
                validation_results["valid"] = False
            
            # Check question length
            if len(question.get("Question", "")) < 10:
                validation_results["warnings"].append(
                    f"Question {question_id}: Very short question (< 10 chars)"
                )
            
            # Check if answer is provided (for validation split)
            if not question.get("Final answer"):
                validation_results["warnings"].append(
                    f"Question {question_id}: No final answer provided"
                )
        
        return validation_results 