# GAIA Benchmark for AgentX Framework

A comprehensive benchmark implementation for evaluating agent teams on the GAIA (General AI Assistant) dataset using the AgentX multi-agent framework.

## Quick Start

### Using PyProject Scripts (Recommended)

The benchmark includes convenient scripts in `pyproject.toml` for easy execution:

```bash
# Quick test with 5 questions (team3)
uv run benchmark-quick

# Run full benchmark with specific teams
uv run benchmark-team1
uv run benchmark-team2
uv run benchmark-team3

# Run benchmark with custom options
uv run benchmark --team team1 --limit 10 --verbose
```

### Manual Execution

You can also run the benchmark manually:

```bash
# Run with team1 configuration
uv run python benchmark/main.py --team team1

# Run limited test with verbose output
uv run python benchmark/main.py --team team3 --limit 10 --verbose

# Resume from checkpoint
uv run python benchmark/main.py --team team1 --resume --checkpoint-dir results/team1_20231201_120000
```

## Available Scripts

- **`benchmark`**: Main benchmark script with full argument control
- **`benchmark-team1`**: Run benchmark with team1 configuration
- **`benchmark-team2`**: Run benchmark with team2 configuration
- **`benchmark-team3`**: Run benchmark with team3 configuration
- **`benchmark-quick`**: Quick test with team3 and 5 questions (verbose mode)

## Configuration

### Team Configurations

The benchmark includes three pre-configured team setups:

- **Team 1**: Multi-agent research team (Coordinator, Researcher, Analyst, Synthesizer)
- **Team 2**: Task-focused team (Planner, Executor, Validator)
- **Team 3**: Single agent setup (GAIA Agent)

Each team configuration is located in `config/team{1,2,3}/` with:

- `team.yaml`: Team structure and agent definitions
- `prompts/`: Individual agent prompt templates

### Options

- `--team`: Team configuration (team1, team2, team3)
- `--limit`: Limit number of questions for testing
- `--concurrent`: Number of concurrent tasks (default: 3)
- `--split`: Dataset split - validation or test (default: validation)
- `--timeout`: Timeout per question in seconds (default: 300)
- `--resume`: Resume from checkpoint
- `--checkpoint-dir`: Specific checkpoint directory
- `--output-dir`: Output directory for results (default: results)
- `--verbose`: Enable verbose logging

## Output

Results are saved to `results/` directory with:

- Individual question results (JSON)
- Final aggregated results
- Evaluation metrics
- Progress checkpoints

## Evaluation Metrics

- Overall accuracy
- Per-level accuracy (Level 1, 2, 3)
- Success rate
- Average processing time
- Total processing time

## Requirements

- Python 3.11+
- AgentX framework installed (`uv pip install -e .`)
- Required API keys (OpenAI, SERP API, etc.) configured in environment

## Overview

The GAIA benchmark tests AI systems on complex, realistic tasks that require:

- **Real-world knowledge** and information gathering
- **Multi-step reasoning** and problem decomposition
- **Tool usage** including web search and information verification
- **Precise answers** with exact format compliance

This implementation provides multiple team configurations for comprehensive evaluation of different multi-agent approaches.

## Team Configurations

### Team 1: Collaborative Research Team

**Approach**: Specialized multi-agent collaboration

- **Coordinator**: Task breakdown and team orchestration
- **Researcher**: Web search and information gathering
- **Analyst**: Data analysis and logical reasoning
- **Synthesizer**: Final answer formulation and quality control

**Model**: DeepSeek Chat (cost-optimized)  
**Best for**: Complex questions requiring specialized expertise

### Team 2: Sequential Planning Team

**Approach**: Structured planning and execution phases

- **Planner**: Systematic task planning and strategy development
- **Executor**: Comprehensive research execution
- **Validator**: Final answer validation and quality assurance

**Model**: Claude 3.5 Haiku (speed-optimized)  
**Best for**: Systematic approach with clear quality gates

### Team 3: Single Agent

**Approach**: Comprehensive single-agent solver

- **GAIA Agent**: End-to-end question solving with all tools

**Model**: DeepSeek Chat  
**Best for**: Baseline comparison and simpler questions

## Setup Instructions

### 1. Prerequisites

```bash
# Ensure AgentX is installed
pip install agentx-py

# Or install from source
cd /path/to/agentx
pip install -e .
```

### 2. Dataset Preparation

Download the GAIA dataset and place it in the datasets directory:

```bash
# Create datasets directory
mkdir -p benchmark/datasets/gaia

# Download GAIA validation set (dev.json) to:
# benchmark/datasets/gaia/dev.json
```

### 3. Environment Configuration

Set up your API keys and environment variables:

```bash
# For DeepSeek (recommended for cost efficiency)
export DEEPSEEK_API_KEY="your_deepseek_api_key"

# For Claude (if using team2)
export ANTHROPIC_API_KEY="your_anthropic_api_key"

# Optional: Enable verbose logging
export AGENTX_VERBOSE=1
```

## Usage

### Basic Usage

```bash
# Run with Team 1 (collaborative approach)
python benchmark/main.py --team team1

# Run with Team 2 (sequential planning)
python benchmark/main.py --team team2

# Run with Team 3 (single agent baseline)
python benchmark/main.py --team team3
```

### Advanced Usage

