# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up API Key
Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Run the Application
```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## Quick Test

### Test with Local Directory
1. In the sidebar, enter your OpenAI API key
2. Select "Local Directory" input method
3. Enter: `src` (to review the source code of this project)
4. Click "Start Code Review"

### Test with GitHub Repository
1. In the sidebar, enter your OpenAI API key
2. Enter a GitHub URL (e.g., `https://github.com/octocat/Hello-World`)
3. Click "Start Code Review"

## Features to Try

- **Filter by Severity**: Click the severity filter to show only critical/high issues
- **Filter by Category**: Focus on security or performance issues
- **Confidence Filtering**: View high vs low confidence comments separately
- **Download Results**: Export to JSON, CSV, or Markdown

## Troubleshooting

**"Module not found" error**: Run `pip install -r requirements.txt`

**API key not working**: 
- Verify your OpenAI API key has credits
- Check that the key is set in the sidebar (for Streamlit) or .env file

**Repository cloning fails**:
- Ensure the repository is public
- Check your internet connection

**No comments generated**:
- Try with a repository that has more Python files
- Check the OpenAI API status

## Next Steps

- Deploy to Streamlit Cloud (see DEPLOYMENT.md)
- Add your GitHub token for PR commenting
- Customize the confidence threshold in the sidebar
