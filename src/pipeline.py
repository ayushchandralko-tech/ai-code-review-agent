"""Main orchestration pipeline for the code review agent."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from src.repo_cloner import RepoCloner
from src.ast_parser import ASTParser, CodeNode
from src.chunker import CodeChunker
from src.llm_reviewer import LLMReviewer, ReviewComment


class CodeReviewPipeline:
    """Orchestrates the entire code review pipeline."""
    
    def __init__(self, base_dir: str = "repos", confidence_threshold: float = 0.7, use_github_models: bool = False):
        """
        Initialize the code review pipeline.
        
        Args:
            base_dir: Base directory for cloned repositories
            confidence_threshold: Threshold for separating high/low confidence comments
            use_github_models: Whether to use GitHub Models instead of OpenAI
        """
        self.cloner = RepoCloner(base_dir)
        self.parser = ASTParser()
        self.chunker = CodeChunker(max_lines=100, overlap_lines=10)
        self.reviewer = LLMReviewer(model="gpt-4o-mini", use_github_models=use_github_models)
        self.confidence_threshold = confidence_threshold
        
        self.results = {
            "repo_info": None,
            "files_analyzed": 0,
            "nodes_extracted": 0,
            "comments_generated": 0,
            "high_confidence_comments": 0,
            "low_confidence_comments": 0,
            "start_time": None,
            "end_time": None,
            "comments": []
        }
    
    def review_repository(self, repo_url: str, max_files: Optional[int] = None) -> Dict[str, Any]:
        """
        Review a GitHub repository end-to-end.
        
        Args:
            repo_url: URL of the repository to review
            max_files: Maximum number of files to analyze (for testing)
            
        Returns:
            Dictionary with review results
        """
        self.results["start_time"] = datetime.now().isoformat()
        
        try:
            # Step 1: Clone repository
            print(f"Cloning repository: {repo_url}")
            repo_path = self.cloner.clone_repo(repo_url)
            self.results["repo_info"] = self.cloner.get_repo_info(repo_path)
            print(f"Repository cloned to: {repo_path}")
            
            # Step 2: Parse all Python files
            print("Parsing Python files...")
            all_nodes = self.parser.parse_directory(repo_path)
            self.results["files_analyzed"] = len(all_nodes)
            total_nodes = sum(len(nodes) for nodes in all_nodes.values())
            self.results["nodes_extracted"] = total_nodes
            print(f"Analyzed {len(all_nodes)} files with {total_nodes} code nodes")
            
            # Step 3: Limit files if specified
            if max_files:
                all_nodes = dict(list(all_nodes.items())[:max_files])
                print(f"Limited analysis to {max_files} files")
            
            # Step 4: Review each file
            print("Starting code review...")
            all_comments = []
            
            for file_path, nodes in all_nodes.items():
                print(f"  Reviewing: {file_path}")
                file_comments = self._review_file(file_path, nodes, repo_path)
                all_comments.extend(file_comments)
            
            # Step 5: Filter by confidence
            high_conf, low_conf = self.reviewer.filter_by_confidence(
                all_comments, 
                self.confidence_threshold
            )
            
            self.results["comments"] = [c.to_dict() for c in all_comments]
            self.results["comments_generated"] = len(all_comments)
            self.results["high_confidence_comments"] = len(high_conf)
            self.results["low_confidence_comments"] = len(low_conf)
            
            # Step 6: Cleanup
            print("Cleaning up...")
            self.cloner.cleanup(repo_path)
            
            self.results["end_time"] = datetime.now().isoformat()
            print(f"Review complete! Generated {len(all_comments)} comments.")
            
            return self.results
            
        except Exception as e:
            self.results["error"] = str(e)
            self.results["end_time"] = datetime.now().isoformat()
            print(f"Error during review: {e}")
            return self.results
    
    def _review_file(self, file_path: str, nodes: List[CodeNode], repo_path: Path) -> List[ReviewComment]:
        """
        Review a single file.
        
        Args:
            file_path: Path to the file
            nodes: AST nodes from the file
            repo_path: Base repository path
            
        Returns:
            List of ReviewComment objects
        """
        comments = []
        
        # Read the file content
        full_path = repo_path / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return comments
        
        # For each node, review the code
        for node in nodes:
            # Skip imports for now (usually not much to review)
            if node.node_type == 'import':
                continue
            
            # Check if node source is too large
            if len(node.source.split('\n')) > self.chunker.max_lines:
                # Chunk the node
                chunks = self.chunker.chunk_code(node.source, f"{file_path}:{node.name}")
                for chunk in chunks:
                    chunk_comments = self.reviewer.review_code(
                        chunk.content,
                        f"{file_path}:{node.name}",
                        chunk.context
                    )
                    comments.extend(chunk_comments)
            else:
                # Review the entire node
                node_comments = self.reviewer.review_code(
                    node.source,
                    f"{file_path}:{node.name}",
                    f"{node.node_type}: {node.name}"
                )
                comments.extend(node_comments)
        
        return comments
    
    def review_local_directory(self, directory: str) -> Dict[str, Any]:
        """
        Review a local directory without cloning.
        
        Args:
            directory: Path to local directory
            
        Returns:
            Dictionary with review results
        """
        self.results["start_time"] = datetime.now().isoformat()
        
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                raise ValueError(f"Directory does not exist: {directory}")
            
            # Parse all Python files
            print("Parsing Python files...")
            all_nodes = self.parser.parse_directory(dir_path)
            self.results["files_analyzed"] = len(all_nodes)
            total_nodes = sum(len(nodes) for nodes in all_nodes.values())
            self.results["nodes_extracted"] = total_nodes
            print(f"Analyzed {len(all_nodes)} files with {total_nodes} code nodes")
            
            # Review each file
            print("Starting code review...")
            all_comments = []
            
            for file_path, nodes in all_nodes.items():
                print(f"  Reviewing: {file_path}")
                file_comments = self._review_file(file_path, nodes, dir_path)
                all_comments.extend(file_comments)
            
            # Filter by confidence
            high_conf, low_conf = self.reviewer.filter_by_confidence(
                all_comments, 
                self.confidence_threshold
            )
            
            self.results["comments"] = [c.to_dict() for c in all_comments]
            self.results["comments_generated"] = len(all_comments)
            self.results["high_confidence_comments"] = len(high_conf)
            self.results["low_confidence_comments"] = len(low_conf)
            
            self.results["end_time"] = datetime.now().isoformat()
            print(f"Review complete! Generated {len(all_comments)} comments.")
            
            return self.results
            
        except Exception as e:
            self.results["error"] = str(e)
            self.results["end_time"] = datetime.now().isoformat()
            print(f"Error during review: {e}")
            return self.results
    
    def save_results(self, output_path: str = "review_results.json") -> None:
        """
        Save review results to a JSON file.
        
        Args:
            output_path: Path to save the results
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Results saved to {output_path}")
    
    def get_summary(self) -> str:
        """Get a summary of the review results."""
        if self.results.get("error"):
            return f"Review failed: {self.results['error']}"
        
        summary = f"""
Code Review Summary
===================
Repository: {self.results.get('repo_info', {}).get('name', 'N/A')}
Files Analyzed: {self.results['files_analyzed']}
Code Nodes Extracted: {self.results['nodes_extracted']}
Total Comments: {self.results['comments_generated']}
  - High Confidence (≥{int(self.confidence_threshold * 100)}%): {self.results['high_confidence_comments']}
  - Low Confidence (<{int(self.confidence_threshold * 100)}%): {self.results['low_confidence_comments']}
Duration: {self.results['start_time']} to {self.results['end_time']}
"""
        return summary
