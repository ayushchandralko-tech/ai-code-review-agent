"""Optional GitHub API integration for posting PR comments."""

import os
from typing import List, Optional
from github import Github, GithubException
from dotenv import load_dotenv
from src.llm_reviewer import ReviewComment

load_dotenv()


class GitHubPRCommenter:
    """Post code review comments to GitHub pull requests."""
    
    def __init__(self):
        """Initialize the GitHub PR commenter."""
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        if not self.github_token:
            print("Warning: GITHUB_TOKEN not set. GitHub integration disabled.")
            self.enabled = False
        else:
            self.github = Github(self.github_token)
            self.enabled = True
    
    def post_review_comments(
        self, 
        repo_name: str, 
        pr_number: int, 
        comments: List[ReviewComment],
        min_confidence: float = 0.7
    ) -> bool:
        """
        Post review comments to a GitHub pull request.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: Pull request number
            comments: List of ReviewComment objects
            min_confidence: Minimum confidence threshold for posting
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            print("GitHub integration is disabled (no GITHUB_TOKEN)")
            return False
        
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Filter comments by confidence
            high_conf_comments = [c for c in comments if c.confidence >= min_confidence]
            
            if not high_conf_comments:
                print(f"No comments above confidence threshold {min_confidence}")
                return True
            
            # Create a review with comments
            review_comments = []
            for comment in high_conf_comments:
                # Convert file path to be relative to repo root
                # The file_path from our pipeline might be absolute
                file_path = comment.file_path
                
                # Create the review comment
                review_comments.append({
                    'path': file_path,
                    'line': comment.line_number,
                    'body': self._format_comment_body(comment)
                })
            
            # Post the review
            pr.create_review(
                body=f"## AI Code Review\n\nGenerated {len(review_comments)} review comments with confidence ≥ {int(min_confidence * 100)}%.",
                comments=review_comments,
                event="COMMENT"  # Can be "APPROVE", "REQUEST_CHANGES", or "COMMENT"
            )
            
            print(f"Successfully posted {len(review_comments)} comments to PR #{pr_number}")
            return True
            
        except GithubException as e:
            print(f"GitHub API error: {e}")
            return False
        except Exception as e:
            print(f"Error posting comments: {e}")
            return False
    
    def _format_comment_body(self, comment: ReviewComment) -> str:
        """Format a comment for GitHub PR."""
        confidence_percent = int(comment.confidence * 100)
        
        body = f"**{comment.severity.upper()}** - {comment.category}\n\n"
        body += f"**Confidence:** {confidence_percent}%\n\n"
        body += f"{comment.message}\n\n"
        body += f"**Suggestion:** {comment.suggestion}\n\n"
        
        if comment.confidence < 0.7:
            body += "⚠️ *Low confidence - please verify this suggestion*"
        
        return body
    
    def post_summary_comment(
        self, 
        repo_name: str, 
        pr_number: int, 
        summary: str
    ) -> bool:
        """
        Post a summary comment to the PR.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: Pull request number
            summary: Summary text to post
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Create an issue comment (not a review comment)
            pr.create_issue_comment(summary)
            
            print(f"Successfully posted summary comment to PR #{pr_number}")
            return True
            
        except GithubException as e:
            print(f"GitHub API error: {e}")
            return False
        except Exception as e:
            print(f"Error posting summary: {e}")
            return False
    
    def validate_access(self, repo_name: str) -> bool:
        """
        Validate that we have access to the repository.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            
        Returns:
            True if accessible, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            repo = self.github.get_repo(repo_name)
            # Try to access the repo
            _ = repo.full_name
            return True
        except Exception as e:
            print(f"Cannot access repository {repo_name}: {e}")
            return False
