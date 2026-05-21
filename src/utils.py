"""Utility functions for error handling and edge case management."""

import os
import sys
from pathlib import Path
from typing import Optional, List, Any
import logging


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('code_review.log')
        ]
    )
    return logging.getLogger(__name__)


def validate_environment() -> tuple[bool, List[str]]:
    """
    Validate that required environment variables are set.
    
    Returns:
        Tuple of (is_valid, list_of_missing_vars)
    """
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return len(missing_vars) == 0, missing_vars


def validate_github_url(url: str) -> bool:
    """
    Validate GitHub repository URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    # Accept both HTTPS and SSH URLs
    valid_prefixes = [
        "https://github.com/",
        "git@github.com:"
    ]
    
    return any(url.startswith(prefix) for prefix in valid_prefixes)


def validate_local_directory(path: str) -> bool:
    """
    Validate that a local directory exists and is accessible.
    
    Args:
        path: Path to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not path:
        return False
    
    dir_path = Path(path)
    return dir_path.exists() and dir_path.is_dir()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def ensure_directory_exists(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to directory
    """
    path.mkdir(parents=True, exist_ok=True)


def safe_file_read(file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read a file with error handling.
    
    Args:
        file_path: Path to file
        encoding: File encoding
        
    Returns:
        File content or None if error
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def truncate_string(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format an error message with context.
    
    Args:
        error: Exception object
        context: Additional context
        
    Returns:
        Formatted error message
    """
    message = f"Error: {type(error).__name__}: {str(error)}"
    if context:
        message = f"{context}\n{message}"
    return message


def is_binary_file(file_path: Path) -> bool:
    """
    Check if a file is likely binary.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if likely binary, False otherwise
    """
    # Check file extension
    binary_extensions = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
        '.mp3', '.mp4', '.avi', '.mov'
    }
    
    if file_path.suffix.lower() in binary_extensions:
        return True
    
    # Try to read first few bytes
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            # Check for null bytes (common in binary files)
            if b'\x00' in chunk:
                return True
    except Exception:
        return True
    
    return False


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
    """
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def is_file_too_large(file_path: Path, max_size_mb: float = 10.0) -> bool:
    """
    Check if a file is too large to process.
    
    Args:
        file_path: Path to file
        max_size_mb: Maximum size in MB
        
    Returns:
        True if too large, False otherwise
    """
    return get_file_size_mb(file_path) > max_size_mb


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum calls per minute
        """
        self.calls_per_minute = calls_per_minute
        self.call_times = []
    
    def can_make_call(self) -> bool:
        """
        Check if a call can be made.
        
        Returns:
            True if call can be made, False otherwise
        """
        import time
        current_time = time.time()
        
        # Remove calls older than 1 minute
        self.call_times = [t for t in self.call_times if current_time - t < 60]
        
        return len(self.call_times) < self.calls_per_minute
    
    def record_call(self) -> None:
        """Record a call."""
        import time
        self.call_times.append(time.time())
    
    def wait_time(self) -> float:
        """
        Get time to wait before next call.
        
        Returns:
        """
        import time
        if not self.call_times:
            return 0.0
        
        current_time = time.time()
        oldest_call = min(self.call_times)
        time_until_free = 60 - (current_time - oldest_call)
        
        return max(0.0, time_until_free)
