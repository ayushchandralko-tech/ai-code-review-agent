"""AST parser for Python code analysis."""

import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class CodeNode:
    """Represents a code node extracted from AST."""
    node_type: str  # 'function', 'class', 'import'
    name: str
    line_start: int
    line_end: int
    source: str
    docstring: Optional[str] = None
    decorators: List[str] = None
    parent: Optional[str] = None
    
    def __post_init__(self):
        if self.decorators is None:
            self.decorators = []


class ASTParser:
    """Parse Python source files using AST."""
    
    SUPPORTED_EXTENSIONS = {'.py'}
    
    def __init__(self):
        """Initialize the AST parser."""
        pass
    
    def parse_file(self, file_path: Path) -> List[CodeNode]:
        """
        Parse a Python file and extract code nodes.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of CodeNode objects
        """
        if file_path.suffix not in self.SUPPORTED_EXTENSIONS:
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            nodes = []
            
            # Extract imports
            nodes.extend(self._extract_imports(tree, source))
            
            # Extract classes and functions
            nodes.extend(self._extract_classes_and_functions(tree, source))
            
            return nodes
            
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return []
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
    
    def _extract_imports(self, tree: ast.AST, source: str) -> List[CodeNode]:
        """Extract import statements from AST."""
        nodes = []
        lines = source.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                module_names = [alias.name for alias in node.names]
                import_source = lines[node.lineno - 1].strip()
                nodes.append(CodeNode(
                    node_type='import',
                    name=', '.join(module_names),
                    line_start=node.lineno,
                    line_end=node.lineno,
                    source=import_source
                ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                names = [alias.name for alias in node.names]
                import_source = lines[node.lineno - 1].strip()
                nodes.append(CodeNode(
                    node_type='import',
                    name=f'from {module} import {", ".join(names)}',
                    line_start=node.lineno,
                    line_end=node.lineno,
                    source=import_source
                ))
        
        return nodes
    
    def _extract_classes_and_functions(self, tree: ast.AST, source: str) -> List[CodeNode]:
        """Extract classes and functions from AST."""
        nodes = []
        lines = source.split('\n')
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_source = self._extract_node_source(node, lines)
                docstring = ast.get_docstring(node)
                decorators = [self._get_decorator_name(d) for d in node.decorator_list]
                
                nodes.append(CodeNode(
                    node_type='class',
                    name=node.name,
                    line_start=node.lineno,
                    line_end=node.end_lineno if node.end_lineno else node.lineno,
                    source=class_source,
                    docstring=docstring,
                    decorators=decorators
                ))
                
                # Extract methods within the class
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_source = self._extract_node_source(item, lines)
                        method_docstring = ast.get_docstring(item)
                        method_decorators = [self._get_decorator_name(d) for d in item.decorator_list]
                        
                        nodes.append(CodeNode(
                            node_type='function',
                            name=f"{node.name}.{item.name}",
                            line_start=item.lineno,
                            line_end=item.end_lineno if item.end_lineno else item.lineno,
                            source=method_source,
                            docstring=method_docstring,
                            decorators=method_decorators,
                            parent=node.name
                        ))
            
            elif isinstance(node, ast.FunctionDef):
                func_source = self._extract_node_source(node, lines)
                docstring = ast.get_docstring(node)
                decorators = [self._get_decorator_name(d) for d in node.decorator_list]
                
                nodes.append(CodeNode(
                    node_type='function',
                    name=node.name,
                    line_start=node.lineno,
                    line_end=node.end_lineno if node.end_lineno else node.lineno,
                    source=func_source,
                    docstring=docstring,
                    decorators=decorators
                ))
        
        return nodes
    
    def _extract_node_source(self, node: ast.AST, lines: List[str]) -> str:
        """Extract source code for a node."""
        start_line = node.lineno - 1
        end_line = node.end_lineno - 1 if node.end_lineno else start_line
        return '\n'.join(lines[start_line:end_line + 1])
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get the name of a decorator."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return str(decorator)
    
    def parse_directory(self, directory: Path) -> Dict[str, List[CodeNode]]:
        """
        Parse all Python files in a directory.
        
        Args:
            directory: Path to the directory
            
        Returns:
            Dictionary mapping file paths to lists of CodeNode objects
        """
        results = {}
        
        for file_path in directory.rglob("*.py"):
            # Skip __pycache__ and test files if desired
            if "__pycache__" in str(file_path):
                continue
            
            nodes = self.parse_file(file_path)
            if nodes:
                results[str(file_path)] = nodes
        
        return results
    
    def get_file_summary(self, nodes: List[CodeNode]) -> Dict[str, int]:
        """Get a summary of code nodes in a file."""
        summary = {
            'total_nodes': len(nodes),
            'functions': 0,
            'classes': 0,
            'imports': 0
        }
        
        for node in nodes:
            summary[node.node_type + 's'] = summary.get(node.node_type + 's', 0) + 1
        
        return summary
