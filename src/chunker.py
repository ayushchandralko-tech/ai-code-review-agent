"""File chunking logic for handling large code files."""

from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class CodeChunk:
    """Represents a chunk of code."""
    content: str
    start_line: int
    end_line: int
    chunk_id: int
    context: str = ""  # Additional context about this chunk


class CodeChunker:
    """Chunk large code files into manageable pieces for LLM analysis."""
    
    def __init__(self, max_lines: int = 100, overlap_lines: int = 10):
        """
        Initialize the code chunker.
        
        Args:
            max_lines: Maximum number of lines per chunk
            overlap_lines: Number of overlapping lines between chunks
        """
        self.max_lines = max_lines
        self.overlap_lines = overlap_lines
    
    def chunk_code(self, source: str, filename: str = "") -> List[CodeChunk]:
        """
        Split source code into chunks.
        
        Args:
            source: Source code to chunk
            filename: Optional filename for context
            
        Returns:
            List of CodeChunk objects
        """
        lines = source.split('\n')
        
        if len(lines) <= self.max_lines:
            # No chunking needed
            return [CodeChunk(
                content=source,
                start_line=1,
                end_line=len(lines),
                chunk_id=0,
                context=f"File: {filename}"
            )]
        
        chunks = []
        chunk_id = 0
        
        for start_idx in range(0, len(lines), self.max_lines - self.overlap_lines):
            end_idx = min(start_idx + self.max_lines, len(lines))
            chunk_lines = lines[start_idx:end_idx]
            chunk_content = '\n'.join(chunk_lines)
            
            chunks.append(CodeChunk(
                content=chunk_content,
                start_line=start_idx + 1,
                end_line=end_idx,
                chunk_id=chunk_id,
                context=f"File: {filename} (Lines {start_idx + 1}-{end_idx})"
            ))
            
            chunk_id += 1
            
            # Stop if we've reached the end
            if end_idx >= len(lines):
                break
        
        return chunks
    
    def chunk_by_function(self, source: str, function_bounds: List[Tuple[int, int]]) -> List[CodeChunk]:
        """
        Chunk code by function boundaries.
        
        Args:
            source: Source code to chunk
            function_bounds: List of (start_line, end_line) tuples for functions
            
        Returns:
            List of CodeChunk objects
        """
        lines = source.split('\n')
        chunks = []
        
        for idx, (start, end) in enumerate(function_bounds):
            # Adjust for 0-based indexing
            start_idx = start - 1
            end_idx = min(end, len(lines))
            
            chunk_lines = lines[start_idx:end_idx]
            chunk_content = '\n'.join(chunk_lines)
            
            # Check if chunk is too large
            if len(chunk_lines) > self.max_lines:
                # Further chunk this function
                sub_chunks = self.chunk_code(chunk_content, f"function_chunk_{idx}")
                chunks.extend(sub_chunks)
            else:
                chunks.append(CodeChunk(
                    content=chunk_content,
                    start_line=start,
                    end_line=end,
                    chunk_id=idx,
                    context=f"Function chunk (Lines {start}-{end})"
                ))
        
        return chunks
    
    def merge_chunks(self, chunks: List[CodeChunk]) -> str:
        """
        Merge chunks back into a single source string.
        
        Args:
            chunks: List of CodeChunk objects to merge
            
        Returns:
            Merged source code
        """
        if not chunks:
            return ""
        
        # Sort chunks by start line
        sorted_chunks = sorted(chunks, key=lambda x: x.start_line)
        
        # Simple merge without deduplication
        # For production, you might want to handle overlaps better
        return '\n'.join(chunk.content for chunk in sorted_chunks)
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count (rough approximation)
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
