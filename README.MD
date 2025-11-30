# ScholarLens 🔬

**AI-Powered Multi-Agent Research Paper Analyzer**

ScholarLens is an intelligent system that reads research papers (PDFs) and generates comprehensive multi-level analysis including summaries, methodology explanations, mathematical interpretations, critical analysis, and implementation guidance.

---

## 🌟 Features

### Multi-Level Analysis
- **📝 Summaries**: TL;DR, paragraph summary, detailed summary, key findings
- **🔬 Methodology**: Research approach, pipeline stages, data collection, validation
- **🔢 Math Interpretation**: Equation-by-equation explanations with intuitive meanings
- **🎯 Critical Analysis**: Assumptions, limitations, biases, reproducibility scoring
- **💻 Implementation**: Pseudo-code, complexity analysis, practical recommendations
- **📊 Aggregated Report**: Synthesized insights in JSON and Markdown formats

### Architecture
- **8 Specialized Agents**: Document extraction, summary, methodology, math, critique, implementation, aggregation, orchestration
- **Session Management**: In-memory storage with optional persistence
- **Observability**: Structured logging with agent tracing and timing
- **Evaluation Framework**: Quality metrics and completeness validation

---

## 📁 Project Structure

```
ScholarLens/
├── src/
│   ├── main.py                    # CLI entry point
│   ├── orchestrator.py            # Agent coordination
│   ├── agents/                    # Specialized agents
│   │   ├── base_agent.py         # Base class & schemas
│   │   ├── document_agent.py     # PDF extraction
│   │   ├── summary_agent.py      # Multi-level summaries
│   │   ├── method_agent.py       # Methodology analysis
│   │   ├── math_agent.py         # Equation interpretation
│   │   ├── critique_agent.py     # Critical analysis
│   │   ├── implementation_agent.py # Implementation guidance
│   │   └── aggregator_agent.py   # Report synthesis
│   ├── tools/                     # Utility tools
│   │   ├── pdf_parser.py         # PDF parsing (PyMuPDF/pdfplumber)
│   │   ├── text_cleaner.py       # Text preprocessing
│   │   └── code_exec.py          # Safe code execution
│   ├── utils/                     # Core utilities
│   │   ├── config.py             # Configuration
│   │   ├── logger.py             # Logging system
│   │   ├── chunking.py           # Text chunking
│   │   └── formatting.py         # Output formatting
│   ├── memory/                    # Session management
│   │   └── session_manager.py    # State storage
│   └── evaluation/                # Quality metrics
│       └── evaluator.py          # Report evaluation
├── data/
│   ├── samples/                   # Sample papers
│   └── outputs/                   # Generated reports
├── logs/                          # Application logs
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## 🚀 Quick Start

### 1. Installation

```powershell
# Clone repository
git clone https://github.com/MayeraaSingh/ScholarLens.git
cd ScholarLens

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration (Optional)

Set up Google Gemini API key for LLM features:

```powershell
# Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"

# Or create .env file
echo GEMINI_API_KEY=your_api_key_here > .env
```

> **Note**: Current version uses placeholder responses. LLM integration can be added by uncommenting `google-generativeai` in `requirements.txt` and implementing the `_call_llm()` methods in agent classes.

### 3. Analyze a Paper

```powershell
# Navigate to src directory
cd src

# Analyze a PDF
python main.py --pdf path/to/paper.pdf

# With specific session
python main.py --pdf paper.pdf --session abc123

# List all sessions
python main.py --list-sessions

# Get report for session
python main.py --get-report <session_id>

# Clear all sessions
python main.py --clear-sessions
```

---

## 📖 Usage Examples

### Basic Analysis

```powershell
python main.py --pdf ../data/samples/sample_paper.pdf
```

**Output**:
- JSON report: `data/outputs/sample_paper_YYYYMMDD_HHMMSS_report.json`
- Markdown report: `data/outputs/sample_paper_YYYYMMDD_HHMMSS_report.md`

### Advanced Options

```powershell
# Don't save to disk
python main.py --pdf paper.pdf --no-save

# Custom output directory
python main.py --pdf paper.pdf --output-dir custom/path

# Set log level
python main.py --pdf paper.pdf --log-level DEBUG
```

---

## 🏗️ Architecture

### Agent Workflow

```
User → main.py → OrchestratorAgent
                       ↓
         1. DocumentExtractorAgent (PDF → structured data)
                       ↓
         2. Analysis Agents (parallel execution):
            ├─ SummaryAgent
            ├─ MethodologyAgent
            ├─ MathAgent
            ├─ CritiqueAgent
            └─ ImplementationAgent
                       ↓
         3. AggregatorAgent (synthesize final report)
                       ↓
         Output: JSON + Markdown reports
```

