# AI Code Review Agent

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-red.svg)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com/)

**An autonomous AI-powered code review system** that leverages Abstract Syntax Trees (AST) parsing and Large Language Models to generate confidence-rated review comments for Python repositories.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Output Format](#output-format)
- [Technical Implementation](#technical-implementation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [Future Roadmap](#future-roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The AI Code Review Agent demonstrates production-grade agentic AI capabilities through a fully autonomous pipeline that:

- **Clones** GitHub repositories using GitPython with automatic validation and cleanup
- **Parses** Python source code using Abstract Syntax Trees to extract functions, classes, and imports
- **Chunks** large files intelligently with overlap for optimal LLM processing
- **Reviews** code using OpenAI GPT-4o-mini to identify issues across multiple categories
- **Scores** confidence for each comment (0-100%) with built-in epistemic humility
- **Presents** results via an interactive Streamlit dashboard with advanced filtering

This system is designed for teams seeking automated code review with transparent confidence metrics, enabling developers to focus on high-impact issues while maintaining human oversight through confidence-based filtering.

---

## Key Features

### 🔍 Confidence Scoring
Every review comment includes a self-rated confidence score (0-100%). Low-confidence comments (<70%) are automatically flagged with "verify this" labels, demonstrating responsible AI practices and enabling appropriate human oversight.

### 🧩 Intelligent Chunking
Large files are automatically split into manageable chunks with configurable overlap to preserve context. The system handles files of any size while maintaining analysis quality.

### 📊 Multi-Category Analysis
Identifies issues across six distinct categories:
- **Security**: Vulnerabilities, authentication issues, data exposure
- **Performance**: Inefficient algorithms, resource usage, optimization opportunities
- **Style**: Code formatting, naming conventions, PEP 8 compliance
- **Bug**: Logic errors, edge cases, potential runtime failures
- **Documentation**: Missing or unclear docstrings, type hints
- **Best Practice**: Design patterns, code organization, maintainability

### 🎯 Severity Levels
Comments are categorized by impact:
- **Critical**: Security vulnerabilities, data loss risks
- **High**: Bugs that will cause failures
- **Medium**: Performance issues, code smells
- **Low**: Style improvements, minor issues
- **Info**: Documentation, suggestions

### 🔗 GitHub Integration
Optional feature to post comments directly to pull requests with formatted output, including confidence indicators and severity badges.

### 🖥️ Interactive Dashboard
- Real-time filtering by severity, category, and confidence
- Export results to JSON, CSV, or Markdown formats
- Progress tracking during analysis
- Configurable analysis parameters

## Architecture

The system follows a modular pipeline architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard                         │
│  (User Interface: Input, Configuration, Results Display)       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CodeReviewPipeline                           │
│                    (Orchestration Layer)                        │
│  - Coordinates all components                                  │
│  - Manages state and results                                   │
│  - Handles error recovery                                      │
└────────┬────────────────────────────────────────┬───────────────┘
         │                                        │
         ▼                                        ▼
┌──────────────────────┐              ┌──────────────────────┐
│    RepoCloner        │              │    ASTParser         │
│  (GitPython)         │              │  (Python ast)        │
│                      │              │                      │
│ - Clone repository   │              │ - Extract functions  │
│ - Validate URL       │              │ - Extract classes    │
│ - Cleanup            │              │ - Extract imports    │
│ - Get repo info      │              │ - Preserve line nums │
└──────────────────────┘              └──────────┬───────────┘
                                                 │
                                                 ▼
                                        ┌──────────────────────┐
                                        │    CodeChunker       │
│                      │              │                      │
│ - Split large files  │              │ - Add overlap        │
│ - Estimate tokens    │              │ - Preserve context    │
└──────────┬───────────┘              │ - Function-aware     │
           │                          └──────────┬───────────┘
           ▼                                     │
┌──────────────────────┐                          │
│    LLMReviewer       │◄─────────────────────────┘
│  (OpenAI GPT-4o)     │
│                      │
│ - Review code        │
│ - Generate comments  │
│ - Score confidence   │
│ - Filter by threshold│
│ - Retry logic        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  ReviewComment       │
│  (Data Model)        │
│                      │
│ - Severity           │
│ - Category           │
│ - Message            │
│ - Suggestion         │
│ - Confidence (0-1)   │
│ - Code snippet       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  GitHubPRCommenter   │
│  (Optional)          │
│                      │
│ - Post to PR         │
│ - Format comments    │
│ - Validate access    │
└──────────────────────┘
```

### Component Responsibilities

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Streamlit Dashboard** | Streamlit 1.31.0 | User interface, configuration, results visualization |
| **RepoCloner** | GitPython 3.1.43 | Repository cloning, validation, cleanup |
| **ASTParser** | Python ast | Code parsing, node extraction, line number tracking |
| **CodeChunker** | Custom | File splitting, token estimation, context preservation |
| **LLMReviewer** | OpenAI GPT-4o-mini | Code analysis, comment generation, confidence scoring |
| **GitHubPRCommenter** | PyGithub 2.1.1 | PR comment posting, formatting |
| **CodeReviewPipeline** | Custom | Orchestration, state management, error handling |

## Quick Start

### Prerequisites

- **Python 3.8+** - Download from [python.org](https://www.python.org/downloads/)
- **API Key** - Choose one:
  - **OpenAI API Key** - Obtain from [platform.openai.com](https://platform.openai.com/api-keys)
  - **GitHub Token** - For GitHub Models (free tier, rate limited), create at [github.com/settings/tokens](https://github.com/settings/tokens)
  - **Groq API Key** - For Groq (free, fast, higher rate limits), obtain from [console.groq.com](https://console.groq.com)
- **GitHub Token** (Optional) - For PR commenting, create at [github.com/settings/tokens](https://github.com/settings/tokens)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/ayushchandralko-tech/ai-code-review-agent.git
cd ai-code-review-agent
```

#### 2. Create Virtual Environment

```bash
# On Linux/macOS
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

```bash
cp .env.example .env
```

**Option A: Using OpenAI API**
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Option B: Using GitHub Models (Free Tier)**
```env
GITHUB_TOKEN=ghp_your-github-token-here
```

**Option C: Using Groq (Free, Faster, Higher Rate Limits)**
```env
GROQ_API_KEY=gsk_your-groq-api-key-here
```

Optionally add your GitHub token for PR commenting:
```env
GITHUB_PR_TOKEN=ghp_your-github-token-here
```

### Running the Application

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

The dashboard will automatically open at `http://localhost:8501`

---

## Usage

### GitHub Repository Review

1. **Select LLM Provider**: Choose between "OpenAI", "GitHub Models", or "Groq (Free)" in the sidebar
2. **Enter API Key**: 
   - For OpenAI: Input your OpenAI API key
   - For GitHub Models: Input your GitHub token (free tier, rate limited)
   - For Groq: Input your Groq API key (free, fast, higher rate limits)
3. **Provide Repository URL**: Enter a GitHub repository URL (e.g., `https://github.com/username/repository`)
4. **Optional PR Integration**: 
   - Enter the PR number to post comments directly
   - Provide the repository name in `owner/repo` format
5. **Start Review**: Click the "Start Code Review" button
6. **Review Results**: Explore the interactive dashboard with filtering options

### Local Directory Review

1. **Select LLM Provider**: Choose between "OpenAI", "GitHub Models", or "Groq (Free)" in the sidebar
2. **Enter API Key**: 
   - For OpenAI: Input your OpenAI API key
   - For GitHub Models: Input your GitHub token (free tier, rate limited)
   - For Groq: Input your Groq API key (free, fast, higher rate limits)
3. **Select Input Method**: Choose "Local Directory" from the input options
4. **Provide Path**: Enter the absolute path to your local code directory
5. **Start Review**: Click "Start Code Review"
6. **Review Results**: Analyze the generated comments and insights

### Configuration Options

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| **LLM Provider** | Choose between OpenAI, GitHub Models, or Groq | OpenAI | OpenAI, GitHub Models, Groq |
| **Confidence Threshold** | Minimum confidence for high-confidence comments | 0.7 | 0.0 - 1.0 |
| **LLM Model** | Model for code analysis | gpt-4o-mini | gpt-4o-mini, gpt-4o, llama-3.1-70b-versatile |
| **Max Files** | Limit number of files to analyze | None | 1 - 100 |

### Filtering Results

The dashboard provides advanced filtering capabilities:

- **Severity Filter**: Show only critical, high, medium, low, or info issues
- **Category Filter**: Focus on specific issue types (security, performance, etc.)
- **Confidence Filter**: View high-confidence (≥70%) or low-confidence (<70%) comments separately
- **Export Options**: Download results in JSON, CSV, or Markdown format

## Output Format

The agent generates structured review comments with the following schema:

```json
{
  "file_path": "src/example.py",
  "line_number": 42,
  "severity": "high",
  "category": "security",
  "message": "Potential SQL injection vulnerability",
  "suggestion": "Use parameterized queries instead of string concatenation",
  "confidence": 0.85,
  "code_snippet": ">>> 42: query = f\"SELECT * FROM users WHERE id = {user_id}\""
}
```

### Severity Classification

| Severity | Description | Examples |
|----------|-------------|----------|
| **Critical** | Security vulnerabilities, data loss risks | SQL injection, hardcoded credentials |
| **High** | Bugs that will cause failures | Null pointer exceptions, unhandled exceptions |
| **Medium** | Performance issues, code smells | Inefficient loops, duplicate code |
| **Low** | Style improvements, minor issues | Inconsistent naming, missing docstrings |
| **Info** | Documentation, suggestions | Type hints, best practice recommendations |

### Issue Categories

| Category | Focus Areas |
|----------|-------------|
| **Security** | Vulnerabilities, authentication, data exposure |
| **Performance** | Algorithm efficiency, resource usage, optimization |
| **Style** | Code formatting, naming conventions, PEP 8 compliance |
| **Bug** | Logic errors, edge cases, runtime failures |
| **Documentation** | Docstrings, type hints, code clarity |
| **Best Practice** | Design patterns, code organization, maintainability |

---

## Technical Implementation

### AST Parsing

The system leverages Python's built-in `ast` module for precise code analysis:

- **Function Extraction**: Captures function definitions with docstrings, decorators, and line numbers
- **Class Analysis**: Extracts class definitions with methods and inheritance information
- **Import Tracking**: Identifies all import statements for dependency analysis
- **Line Number Preservation**: Maintains precise line references for accurate commenting

### File Chunking Strategy

Large files are intelligently processed using a configurable chunking algorithm:

- **Chunk Size**: Maximum 100 lines per chunk (configurable)
- **Overlap**: 10-line overlap between chunks to preserve context
- **Function Awareness**: Attempts to chunk at function boundaries when possible
- **Token Estimation**: Pre-calculates token counts to optimize API usage

### Prompt Engineering

The system employs carefully engineered prompts to ensure consistent, high-quality output:

- **Structured JSON Schema**: Enforces consistent output format
- **Confidence Guidelines**: Instructs the LLM on confidence scoring methodology
- **Category Definitions**: Provides clear category boundaries
- **Severity Criteria**: Defines severity level requirements
- **Context Preservation**: Includes relevant code context in prompts

### Confidence Scoring Mechanism

The LLM evaluates confidence based on multiple factors:

- **Issue Clarity**: How clearly the problem is defined
- **Fix Certainty**: How certain the suggested fix is correct
- **Alternative Interpretations**: Whether other valid interpretations exist
- **Context Completeness**: Whether sufficient context is available
- **Code Complexity**: Impact of code complexity on analysis certainty

Comments with confidence < 70% are automatically flagged for manual verification, demonstrating responsible AI practices.

---

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
python test_pipeline.py
```

This validates:
- Repository cloning and URL validation
- AST parsing functionality
- Code chunking logic
- LLM integration (requires API key)
- Pipeline orchestration

### Integration Test

Test with a real repository:

```bash
python -c "
from src.pipeline import CodeReviewPipeline
pipeline = CodeReviewPipeline()
results = pipeline.review_repository('https://github.com/python/cpython', max_files=2)
print(pipeline.get_summary())
"
```

### Local Testing

Test with your local code:

```bash
python -c "
from src.pipeline import CodeReviewPipeline
pipeline = CodeReviewPipeline()
results = pipeline.review_local_directory('src')
print(pipeline.get_summary())
"
```

## Deployment

### Streamlit Cloud

Streamlit Cloud provides the simplest deployment path:

1. **Push to GitHub**: Ensure your repository is public on GitHub
2. **Access Streamlit Cloud**: Navigate to [share.streamlit.io](https://share.streamlit.io)
3. **Create New App**: Click "New app" and connect your GitHub account
4. **Configure App**:
   - Select repository: `ayushchandralko-tech/ai-code-review-agent`
   - Main file path: `app.py`
   - Click "Deploy"
5. **Add Secrets**:
   - Go to app settings → Secrets
   - Add one of the following:
     - For OpenAI: `OPENAI_API_KEY=sk-your-actual-key-here`
     - For GitHub Models: `GITHUB_TOKEN=ghp-your-token-here`
     - For Groq: `GROQ_API_KEY=gsk-your-token-here`
   - (Optional) Add: `GITHUB_PR_TOKEN=ghp-your-token-here` for PR comments
6. **Redeploy**: Click "Redeploy" to apply secrets

Your app will be available at: `https://ayushchandralko-tech-ai-code-review-agent.streamlit.app`

### HuggingFace Spaces

Alternative deployment using HuggingFace:

1. **Create Space**: Visit [huggingface.co/spaces](https://huggingface.co/spaces)
2. **Configure Space**:
   - Choose "Streamlit" as the SDK
   - Name your space
   - Make it public
3. **Upload Code**: Either:
   - Clone the space and push your code
   - Use the web interface to upload files
4. **Add Secrets**:
   - Go to Space Settings → Secrets
   - Add `OPENAI_API_KEY`
   - (Optional) Add `GITHUB_TOKEN`
5. **Deploy**: The space will automatically build and deploy

### Docker Deployment (Advanced)

For custom deployments, use the provided Dockerfile:

```bash
docker build -t ai-code-reviewer .
docker run -p 8501:8501 -e OPENAI_API_KEY=your-key ai-code-reviewer
```

---

## Project Structure

```
ai-code-reviewer/
├── app.py                      # Streamlit dashboard application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore configuration
├── README.md                  # Project documentation
├── DEPLOYMENT.md              # Detailed deployment guide
├── QUICKSTART.md              # Quick start guide
├── test_pipeline.py           # Test suite
├── src/
│   ├── __init__.py           # Package initialization
│   ├── repo_cloner.py        # Repository cloning module
│   ├── ast_parser.py         # AST parsing module
│   ├── chunker.py            # File chunking module
│   ├── llm_reviewer.py       # LLM integration module
│   ├── pipeline.py           # Main orchestration pipeline
│   ├── github_pr.py          # GitHub API integration
│   └── utils.py              # Utility functions
└── repos/                     # Cloned repositories (gitignored)
```

## Known Limitations

The current implementation has the following constraints:

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Python Only** | Only Python code can be analyzed | Future versions will support JavaScript, Go, TypeScript via tree-sitter |
| **File Size** | Files >10MB are automatically skipped | Use the max_files parameter for large repositories |
| **API Rate Limits** | OpenAI rate limits may affect large repositories | Implement rate limiting and retry logic (built-in) |
| **Binary Files** | Binary files are automatically skipped | System automatically detects and skips binary files |
| **Context Loss** | Chunking may lose context for very large functions | Configurable overlap helps preserve context |
| **False Positives** | LLM may generate false positives | Confidence scoring enables filtering of uncertain results |
| **Cost** | API costs scale with repository size | Use max_files parameter to limit analysis scope |

---

## Future Roadmap

Planned enhancements for future versions:

### Phase 1: Multi-Language Support
- [ ] Integrate tree-sitter for JavaScript, TypeScript, Go
- [ ] Language-specific parsing strategies
- [ ] Unified AST representation across languages

### Phase 2: Advanced Features
- [ ] Incremental analysis (only review changed files in PRs)
- [ ] Custom rule engine for team-specific standards
- [ ] Historical tracking and trend analysis
- [ ] Team collaboration and review sharing

### Phase 3: Automation
- [ ] Auto-fix capabilities using AI
- [ ] CI/CD integration (GitHub Actions, GitLab CI)
- [ ] Pre-commit hooks integration
- [ ] Automated PR creation with fixes

### Phase 4: Enterprise Features
- [ ] Cost estimation before analysis
- [ ] Response caching to reduce API costs
- [ ] Advanced metrics and scoring
- [ ] Role-based access control
- [ ] Audit logging and compliance

---

## Contributing

We welcome contributions from the community! Please follow these guidelines:

### Development Workflow

1. **Fork the Repository**: Create a fork on GitHub
2. **Create a Branch**: Use descriptive branch names (e.g., `feature/add-javascript-support`)
3. **Make Changes**: Implement your changes with clear commit messages
4. **Test**: Run the test suite to ensure no regressions
5. **Submit PR**: Create a pull request with a clear description

### Code Style

- Follow PEP 8 for Python code
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Write tests for new features

### Issue Reporting

When reporting issues, please include:
- Python version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages or logs

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 AI Code Review Agent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

This project was built using excellent open-source tools and services:

- **OpenAI** - GPT-4o-mini for code analysis
- **Streamlit** - Dashboard framework
- **GitPython** - Repository handling
- **Python AST Module** - Code parsing
- **PyGithub** - GitHub API integration

---

## Support

For questions, issues, or feature requests:

- **GitHub Issues**: [Create an issue](https://github.com/ayushchandralko-tech/ai-code-review-agent/issues)
- **Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment details
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md) for setup instructions

---

## Citation

If you use this project in your research or work, please cite:

```bibtex
@software{ai_code_review_agent,
  title = {AI Code Review Agent},
  author = {Ayush Chandralko},
  year = {2024},
  url = {https://github.com/ayushchandralko-tech/ai-code-review-agent}
}
```

---


