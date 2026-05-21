# 🤖 AI Code Review Agent

An autonomous AI-powered code review system that clones repositories, analyzes code using Abstract Syntax Trees (AST), and generates confidence-rated review comments using Large Language Models.

## 🎯 Overview

This agent demonstrates production-grade agentic AI capabilities by autonomously:
- **Cloning** GitHub repositories using GitPython
- **Parsing** Python source code using AST to extract functions, classes, and imports
- **Chunking** large files intelligently for LLM processing
- **Reviewing** code with OpenAI GPT-4o-mini to identify issues
- **Scoring** confidence for each comment (0-100%) with epistemic humility
- **Presenting** results via an interactive Streamlit dashboard

## ✨ Key Features

- **Confidence Scoring**: Every comment includes a self-rated confidence score. Low-confidence comments (<70%) are flagged with "verify this" labels.
- **Intelligent Chunking**: Large files are automatically split into manageable chunks with overlap for context preservation.
- **Multi-Category Analysis**: Identifies issues across security, performance, style, bugs, documentation, and best practices.
- **Severity Levels**: Comments are categorized as critical, high, medium, low, or info.
- **GitHub Integration**: Optional feature to post comments directly to pull requests.
- **Interactive Dashboard**: Filter by severity, category, and confidence; export to JSON, CSV, or Markdown.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard                         │
│  (User Input: GitHub URL / Local Directory + Configuration)    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CodeReviewPipeline                           │
│                    (Orchestration Layer)                        │
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
└──────────────────────┘              └──────────┬───────────┘
                                                 │
                                                 ▼
                                        ┌──────────────────────┐
                                        │    CodeChunker       │
                                        │                      │
                                        │ - Split large files  │
                                        │ - Add overlap        │
                                        │ - Estimate tokens    │
                                        └──────────┬───────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────────┐
                                        │    LLMReviewer       │
                                        │  (OpenAI GPT-4o)     │
                                        │                      │
                                        │ - Review code        │
                                        │ - Generate comments  │
                                        │ - Score confidence   │
                                        │ - Filter by threshold│
                                        └──────────┬───────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────────┐
                                        │  ReviewComment       │
                                        │                      │
                                        │ - Severity           │
                                        │ - Category           │
                                        │ - Message            │
                                        │ - Suggestion         │
                                        │ - Confidence (0-1)   │
                                        │ - Code snippet       │
                                        └──────────────────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────────┐
                                        │  GitHubPRCommenter   │
                                        │  (Optional)          │
                                        │                      │
                                        │ - Post to PR         │
                                        │ - Format comments    │
                                        └──────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- (Optional) GitHub token for PR comments

### Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd git-code-reviewer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running the Application

Start the Streamlit dashboard:
```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 📖 Usage

### Via GitHub Repository URL

1. Enter your OpenAI API key in the sidebar
2. Enter a GitHub repository URL (e.g., `https://github.com/username/repo`)
3. (Optional) Enter PR number and repo name to post comments directly
4. Click "Start Code Review"
5. View results in the dashboard with filtering options

### Via Local Directory

1. Enter your OpenAI API key in the sidebar
2. Select "Local Directory" input method
3. Enter the path to your local code directory
4. Click "Start Code Review"

### Configuration Options

- **Confidence Threshold**: Filter comments by confidence (default: 0.7)
- **LLM Model**: Choose between gpt-4o-mini (faster, cheaper) or gpt-4o (more capable)
- **Max Files**: Limit the number of files analyzed (useful for testing)

## 📊 Output Formats

The agent generates review comments with the following structure:

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

### Severity Levels

- **Critical**: Security vulnerabilities, data loss risks
- **High**: Bugs that will cause failures
- **Medium**: Performance issues, code smells
- **Low**: Style improvements, minor issues
- **Info**: Documentation, suggestions

### Categories

- **Security**: Vulnerabilities, authentication issues
- **Performance**: Inefficient code, resource usage
- **Style**: Code formatting, naming conventions
- **Bug**: Logic errors, edge cases
- **Documentation**: Missing or unclear docs
- **Best Practice**: PEP 8, design patterns

## 🔧 Technical Details

### AST Parsing

The agent uses Python's built-in `ast` module to parse source code and extract:
- Function definitions with docstrings and decorators
- Class definitions with methods
- Import statements
- Line numbers for precise commenting

### File Chunking

Large files (>100 lines) are automatically chunked with:
- Maximum 100 lines per chunk
- 10-line overlap between chunks for context
- Function-aware chunking when possible

### Prompt Engineering

The system uses carefully engineered prompts to ensure:
- Consistent JSON output structure
- Appropriate confidence scoring
- Clear, actionable suggestions
- Proper categorization

### Confidence Scoring

The LLM is instructed to rate confidence based on:
- Clarity of the issue
- Certainty about the fix
- Alternative interpretations
- Context completeness

Low confidence (<70%) comments are flagged for manual verification.

## 🧪 Testing

Run a quick test with a small repository:

```bash
python -c "
from src.pipeline import CodeReviewPipeline
pipeline = CodeReviewPipeline()
results = pipeline.review_repository('https://github.com/python/cpython', max_files=2)
print(pipeline.get_summary())
"
```

## 🚢 Deployment

### Streamlit Cloud

1. Push your code to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" and connect your repository
4. Set the main file path to `app.py`
5. Add your OpenAI API key in the Secrets section
6. Deploy!

### HuggingFace Spaces

1. Create a new Space on [huggingface.co](https://huggingface.co/spaces)
2. Choose "Streamlit" as the SDK
3. Upload your code
4. Add `OPENAI_API_KEY` as a secret
5. Deploy!

## 📁 Project Structure

```
git-code-reviewer/
├── app.py                      # Streamlit dashboard
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── src/
│   ├── __init__.py
│   ├── repo_cloner.py         # Repository cloning
│   ├── ast_parser.py          # AST parsing
│   ├── chunker.py             # File chunking
│   ├── llm_reviewer.py        # LLM integration
│   ├── pipeline.py            # Main orchestration
│   ├── github_pr.py           # GitHub API integration
│   └── utils.py               # Utility functions
└── repos/                     # Cloned repositories (gitignored)
```

## ⚠️ Known Limitations

1. **Python Only**: Currently only supports Python code analysis
2. **File Size**: Very large files (>10MB) are skipped
3. **Rate Limits**: OpenAI API rate limits may affect large repositories
4. **Binary Files**: Binary files are automatically skipped
5. **Context Loss**: Chunking may lose some context for very large functions
6. **False Positives**: LLM may generate false positives, especially with low confidence

## 🔮 Future Improvements

With more time, I would add:

1. **Multi-language Support**: Add tree-sitter for JavaScript, Go, TypeScript, etc.
2. **Incremental Analysis**: Only review changed files in PRs
3. **Custom Rules**: Allow users to define custom review rules
4. **Historical Tracking**: Track review history over time
5. **Team Collaboration**: Share reviews with team members
6. **Auto-fix**: Automatically apply some fixes using AI
7. **CI/CD Integration**: GitHub Actions workflow
8. **Cost Estimation**: Show estimated API costs before review
9. **Caching**: Cache LLM responses to reduce costs
10. **Advanced Metrics**: Code quality scores, trend analysis

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenAI for GPT-4o-mini
- Streamlit for the excellent dashboard framework
- GitPython for repository handling
- Python AST module for code parsing

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

Built with ❤️ for the Agentic AI assignment
