"""
Cost Calculator for LLM Usage Tracking

Uses LiteLLM's built-in cost tracking and completion_cost functions
to provide accurate cost calculation for LLM usage.
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import json
import litellm
import functools


@dataclass
class ModelUsage:
    """Usage statistics for a specific model."""
    model: str
    call_count: int = 0
    total_cost: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def add_call(self, cost: float, usage: Dict[str, Any]):
        """Add a single LLM call's usage and cost."""
        self.call_count += 1
        self.total_cost += cost
        self.prompt_tokens += usage.get("prompt_tokens", 0)
        self.completion_tokens += usage.get("completion_tokens", 0) 
        self.total_tokens += usage.get("total_tokens", 0)


class CostCalculator:
    """
    Calculator for LLM costs using LiteLLM's built-in cost tracking.
    
    Uses LiteLLM's completion_cost() function and model pricing data
    instead of maintaining custom pricing tables.
    """
    
    def __init__(self):
        self.model_usage: Dict[str, ModelUsage] = {}
        self._wrapped_agents = []

    # ============================================================================
    # DIRECT USAGE TRACKING (existing methods)
    # ============================================================================

    def add_completion_response(self, response) -> float:
        """
        Add usage data from a LiteLLM completion response.
        
        Args:
            response: LiteLLM completion response object
            
        Returns:
            float: Cost of this completion
        """
        try:
            # Use LiteLLM's built-in cost calculation
            cost = litellm.completion_cost(completion_response=response)
            
            # Extract model and usage data
            model = response.model
            usage = response.usage
            
            if usage:
                # Handle different usage object formats
                if hasattr(usage, 'model_dump'):
                    usage_dict = usage.model_dump()
                elif hasattr(usage, 'dict'):
                    usage_dict = usage.dict()
                else:
                    usage_dict = usage
                self._add_usage(model, cost, usage_dict)
            
            return cost
            
        except Exception as e:
            print(f"Error calculating cost from completion response: {e}")
            return 0.0
    
    def add_streaming_finish(self, model: str, usage: Optional[Dict[str, Any]]) -> float:
        """
        Add usage data from streaming finish event.
        
        Args:
            model: Model name
            usage: Usage data from streaming response
            
        Returns:
            float: Cost of this completion
        """
        if not usage:
            return 0.0
            
        try:
            # Extract usage data - handle both dict and object formats
            if hasattr(usage, 'model_dump'):
                usage_dict = usage.model_dump()
            elif hasattr(usage, 'dict'):
                usage_dict = usage.dict()
            else:
                usage_dict = usage
            
            # Get token counts
            prompt_tokens = usage_dict.get("prompt_tokens", 0)
            completion_tokens = usage_dict.get("completion_tokens", 0)
            
            # Use LiteLLM's completion_cost with prompt+completion strings
            # This is more accurate than cost_per_token according to the docs
            cost = 0.0
            try:
                # Create dummy prompt and completion strings for cost calculation
                prompt = "x" * prompt_tokens  # Approximate prompt
                completion = "x" * completion_tokens  # Approximate completion
                
                cost = litellm.completion_cost(
                    model=model,
                    prompt=prompt,
                    completion=completion
                )
            except Exception:
                # Fallback: try with provider prefix
                try:
                    # Add common provider prefixes if missing
                    model_with_prefix = model
                    if "/" not in model and model.startswith("deepseek"):
                        model_with_prefix = f"deepseek/{model}"
                    
                    cost = litellm.completion_cost(
                        model=model_with_prefix,
                        prompt=prompt,
                        completion=completion
                    )
                except Exception as fallback_error:
                    print(f"Could not calculate cost for model {model}: {fallback_error}")
                    # Use LiteLLM model cost data directly as final fallback
                    try:
                        model_costs = litellm.model_cost
                        model_key = model_with_prefix if "/" in model_with_prefix else model
                        if model_key in model_costs:
                            model_data = model_costs[model_key]
                            input_cost = model_data.get("input_cost_per_token", 0)
                            output_cost = model_data.get("output_cost_per_token", 0)
                            cost = (prompt_tokens * input_cost) + (completion_tokens * output_cost)
                        else:
                            # Very rough fallback estimate
                            cost = (prompt_tokens * 0.0000001) + (completion_tokens * 0.0000002)
                    except Exception:
                        cost = (prompt_tokens * 0.0000001) + (completion_tokens * 0.0000002)
            
            self._add_usage(model, cost, usage_dict)
            return cost
            
        except Exception as e:
            print(f"Error calculating cost from streaming finish: {e}")
            return 0.0
    
    def _add_usage(self, model: str, cost: float, usage: Dict[str, Any]):
        """Add usage data for a model."""
        if model not in self.model_usage:
            self.model_usage[model] = ModelUsage(model=model)
        
        self.model_usage[model].add_call(cost, usage)

    # ============================================================================
    # AGENT BRAIN WRAPPING (new simpler approach)
    # ============================================================================

    def wrap_agent_brain(self, agent, agent_name: str):
        """
        Wrap an agent's brain methods to track usage directly.
        This is simpler and more reliable than callbacks.
        
        Args:
            agent: Agent instance to wrap
            agent_name: Name for debugging
        """
        if not hasattr(agent, 'brain'):
            print(f"[CostCalculator] Agent {agent_name} has no brain to wrap")
            return
            
        brain = agent.brain
        original_generate = brain.generate_response
        original_stream = brain.stream_response
        
        @functools.wraps(original_generate)
        async def wrapped_generate(*args, **kwargs):
            print(f"[CostCalculator] Wrapping generate_response for {agent_name}")
            try:
                response = await original_generate(*args, **kwargs)
                # Extract usage from response
                if hasattr(response, 'usage') and response.usage and hasattr(response, 'model'):
                    cost = self.add_streaming_finish(response.model, response.usage)
                    print(f"[CostCalculator] Tracked cost ${cost:.6f} for {agent_name}")
                return response
            except Exception as e:
                print(f"[CostCalculator] Error in wrapped generate_response: {e}")
                raise
        
        @functools.wraps(original_stream)
        async def wrapped_stream(*args, **kwargs):
            print(f"[CostCalculator] Wrapping stream_response for {agent_name}")
            try:
                async for chunk in original_stream(*args, **kwargs):
                    # Check for finish events with usage data
                    if chunk.get('type') == 'finish':
                        print(f"[CostCalculator] Finish chunk for {agent_name}: {chunk}")
                        if chunk.get('usage') and chunk.get('model'):
                            cost = self.add_streaming_finish(chunk['model'], chunk['usage'])
                            print(f"[CostCalculator] Tracked streaming cost ${cost:.6f} for {agent_name}")
                        else:
                            print(f"[CostCalculator] Finish chunk missing usage data: usage={chunk.get('usage')}, model={chunk.get('model')}")
                    yield chunk
            except Exception as e:
                print(f"[CostCalculator] Error in wrapped stream_response: {e}")
                raise
        
        # Replace the methods
        brain.generate_response = wrapped_generate
        brain.stream_response = wrapped_stream
        
        # Keep track for cleanup
        self._wrapped_agents.append((brain, original_generate, original_stream))
        print(f"[CostCalculator] Successfully wrapped brain methods for {agent_name}")

    def unwrap_agents(self):
        """Restore original brain methods."""
        for brain, original_generate, original_stream in self._wrapped_agents:
            brain.generate_response = original_generate
            brain.stream_response = original_stream
        self._wrapped_agents.clear()

    # ============================================================================
    # REPORTING METHODS (unchanged)
    # ============================================================================

    def get_total_cost(self) -> float:
        """Get total cost across all models."""
        return sum(usage.total_cost for usage in self.model_usage.values())
    
    def get_total_calls(self) -> int:
        """Get total number of LLM calls."""
        return sum(usage.call_count for usage in self.model_usage.values())
    
    def get_total_tokens(self) -> int:
        """Get total tokens used across all models."""
        total_prompt_tokens = sum(mu.prompt_tokens for mu in self.model_usage.values())
        total_completion_tokens = sum(mu.completion_tokens for mu in self.model_usage.values())
        total_tokens = sum(mu.total_tokens for mu in self.model_usage.values())
        
        # Use total_tokens if available, otherwise sum prompt + completion
        return total_tokens if total_tokens > 0 else (total_prompt_tokens + total_completion_tokens)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get detailed cost and usage summary."""
        total_cost = self.get_total_cost()
        total_calls = self.get_total_calls()
        total_tokens = self.get_total_tokens()
        
        summary = {
            "total_cost": total_cost,
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "models": {}
        }
        
        for model, usage in self.model_usage.items():
            summary["models"][model] = {
                "model": model,
                "call_count": usage.call_count,
                "total_cost": usage.total_cost,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "avg_cost_per_call": usage.total_cost / usage.call_count if usage.call_count > 0 else 0.0
            }
        
        return summary
    
    def print_summary(self):
        """Print a formatted cost summary."""
        summary = self.get_summary()
        
        print(f"\n💰 Cost Summary:")
        print(f"   Total Cost: ${summary['total_cost']:.6f}")
        print(f"   Total Calls: {summary['total_calls']}")
        print(f"   Total Tokens: {summary['total_tokens']}")
        
        if summary['models']:
            print(f"\n📊 By Model:")
            for model_data in summary['models'].values():
                print(f"   {model_data['model']}:")
                print(f"     Calls: {model_data['call_count']}")
                print(f"     Cost: ${model_data['total_cost']:.6f}")
                print(f"     Tokens: {model_data['total_tokens']} "
                      f"({model_data['prompt_tokens']} prompt + {model_data['completion_tokens']} completion)")
                print(f"     Avg/call: ${model_data['avg_cost_per_call']:.6f}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        summary = self.get_summary()
        summary["calculator_type"] = "litellm_native"
        return summary
    
    def save_to_file(self, filepath: str):
        """Save cost data to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def reset(self):
        """Reset all usage tracking."""
        self.model_usage.clear()
        # Don't clear wrapped agents as they might be reused 