### Agent Responsibilities

| Agent | Purpose | Key Outputs |
|-------|---------|-------------|
| **DocumentExtractor** | Parse PDF, extract structure | Title, authors, abstract, sections, equations |
| **Summary** | Generate multi-level summaries | TL;DR, paragraph, detailed, key findings |
| **Methodology** | Analyze research approach | Approach, pipeline stages, validation |
| **Math** | Interpret equations | Equation explanations, variable meanings |
| **Critique** | Critical analysis | Assumptions, limitations, biases, reproducibility |
| **Implementation** | Implementation guidance | Pseudo-code, complexity, recommendations |
| **Aggregator** | Synthesize all outputs | Final report (JSON + Markdown) |

---

## 🔧 Configuration

Edit `src/utils/config.py` to customize:

```python
# Model settings per agent
MODEL_CONFIGS = {
    "summary": ModelConfig(temperature=0.3, max_tokens=2048),
    "critique": ModelConfig(temperature=0.7, max_tokens=3072),
    # ... more configs
}

# Chunking configuration
CHUNKING_CONFIG = ChunkingConfig(
    chunk_size=8000,  # tokens
    overlap=500
)

# Session settings
MAX_SESSIONS = 100
SESSION_TIMEOUT_HOURS = 24
```

---

## 📊 Output Format

### JSON Report Structure

```json
{
  "metadata": {
    "title": "Paper Title",
    "authors": ["Author 1", "Author 2"],
    "num_pages": 12,
    "num_sections": 8
  },
  "summaries": {
    "tldr": "2-3 sentence summary",
    "paragraph_summary": "100-150 word summary",
    "detailed_summary": "500+ word summary",
    "key_findings": ["Finding 1", "Finding 2"]
  },
  "methodology": {
    "approach": "empirical",
    "pipeline_stages": ["Stage 1", "Stage 2"],
    "validation": "Cross-validation approach"
  },
  "math_explanations": {
    "interpretations": [...]
  },
  "critique": {
    "assumptions": ["Assumption 1"],
    "limitations": ["Limitation 1"],
    "reproducibility_score": 7.5
  },
  "implementation": {
    "pseudocode": [...],
    "complexity": {"time": "O(n)", "space": "O(n)"},
    "recommendations": ["Recommendation 1"]
  },
  "final_markdown": "..."
}
```

---

## 🧪 Testing

### Run Sample Analysis

```powershell
cd src

# Test with a sample PDF (add your own PDF to data/samples/)
python main.py --pdf ../data/samples/your_paper.pdf

# Check outputs
ls ../data/outputs/
```

### Validate Report Quality

```python
from evaluation import evaluate_report
import json

# Load report
with open('data/outputs/report.json', 'r') as f:
    report = json.load(f)

# Evaluate
evaluation = evaluate_report(report)
print(f"Overall Score: {evaluation['overall_score']}/100")
print(f"Recommendations: {evaluation['recommendations']}")
```

---

## 🛠️ Development

### Adding LLM Integration

1. Uncomment `google-generativeai` in `requirements.txt`
2. Install: `pip install google-generativeai`
3. Update `_call_llm()` in `agents/base_agent.py`:

```python
def _call_llm(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> str:
    from google.generativeai import GenerativeModel
    
    model = GenerativeModel(self.config.GEMINI_MODEL_NAME)
    response = model.generate_content(
        prompt,
        generation_config={
            'temperature': temperature,
            'max_output_tokens': max_tokens
        }
    )
    return response.text
```

### Adding New Agents

1. Create new agent file in `src/agents/`
2. Inherit from `BaseAgent`
3. Implement `run(self, data: Dict[str, Any]) -> Dict[str, Any]`
4. Register in `orchestrator.py`

---

## 📈 Performance

- **Average processing time**: 30-60 seconds per paper (without LLM)
- **Memory usage**: ~200-500MB per session
- **Supported PDF sizes**: Up to 50MB, 100+ pages
- **Concurrent sessions**: Up to 100 (configurable)

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- LLM integration (Gemini, GPT-4, Claude)
- Parallel agent execution
- Web interface
- Batch processing
- Additional output formats (HTML, LaTeX)
- Enhanced equation parsing
- Citation extraction and linking

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built with:
- PyMuPDF & pdfplumber for PDF parsing
- Pydantic for data validation
- Google Gemini (planned) for LLM capabilities

---

## 📞 Contact

- **Author**: MayeraaSingh
- **Repository**: https://github.com/MayeraaSingh/ScholarLens
- **Issues**: https://github.com/MayeraaSingh/ScholarLens/issues

---

**Happy Analyzing! 🔬✨**