```bash
# Test with limited questions for development
python benchmark/main.py --team team1 --limit 10

# Run with custom concurrency and timeout
python benchmark/main.py --team team1 --concurrent-limit 5 --timeout 600

# Resume from checkpoint
python benchmark/main.py --team team1 --resume --checkpoint-dir results/team1_20240101_120000

# Enable verbose logging
python benchmark/main.py --team team1 --verbose

# Custom output directory
python benchmark/main.py --team team1 --output-dir my_results
```

### Comparing Teams

```bash
# Run all teams for comparison
python benchmark/main.py --team team1 --output-dir results/comparison
python benchmark/main.py --team team2 --output-dir results/comparison
python benchmark/main.py --team team3 --output-dir results/comparison
```

## Output Structure

Each benchmark run creates a timestamped directory with comprehensive results:

```
results/
└── team1_20240101_120000/
    ├── metadata.json          # Run configuration and metadata
    ├── results.json           # Complete results for all questions
    ├── results.jsonl          # Line-delimited JSON for easy processing
    ├── summary.json           # Statistical summary
    ├── evaluation.json        # GAIA evaluation metrics
    ├── report.txt             # Human-readable report
    ├── submission_team1.json  # GAIA leaderboard submission format
    ├── progress.json          # Real-time progress tracking
    ├── final_summary.json     # Final execution summary
    └── questions/             # Individual question results
        ├── question_1.json
        ├── question_2.json
        └── ...
```

## Key Metrics

The benchmark tracks comprehensive metrics aligned with GAIA evaluation:

### Accuracy Metrics

- **Overall Accuracy**: Percentage of correctly answered questions
- **Level 1/2/3 Accuracy**: Accuracy by difficulty level
- **Success Rate**: Percentage of questions completed (vs. errors/timeouts)

### Performance Metrics

- **Processing Time**: Average and total time per question
- **Cost Efficiency**: API costs (when available)
- **Throughput**: Questions processed per hour

### Quality Metrics

- **Error Rate**: Percentage of failed executions
- **Timeout Rate**: Percentage of questions that timed out
- **Source Verification**: Quality of research and fact-checking

## Configuration Customization

### Creating New Teams

1. Create new team directory: `benchmark/config/team4/`
2. Add `team.yaml` with agent configuration
3. Create prompts in `benchmark/config/team4/prompts/`
4. Run with `--team team4`

### Modifying Existing Teams

- **Models**: Change `brain.model` in team.yaml
- **Tools**: Modify `tools` list for each agent
- **Prompts**: Edit markdown files in prompts/ directory
- **Parameters**: Adjust temperature, memory settings, etc.

### Example Team Configuration

```yaml
name: "Custom Team"
description: "Description of approach"

brain:
  model: "deepseek/deepseek-chat"
  temperature: 0.1

memory:
  backend: "local"
  config:
    max_entries: 1000

routing_brain:
  model: "deepseek/deepseek-chat"
  temperature: 0.0

agents:
  agent_name:
    role: "Agent Role"
    prompt_file: "agent_prompt.md"
    brain:
      model: "deepseek/deepseek-chat"
      temperature: 0.2
    tools:
      - web_tools
      - search_tools
      - context_tools
```

## Best Practices

### For Development

- Start with `--limit 5` for quick testing
- Use `--verbose` to see detailed execution logs
- Test with different team configurations
- Monitor costs with cost-effective models

### For Evaluation

- Run complete dataset without limits
- Use appropriate `--concurrent-limit` for your setup
- Enable checkpointing for long runs
- Compare multiple team approaches

### For Production

- Use robust error handling and timeouts
- Monitor API rate limits and costs
- Scale concurrency based on resources
- Archive results for analysis

## Troubleshooting

### Common Issues

**"Dataset file not found"**

- Ensure dev.json is in benchmark/datasets/gaia/
- Check file permissions and path

**API Rate Limits**

- Reduce `--concurrent-limit`
- Add delays between requests
- Use multiple API keys if available

**Memory Issues**

- Reduce concurrent tasks
- Clear memory between questions
- Monitor system resources

**Timeout Issues**

- Increase `--timeout` value
- Check network connectivity
- Simplify complex questions for testing

### Performance Optimization

**Speed Optimization**

- Use Claude 3.5 Haiku or similar fast models
- Increase concurrent limits carefully
- Optimize search strategies

**Cost Optimization**

- Use DeepSeek or other cost-effective models
- Implement smart caching
- Optimize prompt lengths

**Accuracy Optimization**

- Use higher-capability models for complex questions
- Implement comprehensive verification
- Add multiple validation steps

## Contributing

### Adding New Team Configurations

1. Create team directory and configuration
2. Write comprehensive prompts
3. Test thoroughly with sample questions
4. Document approach and expected performance

### Improving Evaluation

- Enhance answer comparison logic
- Add new metrics and analysis
- Improve error handling and recovery
- Optimize performance and costs

### Dataset Management

- Support additional GAIA splits
- Implement data validation
- Add question categorization
- Enable subset selection

## License

This benchmark implementation follows the AgentX project license. The GAIA dataset has its own licensing terms - please refer to the original GAIA paper and dataset documentation.

## References

- [GAIA: A Benchmark for General AI Assistants](https://arxiv.org/abs/2311.12983)
- [AgentX Framework Documentation](../docs)
- [GAIA Leaderboard](https://gaia-benchmark.github.io)
