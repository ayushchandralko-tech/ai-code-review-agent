"""Streamlit dashboard for the AI Code Review Agent."""

import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

from src.pipeline import CodeReviewPipeline
from src.llm_reviewer import ReviewComment
from src.github_pr import GitHubPRCommenter


# Page configuration
st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .confidence-high {
        color: #2ecc71;
        font-weight: bold;
    }
    .confidence-low {
        color: #e74c3c;
        font-weight: bold;
    }
    .severity-critical { color: #e74c3c; font-weight: bold; }
    .severity-high { color: #e67e22; font-weight: bold; }
    .severity-medium { color: #f39c12; font-weight: bold; }
    .severity-low { color: #3498db; font-weight: bold; }
    .severity-info { color: #95a5a6; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None
    if 'review_in_progress' not in st.session_state:
        st.session_state.review_in_progress = False


def render_sidebar():
    """Render the sidebar with configuration options."""
    st.sidebar.title("⚙️ Configuration")
    
    # LLM Provider selection
    llm_provider = st.sidebar.radio(
        "LLM Provider",
        ["OpenAI", "GitHub Models", "Groq (Free)", "Gemini (Free)"],
        help="Choose LLM provider: OpenAI (paid), GitHub Models (free, rate limited), Groq (free, faster), or Gemini (free, generous limits)"
    )
    
    if llm_provider == "OpenAI":
        # OpenAI API Key input
        api_key = st.sidebar.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key to enable code review"
        )
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
    elif llm_provider == "GitHub Models":
        # GitHub Token input
        github_token = st.sidebar.text_input(
            "GitHub Token",
            type="password",
            help="Enter your GitHub token for GitHub Models (free tier available, rate limited)"
        )
        if github_token:
            os.environ["GITHUB_TOKEN"] = github_token
    elif llm_provider == "Groq (Free)":
        # Groq API Key input
        groq_key = st.sidebar.text_input(
            "Groq API Key",
            type="password",
            help="Enter your Groq API key (free, fast, higher rate limits) - Get it from console.groq.com"
        )
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
    else:  # Gemini
        # Gemini API Key input
        gemini_key = st.sidebar.text_input(
            "Gemini API Key",
            type="password",
            help="Enter your Gemini API key (free, generous rate limits) - Get it from makersuite.google.com"
        )
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
    
    # GitHub Token for PR comments (optional, separate from LLM)
    st.sidebar.divider()
    pr_github_token = st.sidebar.text_input(
        "GitHub Token for PR Comments (Optional)",
        type="password",
        help="Enter your GitHub token to post PR comments (if different from LLM token)"
    )
    if pr_github_token:
        os.environ["GITHUB_PR_TOKEN"] = pr_github_token
    
    st.sidebar.divider()
    
    # Confidence threshold
    confidence_threshold = st.sidebar.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Minimum confidence for high-confidence comments"
    )
    
    # Model selection (based on provider)
    if llm_provider == "Groq (Free)":
        model = st.sidebar.selectbox(
            "LLM Model",
            ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            help="Select the Groq model to use for code review"
        )
    elif llm_provider == "Gemini (Free)":
        model = st.sidebar.selectbox(
            "LLM Model",
            ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
            help="Select the Gemini model to use for code review"
        )
    else:
        model = st.sidebar.selectbox(
            "LLM Model",
            ["gpt-4o-mini", "gpt-4o"],
            help="Select the model to use for code review"
        )
    
    # Max files (for testing)
    max_files = st.sidebar.number_input(
        "Max Files to Analyze",
        min_value=1,
        max_value=100,
        value=None,
        help="Limit the number of files to analyze (for testing)"
    )
    
    return confidence_threshold, model, max_files, llm_provider


def render_main_input():
    """Render the main input section."""
    st.markdown('<div class="main-header">🤖 AI Code Review Agent</div>', unsafe_allow_html=True)
    st.markdown("Autonomous code analysis with confidence-rated review comments")
    
    st.divider()
    
    # Input method selection
    input_method = st.radio(
        "Select Input Method",
        ["GitHub Repository URL", "Local Directory"],
        horizontal=True
    )
    
    if input_method == "GitHub Repository URL":
        repo_url = st.text_input(
            "Repository URL",
            placeholder="https://github.com/username/repository",
            help="Enter the GitHub repository URL to review"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            pr_number = st.number_input(
                "PR Number (Optional)",
                min_value=1,
                value=None,
                help="Enter PR number to post comments directly"
            )
        with col2:
            repo_name = st.text_input(
                "Repo Name (for PR)",
                placeholder="owner/repo",
                help="Required if posting to PR"
            )
        
        return input_method, repo_url, pr_number, repo_name
    else:
        local_dir = st.text_input(
            "Local Directory Path",
            placeholder="/path/to/your/code",
            help="Enter the path to a local directory to review"
        )
        
        return input_method, local_dir, None, None


def render_results(results):
    """Render the review results."""
    if not results:
        return
    
    # Summary metrics
    st.subheader("📊 Review Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Files Analyzed", results.get('files_analyzed', 0))
    with col2:
        st.metric("Code Nodes", results.get('nodes_extracted', 0))
    with col3:
        st.metric("Total Comments", results.get('comments_generated', 0))
    with col4:
        high_conf = results.get('high_confidence_comments', 0)
        st.metric("High Confidence", high_conf, delta_color="normal")
    with col5:
        low_conf = results.get('low_confidence_comments', 0)
        st.metric("Low Confidence", low_conf, delta_color="inverse")
    
    st.divider()
    
    # Repository info
    if results.get('repo_info'):
        st.subheader("📁 Repository Information")
        repo_info = results['repo_info']
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {repo_info.get('name', 'N/A')}")
            st.write(f"**Branch:** {repo_info.get('branch', 'N/A')}")
        with col2:
            st.write(f"**Commit:** {repo_info.get('commit', 'N/A')[:8]}...")
            st.write(f"**Author:** {repo_info.get('author', 'N/A')}")
        st.divider()
    
    # Comments section
    comments = results.get('comments', [])
    if not comments:
        st.info("No comments generated")
        return
    
    st.subheader("💬 Review Comments")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        severity_filter = st.multiselect(
            "Filter by Severity",
            ['critical', 'high', 'medium', 'low', 'info'],
            default=['critical', 'high', 'medium', 'low', 'info']
        )
    with col2:
        category_filter = st.multiselect(
            "Filter by Category",
            ['security', 'performance', 'style', 'bug', 'documentation', 'best_practice'],
            default=['security', 'performance', 'style', 'bug', 'documentation', 'best_practice']
        )
    with col3:
        confidence_filter = st.selectbox(
            "Filter by Confidence",
            ["All", "High (≥70%)", "Low (<70%)"],
            index=0
        )
    
    # Apply filters
    filtered_comments = []
    for comment in comments:
        # Severity filter
        if comment['severity'] not in severity_filter:
            continue
        
        # Category filter
        if comment['category'] not in category_filter:
            continue
        
        # Confidence filter
        if confidence_filter == "High (≥70%)" and comment['confidence'] < 0.7:
            continue
        if confidence_filter == "Low (<70%)" and comment['confidence'] >= 0.7:
            continue
        
        filtered_comments.append(comment)
    
    # Display comments
    if not filtered_comments:
        st.info("No comments match the selected filters")
        return
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["All Comments", "High Confidence", "Low Confidence"])
    
    with tab1:
        display_comments(filtered_comments, show_all=True)
    
    with tab2:
        high_conf = [c for c in filtered_comments if c['confidence'] >= 0.7]
        if high_conf:
            display_comments(high_conf, show_all=False)
        else:
            st.info("No high-confidence comments")
    
    with tab3:
        low_conf = [c for c in filtered_comments if c['confidence'] < 0.7]
        if low_conf:
            display_comments(low_conf, show_all=False, verify_label=True)
        else:
            st.info("No low-confidence comments")
    
    # Download options
    st.divider()
    st.subheader("📥 Download Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # JSON download
        json_str = json.dumps(results, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        # CSV download
        df = pd.DataFrame(filtered_comments)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col3:
        # Markdown download
        md_content = generate_markdown_report(filtered_comments, results)
        st.download_button(
            label="Download Markdown",
            data=md_content,
            file_name=f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )


def display_comments(comments, show_all=True, verify_label=False):
    """Display comments in a formatted way."""
    for i, comment in enumerate(comments):
        with st.expander(
            f"{get_emoji(comment['severity'])} {comment['severity'].upper()} - {comment['category']} "
            f"(Line {comment['line_number']}) - Confidence: {int(comment['confidence'] * 100)}%"
        ):
            st.write(f"**File:** `{comment['file_path']}`")
            st.write(f"**Line:** {comment['line_number']}")
            
            confidence_class = "confidence-high" if comment['confidence'] >= 0.7 else "confidence-low"
            st.markdown(f"**Confidence:** <span class='{confidence_class}'>{int(comment['confidence'] * 100)}%</span>", unsafe_allow_html=True)
            
            if verify_label and comment['confidence'] < 0.7:
                st.warning("⚠️ Low confidence - please verify this suggestion")
            
            st.write(f"**Issue:** {comment['message']}")
            st.write(f"**Suggestion:** {comment['suggestion']}")
            
            st.code(comment['code_snippet'], language='python')


def get_emoji(severity):
    """Get emoji for severity."""
    emojis = {
        'critical': '🚨',
        'high': '⚠️',
        'medium': '⚡',
        'low': '💡',
        'info': 'ℹ️'
    }
    return emojis.get(severity, '📝')


def generate_markdown_report(comments, results):
    """Generate a markdown report."""
    md = f"""# Code Review Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Files Analyzed:** {results.get('files_analyzed', 0)}
- **Code Nodes Extracted:** {results.get('nodes_extracted', 0)}
- **Total Comments:** {results.get('comments_generated', 0)}
- **High Confidence (≥70%):** {results.get('high_confidence_comments', 0)}
- **Low Confidence (<70%):** {results.get('low_confidence_comments', 0)}

"""
    
    if results.get('repo_info'):
        repo_info = results['repo_info']
        md += f"""## Repository Information

- **Name:** {repo_info.get('name', 'N/A')}
- **Branch:** {repo_info.get('branch', 'N/A')}
- **Commit:** {repo_info.get('commit', 'N/A')}
- **Author:** {repo_info.get('author', 'N/A')}

"""
    
    md += "## Review Comments\n\n"
    
    for comment in comments:
        confidence_percent = int(comment['confidence'] * 100)
        emoji = get_emoji(comment['severity'])
        
        md += f"{emoji} **{comment['severity'].upper()}** - {comment['category']}\n\n"
        md += f"**File:** `{comment['file_path']}`\n"
        md += f"**Line:** {comment['line_number']}\n"
        md += f"**Confidence:** {confidence_percent}%\n\n"
        md += f"**Issue:** {comment['message']}\n\n"
        md += f"**Suggestion:** {comment['suggestion']}\n\n"
        md += "```python\n"
        md += comment['code_snippet']
        md += "\n```\n\n"
        md += "---\n\n"
    
    return md


def main():
    """Main application function."""
    initialize_session_state()
    
    # Render sidebar
    confidence_threshold, model, max_files, llm_provider = render_sidebar()
    
    # Render main input
    input_method, input_value, pr_number, repo_name = render_main_input()
    
    # Review button
    st.divider()
    
    # Check if required API key is set
    if llm_provider == "OpenAI":
        api_key_set = bool(os.getenv("OPENAI_API_KEY"))
        warning_message = "⚠️ Please enter your OpenAI API Key in the sidebar to enable code review"
    elif llm_provider == "GitHub Models":
        api_key_set = bool(os.getenv("GITHUB_TOKEN"))
        warning_message = "⚠️ Please enter your GitHub Token in the sidebar to enable code review"
    elif llm_provider == "Groq (Free)":
        api_key_set = bool(os.getenv("GROQ_API_KEY"))
        warning_message = "⚠️ Please enter your Groq API Key in the sidebar to enable code review"
    else:  # Gemini
        api_key_set = bool(os.getenv("GEMINI_API_KEY"))
        warning_message = "⚠️ Please enter your Gemini API Key in the sidebar to enable code review"
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        review_button = st.button(
            "🚀 Start Code Review",
            type="primary",
            disabled=st.session_state.review_in_progress or not api_key_set
        )
    
    if not api_key_set:
        st.warning(warning_message)
    
    # Handle review request
    if review_button and api_key_set:
        st.session_state.review_in_progress = True
        
        try:
            # Create pipeline with correct provider
            if llm_provider == "GitHub Models":
                provider = "github"
            elif llm_provider == "Groq (Free)":
                provider = "groq"
            elif llm_provider == "Gemini (Free)":
                provider = "gemini"
            else:
                provider = "openai"
            
            pipeline = CodeReviewPipeline(
                confidence_threshold=confidence_threshold,
                provider=provider
            )
            pipeline.reviewer.model = model
            
            # Show progress
            progress_bar = st.progress(0, text="Initializing...")
            
            if input_method == "GitHub Repository URL":
                progress_bar.progress(10, text="Cloning repository...")
                results = pipeline.review_repository(input_value, max_files=max_files)
            else:
                progress_bar.progress(10, text="Analyzing local directory...")
                results = pipeline.review_local_directory(input_value)
            
            progress_bar.progress(100, text="Review complete!")
            
            # Store results
            st.session_state.results = results
            
            # Post to GitHub PR if requested
            if pr_number and repo_name and results.get('comments'):
                st.info(f"Posting comments to PR #{pr_number}...")
                commenter = GitHubPRCommenter()
                comments = [ReviewComment(**c) for c in results['comments']]
                success = commenter.post_review_comments(
                    repo_name,
                    pr_number,
                    comments,
                    min_confidence=confidence_threshold
                )
                if success:
                    st.success(f"✅ Successfully posted comments to PR #{pr_number}")
                else:
                    st.error("❌ Failed to post comments to PR")
            
        except Exception as e:
            st.error(f"Error during review: {str(e)}")
            st.session_state.results = {"error": str(e)}
        
        finally:
            st.session_state.review_in_progress = False
            st.rerun()
    
    # Display results
    if st.session_state.results:
        render_results(st.session_state.results)


if __name__ == "__main__":
    main()
