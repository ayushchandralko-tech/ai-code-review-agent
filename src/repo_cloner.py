"""Repository cloning module using GitPython."""

import os
import shutil
from pathlib import Path
from typing import Optional
import git
from git import Repo, GitCommandError


class RepoCloner:
    """Handles cloning and validation of GitHub repositories."""
    
    def __init__(self, base_dir: str = "repos"):
        """
        Initialize the repository cloner.
        
        Args:
            base_dir: Base directory for cloned repositories
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True, parents=True)
    
    def clone_repo(self, repo_url: str, target_name: Optional[str] = None) -> Path:
        """
        Clone a GitHub repository.
        
        Args:
            repo_url: URL of the repository to clone
            target_name: Optional custom name for the cloned directory
            
        Returns:
            Path to the cloned repository
            
        Raises:
            GitCommandError: If cloning fails
            ValueError: If URL is invalid
        """
        # Validate URL
        if not self._is_valid_github_url(repo_url):
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        # Determine target directory name
        if target_name:
            repo_name = target_name
        else:
            repo_name = self._extract_repo_name(repo_url)
        
        target_path = self.base_dir / repo_name
        
        # Remove existing directory if it exists
        if target_path.exists():
            shutil.rmtree(target_path)
        
        # Clone the repository
        try:
            Repo.clone_from(repo_url, target_path)
            print(f"Successfully cloned repository to {target_path}")
            return target_path
        except GitCommandError as e:
            raise GitCommandError(f"Failed to clone repository: {e}")
    
    def _is_valid_github_url(self, url: str) -> bool:
        """Validate if the URL is a valid GitHub repository URL."""
        return url.startswith(("https://github.com/", "git@github.com:"))
    
    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from GitHub URL."""
        # Handle both HTTPS and SSH URLs
        if url.startswith("https://"):
            # https://github.com/user/repo.git or https://github.com/user/repo
            parts = url.rstrip("/").split("/")
            repo_name = parts[-1].replace(".git", "")
        else:
            # git@github.com:user/repo.git
            parts = url.split(":")
            repo_path = parts[-1].replace(".git", "")
            # Extract just the repo name from user/repo
            repo_name = repo_path.split("/")[-1]
        
        return repo_name
    
    def cleanup(self, repo_path: Path) -> None:
        """
        Remove a cloned repository directory.
        
        Args:
            repo_path: Path to the repository to remove
        """
        if repo_path.exists():
            shutil.rmtree(repo_path)
            print(f"Cleaned up repository at {repo_path}")
    
    def get_repo_info(self, repo_path: Path) -> dict:
        """
        Get information about a cloned repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary with repository information
        """
        try:
            repo = Repo(repo_path)
            return {
                "name": repo_path.name,
                "path": str(repo_path),
                "branch": repo.active_branch.name,
                "commit": repo.head.commit.hexsha,
                "commit_message": repo.head.commit.message.strip(),
                "author": repo.head.commit.author.name,
                "is_dirty": repo.is_dirty()
            }
        except Exception as e:
            return {
                "name": repo_path.name,
                "path": str(repo_path),
                "error": str(e)
            }
