"""LLM integration module for code review using OpenAI, GitHub Models, or Groq."""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
load_dotenv()


@dataclass
class ReviewComment:
    """Represents a code review comment."""
    file_path: str
    line_number: int
    severity: str  # 'critical', 'high', 'medium', 'low', 'info'
    category: str  # 'security', 'performance', 'style', 'bug', 'documentation', 'best_practice'
    message: str
    suggestion: str
    confidence: float  # 0.0 to 1.0
    code_snippet: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_markdown(self) -> str:
        """Convert to markdown format."""
        confidence_percent = int(self.confidence * 100)
        emoji = self._get_emoji()
        
        md = f"{emoji} **{self.severity.upper()}** - {self.category}\n\n"
        md += f"**File:** `{self.file_path}:{self.line_number}`\n"
        md += f"**Confidence:** {confidence_percent}%\n\n"
        md += f"**Issue:** {self.message}\n\n"
        md += f"**Suggestion:** {self.suggestion}\n\n"
        md += f"```python\n{self.code_snippet}\n```\n"
        md += "---\n"
        
        return md
    
    def _get_emoji(self) -> str:
        """Get emoji based on severity."""
        emojis = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '⚡',
            'low': '💡',
            'info': 'ℹ️'
        }
        return emojis.get(self.severity, '📝')


class LLMReviewer:
    """Review code using OpenAI, GitHub Models, or Groq."""
    
    SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge of software engineering best practices, security vulnerabilities, performance optimization, and clean code principles.

Your task is to review the provided code snippet and generate structured feedback in JSON format.

For each issue you identify, you must:
1. Assign a severity level: 'critical', 'high', 'medium', 'low', or 'info'
2. Categorize the issue: 'security', 'performance', 'style', 'bug', 'documentation', or 'best_practice'
3. Provide a clear, actionable message explaining the issue
4. Suggest a specific fix or improvement
5. Rate your confidence in this review (0.0 to 1.0) based on:
   - How clear the issue is
   - How certain you are about the fix
   - Whether there are alternative interpretations
   - Context completeness

Be conservative with confidence scores. If you're unsure, assign a lower confidence (0.3-0.6). If you're very certain, assign higher confidence (0.8-1.0).

IMPORTANT: Return ONLY a valid JSON array with the following structure:
[
  {
    "line_number": <int>,
    "severity": "<string>",
    "category": "<string>",
    "message": "<string>",
    "suggestion": "<string>",
    "confidence": <float between 0.0 and 1.0>
  }
]

If no issues are found, return an empty array: []

Do not include any text before or after the JSON. Do not use markdown code blocks. Return raw JSON only."""
    
    def __init__(self, model: str = "gpt-4o-mini", provider: str = "openai"):
        """
        Initialize the LLM reviewer.
        
        Args:
            model: Model to use (e.g., "gpt-4o-mini", "llama-3.1-70b-versatile")
            provider: Provider to use ("openai", "github", "groq")
        """
        self.model = model
        self.provider = provider
        
        if provider == "github":
            # Use GitHub Models
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                raise ValueError("GITHUB_TOKEN environment variable not set for GitHub Models")
            
            # GitHub Models uses Azure AI endpoint
            self.client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=github_token
            )
            print(f"Initialized GitHub Models client with model: {model}")
        elif provider == "groq":
            # Use Groq (free, fast, higher rate limits)
            groq_key = os.getenv("GROQ_API_KEY")
            if not groq_key:
                raise ValueError("GROQ_API_KEY environment variable not set for Groq")
            
            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key
            )
            print(f"Initialized Groq client with model: {model}")
        else:
            # Use OpenAI (default)
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self.client = OpenAI(api_key=openai_key)
            print(f"Initialized OpenAI client with model: {model}")
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type(Exception),
        retry_error_callback=lambda retry_state: None
    )
    def review_code(self, code: str, file_path: str, context: str = "") -> List[ReviewComment]:
        """
        Review a code snippet using the LLM.
        
        Args:
            code: Code snippet to review
            file_path: Path to the file being reviewed
            context: Additional context about the code
            
        Returns:
            List of ReviewComment objects
        """
        user_prompt = self._build_user_prompt(code, file_path, context)
        
        try:
            provider_name = {
                'github': 'GitHub Models',
                'groq': 'Groq',
                'openai': 'OpenAI'
            }.get(self.provider, self.provider)
            print(f"Sending request to {self.model} via {provider_name}")
            print(f"Code length: {len(code)} characters")
            
            # OpenAI-compatible API (OpenAI, GitHub Models, Groq)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            
            print(f"Received response from LLM, length: {len(content)}")
            
            result = json.loads(content)
            
            # Handle both array and object responses
            if isinstance(result, dict):
                comments_data = result.get("comments", result.get("issues", []))
            else:
                comments_data = result
            
            # Convert to ReviewComment objects
            comments = []
            for comment_data in comments_data:
                # Extract code snippet around the line
                line_number = comment_data.get("line_number", 1)
                code_snippet = self._extract_code_snippet(code, line_number)
                
                comment = ReviewComment(
                    file_path=file_path,
                    line_number=line_number,
                    severity=comment_data.get("severity", "info"),
                    category=comment_data.get("category", "best_practice"),
                    message=comment_data.get("message", ""),
                    suggestion=comment_data.get("suggestion", ""),
                    confidence=min(max(comment_data.get("confidence", 0.5), 0.0), 1.0),
                    code_snippet=code_snippet
                )
                comments.append(comment)
            
            print(f"Generated {len(comments)} review comments")
            return comments
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Raw response: {content}")
            return []
        except Exception as e:
            print(f"Error during LLM review: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _build_user_prompt(self, code: str, file_path: str, context: str) -> str:
        """Build the user prompt for the LLM."""
        prompt = f"""Review the following code from `{file_path}`.

"""
        if context:
            prompt += f"Context: {context}\n\n"
        
        prompt += f"""```python
{code}
```

Please analyze this code and provide your review in the specified JSON format."""
        
        return prompt
    
    def _extract_code_snippet(self, code: str, line_number: int, context_lines: int = 3) -> str:
        """Extract a code snippet around a specific line."""
        lines = code.split('\n')
        
        # Adjust for 1-based indexing
        line_idx = line_number - 1
        
        start_idx = max(0, line_idx - context_lines)
        end_idx = min(len(lines), line_idx + context_lines + 1)
        
        snippet_lines = lines[start_idx:end_idx]
        
        # Add line numbers
        numbered_lines = []
        for i, line in enumerate(snippet_lines, start=start_idx + 1):
            marker = ">>> " if i == line_number else "    "
            numbered_lines.append(f"{marker}{i}: {line}")
        
        return '\n'.join(numbered_lines)
    
    def review_multiple_chunks(self, chunks: List[tuple]) -> List[ReviewComment]:
        """
        Review multiple code chunks.
        
        Args:
            chunks: List of (code, file_path, context) tuples
            
        Returns:
            List of all ReviewComment objects
        """
        all_comments = []
        
        for code, file_path, context in chunks:
            comments = self.review_code(code, file_path, context)
            all_comments.extend(comments)
        
        return all_comments
    
    def filter_by_confidence(self, comments: List[ReviewComment], threshold: float = 0.7) -> tuple:
        """
        Filter comments by confidence threshold.
        
        Args:
            comments: List of ReviewComment objects
            threshold: Confidence threshold (0.0 to 1.0)
            
        Returns:
            Tuple of (high_confidence_comments, low_confidence_comments)
        """
        high_conf = [c for c in comments if c.confidence >= threshold]
        low_conf = [c for c in comments if c.confidence < threshold]
        
        return high_conf, low_conf
