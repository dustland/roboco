# SuperWriter - Advanced Research Report Generation System

SuperWriter is a comprehensive multi-agent system designed to generate professional, long-form research reports (50+ pages, 50k+ words) through autonomous collaboration between specialized AI agents.

## 🎯 Key Features

- **Long-form Content Generation**: Produces comprehensive reports of 50+ pages or 50k+ words
- **Autonomous Multi-Agent Workflow**: Planner → Researcher → Writer → Reviewer collaboration
- **Real-time Monitoring**: Track progress via observability platform at http://localhost:8506
- **Human Intervention**: Jump in with guidance messages during generation
- **Professional Quality**: Academic-grade research with proper citations and structure
- **Artifact Management**: Automatic saving of research notes, drafts, and final reports

## 🚀 Quick Start

### Prerequisites

Set up your API key:

```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key"
# OR
export OPENAI_API_KEY="your-openai-api-key"
```

### Generate a Research Report

```bash
cd examples/superwriter

# Generate a comprehensive research report
python main.py "Tesla auto driving technology"

# Specify target length
python main.py "AI in healthcare" --length "100 pages"

# Run without real-time streaming
python main.py "Climate change solutions" --no-streaming

# Disable human intervention
python main.py "Quantum computing" --no-intervention
```

## 📊 Real-time Monitoring

While the report is being generated, you can:

1. **Monitor Progress**: Visit http://localhost:8506 to see real-time progress
2. **View Artifacts**: Check the `workspace/` directory for generated files
3. **Track Metrics**: See word count, agent activity, and completion status
4. **Intervene**: Provide guidance messages during handoffs (if enabled)

## 🤖 Agent Workflow

### 1. Planner Agent

- Creates comprehensive research methodology
- Defines report structure and section outlines
- Sets quality standards and success criteria

### 2. Researcher Agent

- Conducts extensive research using multiple sources
- Gathers data, statistics, and expert opinions
- Compiles research notes and source materials

### 3. Writer Agent

- Drafts sections based on research findings
- Maintains professional tone and academic rigor
- Creates structured, well-formatted content

### 4. Reviewer Agent

- Performs quality assurance and fact-checking
- Ensures completeness and coherence
- Validates citations and sources

## 📋 Report Structure

Generated reports include:

1. **Executive Summary** (2-3 pages)
2. **Introduction and Background** (5-7 pages)
3. **Current State Analysis** (8-10 pages)
4. **Technical Deep Dive** (10-15 pages)
5. **Market Analysis** (8-10 pages)
6. **Competitive Landscape** (6-8 pages)
7. **Challenges and Limitations** (5-7 pages)
8. **Future Outlook and Trends** (8-10 pages)
9. **Recommendations** (3-5 pages)
10. **Conclusion** (2-3 pages)
11. **References and Bibliography**
12. **Appendices** (technical details, data tables)

## 🛠️ Configuration

### Team Configuration

The system uses `config/team.yaml` which defines:

- **Agent Roles**: Specialized prompts and capabilities
- **Tool Access**: Research, writing, and analysis tools
- **Handoff Rules**: Collaboration workflow patterns
- **Quality Standards**: Guardrails and validation rules
- **Memory Management**: Long-term context retention

### Customization Options

```bash
# Use custom team configuration
python main.py "Your topic" --config path/to/custom/team.yaml

# Adjust target length
python main.py "Your topic" --length "75 pages"

# Control execution mode
python main.py "Your topic" --no-streaming --no-intervention
```

## 📁 Output Files

Generated artifacts are saved to `workspace/`:

```
workspace/
├── research_plan.md          # Initial research methodology
├── research_notes/           # Compiled research materials
│   ├── sources.md
│   ├── data_analysis.md
│   └── expert_opinions.md
├── drafts/                   # Section drafts
│   ├── executive_summary.md
│   ├── introduction.md
│   ├── technical_analysis.md
│   └── ...
├── final_report.md           # Complete compiled report
├── bibliography.md           # References and citations
└── appendices/               # Supporting materials
```

## 🔍 Quality Assurance

SuperWriter implements multiple quality checks:

- **Source Verification**: Validates credibility and recency
- **Fact Checking**: Cross-references claims with reliable sources
- **Citation Management**: Ensures proper academic formatting
- **Completeness Checks**: Verifies all required sections
- **Readability Analysis**: Maintains professional writing standards

## 🎛️ Advanced Features

### Human Intervention

During generation, you can provide guidance:

```
💡 Intervention opportunity - type 'INTERVENE: <message>' or press Enter to continue

INTERVENE: Focus more on the safety aspects of autonomous driving
INTERVENE: Include more recent 2024 developments
INTERVENE: Add comparison with European regulations
```

### Progress Tracking

Real-time metrics include:

- **Word Count**: Progress toward 50k+ word target
- **Agent Activity**: Current agent and task status
- **Handoffs**: Collaboration flow between agents
- **Artifacts**: Generated files and documents
- **Quality Scores**: Research and writing quality metrics

### Observability Platform

Access detailed monitoring at http://localhost:8506:

- Task execution timeline
- Agent conversation history
- Artifact generation tracking
- Performance metrics
- Error logs and debugging info

## 🏆 Success Criteria

A successful report generation includes:

- ✅ **Length**: Meets or exceeds 50k word target
- ✅ **Quality**: Professional, well-researched content
- ✅ **Structure**: Complete with all required sections
- ✅ **Sources**: Credible, recent, and properly cited
- ✅ **Coherence**: Logical flow and clear organization
- ✅ **Completeness**: Comprehensive coverage of topic

## 🔧 Troubleshooting

### Common Issues

**Generation stops early**: Check API key limits and increase timeout
**Low quality output**: Adjust temperature settings in team.yaml
**Missing sections**: Verify handoff rules and completion criteria
**Slow performance**: Consider using faster models or reducing scope

### Debug Mode

Enable detailed logging:

```bash
export AGENTX_LOG_LEVEL=DEBUG
python main.py "Your topic"
```

## 🚀 Competing with Manus

SuperWriter is designed to validate AgentX's capability to compete with advanced systems like Manus by demonstrating:

1. **Scale**: Generating substantial 50k+ word reports
2. **Quality**: Professional, publication-ready content
3. **Autonomy**: Minimal human intervention required
4. **Monitoring**: Real-time progress tracking and intervention
5. **Reliability**: Consistent, repeatable results

This example serves as a comprehensive test of AgentX's multi-agent orchestration, long-form content generation, and production-readiness capabilities.

## 📚 Next Steps

- Experiment with different research topics
- Customize agent prompts for specific domains
- Integrate additional research tools and databases
- Scale up to even longer reports (100k+ words)
- Add support for multiple output formats (PDF, LaTeX, etc.)
