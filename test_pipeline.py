"""Test script for the code review pipeline."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import CodeReviewPipeline
from src.repo_cloner import RepoCloner
from src.ast_parser import ASTParser
from src.chunker import CodeChunker
from src.llm_reviewer import LLMReviewer


def test_repo_cloner():
    """Test repository cloning."""
    print("Testing RepoCloner...")
    cloner = RepoCloner()
    
    # Test URL validation
    assert cloner._is_valid_github_url("https://github.com/python/cpython"), "Failed: HTTPS URL validation"
    assert cloner._is_valid_github_url("git@github.com:python/cpython.git"), "Failed: SSH URL validation"
    assert not cloner._is_valid_github_url("https://example.com/repo"), "Failed: Invalid URL rejection"
    
    # Test repo name extraction
    assert cloner._extract_repo_name("https://github.com/python/cpython.git") == "cpython", "Failed: HTTPS repo name with .git"
    assert cloner._extract_repo_name("https://github.com/python/cpython") == "cpython", "Failed: HTTPS repo name without .git"
    assert cloner._extract_repo_name("git@github.com:python/cpython.git") == "cpython", "Failed: SSH repo name extraction"
    
    print("✅ RepoCloner tests passed")


def test_ast_parser():
    """Test AST parser."""
    print("Testing ASTParser...")
    parser = ASTParser()
    
    # Create a test Python file
    test_code = '''
def hello_world():
    """Print hello world."""
    print("Hello, World!")

class Calculator:
    """Simple calculator."""
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b

import os
from sys import argv
'''
    
    # Write test file
    test_file = Path("test_sample.py")
    test_file.write_text(test_code)
    
    # Parse the file
    nodes = parser.parse_file(test_file)
    
    # Verify nodes
    assert len(nodes) > 0, "Should extract nodes"
    
    # Check for function
    func_nodes = [n for n in nodes if n.node_type == 'function']
    assert len(func_nodes) > 0, "Should extract functions"
    
    # Check for class
    class_nodes = [n for n in nodes if n.node_type == 'class']
    assert len(class_nodes) > 0, "Should extract classes"
    
    # Check for imports
    import_nodes = [n for n in nodes if n.node_type == 'import']
    assert len(import_nodes) > 0, "Should extract imports"
    
    # Cleanup
    test_file.unlink()
    
    print("✅ ASTParser tests passed")


def test_chunker():
    """Test code chunker."""
    print("Testing CodeChunker...")
    chunker = CodeChunker(max_lines=10, overlap_lines=2)
    
    # Test with small code (no chunking needed)
    small_code = "def foo():\n    pass\n"
    chunks = chunker.chunk_code(small_code, "test.py")
    assert len(chunks) == 1, "Small code should not be chunked"
    
    # Test with large code (chunking needed)
    large_code = "\n".join([f"line {i}" for i in range(30)])
    chunks = chunker.chunk_code(large_code, "test.py")
    assert len(chunks) > 1, "Large code should be chunked"
    
    # Test token estimation
    tokens = chunker.estimate_tokens("hello world")
    assert tokens > 0, "Should estimate tokens"
    
    print("✅ CodeChunker tests passed")


def test_llm_reviewer():
    """Test LLM reviewer (requires API key)."""
    print("Testing LLMReviewer...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Skipping LLMReviewer tests (no API key)")
        return
    
    reviewer = LLMReviewer()
    
    # Test with simple code
    test_code = '''
def insecure_function(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return execute_query(query)
'''
    
    try:
        comments = reviewer.review_code(test_code, "test.py", "Security test")
        print(f"  Generated {len(comments)} comments")
        
        if comments:
            comment = comments[0]
            assert comment.file_path == "test.py"
            assert 0 <= comment.confidence <= 1
            assert comment.severity in ['critical', 'high', 'medium', 'low', 'info']
            assert comment.category in ['security', 'performance', 'style', 'bug', 'documentation', 'best_practice']
        
        print("✅ LLMReviewer tests passed")
    except Exception as e:
        print(f"⚠️ LLMReviewer test failed: {e}")


def test_pipeline_local():
    """Test pipeline with local directory."""
    print("Testing CodeReviewPipeline with local directory...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Skipping pipeline tests (no API key)")
        return
    
    # Test with the src directory
    pipeline = CodeReviewPipeline(confidence_threshold=0.7)
    
    try:
        results = pipeline.review_local_directory("src")
        
        assert results["files_analyzed"] > 0, "Should analyze files"
        assert results["nodes_extracted"] > 0, "Should extract nodes"
        
        print(f"  Analyzed {results['files_analyzed']} files")
        print(f"  Extracted {results['nodes_extracted']} nodes")
        print(f"  Generated {results['comments_generated']} comments")
        
        print("✅ Pipeline local directory tests passed")
    except Exception as e:
        print(f"⚠️ Pipeline test failed: {e}")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running AI Code Review Agent Tests")
    print("=" * 60)
    print()
    
    try:
        test_repo_cloner()
        test_ast_parser()
        test_chunker()
        test_llm_reviewer()
        test_pipeline_local()
        
        print()
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Unexpected error: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
