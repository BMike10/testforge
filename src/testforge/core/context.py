import ast
import networkx as nx
import git
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel

class FunctionInfo(BaseModel):
    name: str
    args: List[str]
    docstring: Optional[str]
    line_start: int
    line_end: int
    body: str
    complexity: int = 1

class ClassInfo(BaseModel):
    name: str
    methods: List[FunctionInfo]
    docstring: Optional[str]
    complexity: int = 1

class ModuleInfo(BaseModel):
    file_path: str
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    imports: List[str]
    internal_dependencies: Set[str] = set()
    total_complexity: int = 0
    is_testable: bool = True

class ContextManager:
    """
    Deterministic tool to analyze Python codebase using AST and NetworkX.
    Provides context, complexity analysis, and dependency ordering.
    """

    @staticmethod
    def get_affected_modules(project_root: Path, base_branch: str = "main") -> List[str]:
        """
        Uses Git to identify changed Python files compared to a base branch,
        then uses the dependency graph to find all downstream dependent modules.
        """
        try:
            repo = git.Repo(project_root)
            diffs = repo.commit(base_branch).diff(None) # None means working tree + index
            
            changed_files = set()
            for diff in diffs:
                if diff.a_path and diff.a_path.endswith('.py'):
                    changed_files.add(diff.a_path)
                if diff.b_path and diff.b_path.endswith('.py'):
                    changed_files.add(diff.b_path)
                    
            # Also check untracked files
            for untracked in repo.untracked_files:
                if untracked.endswith('.py'):
                    changed_files.add(untracked)
                    
            if not changed_files:
                return []
                
            graph = ContextManager.build_dependency_graph(project_root)
            
            # Find all nodes in the DAG that are reachable from the changed files
            # Meaning, if A is changed and B depends on A, we need to test B as well.
            # In our graph, edges are dependency -> dependent, or dependent -> dependency?
            # Looking at build_dependency_graph: graph.add_edge(node, rel_path) where node is the dependency and rel_path depends on it.
            # Wait, `for node in graph.nodes: if node.endswith(dep_path): graph.add_edge(node, rel_path)`
            # So edge goes from `dependency` to `dependent`.
            # We want all nodes reachable from changed_files.
            
            affected = set()
            for changed in changed_files:
                if changed in graph:
                    affected.add(changed)
                    affected.update(nx.descendants(graph, changed))
                    
            # Return them in topological order
            full_order = ContextManager.get_topological_sort(graph)
            return [node for node in full_order if node in affected]
            
        except git.InvalidGitRepositoryError:
            return []
        except git.GitCommandError:
            return []

    @staticmethod
    def calculate_complexity(node: ast.AST) -> int:
        """
        Simple McCabe cyclomatic complexity calculation.
        """
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.And, ast.Or, ast.ExceptHandler, ast.With, ast.IfExp)):
                complexity += 1
        return complexity

    @staticmethod
    def analyze_file(file_path: Path, project_root: Path) -> ModuleInfo:
        with open(file_path, "r") as f:
            content = f.read()
        
        tree = ast.parse(content)
        module_info = ModuleInfo(
            file_path=str(file_path.relative_to(project_root)),
            classes=[],
            functions=[],
            imports=[],
            internal_dependencies=set()
        )

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_info.imports.append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module_info.imports.append(f"{node.module}.{node.names[0].name}" if node.module else node.names[0].name)
                if node.module and (node.module.startswith("testforge") or node.level > 0):
                   module_info.internal_dependencies.add(node.module)

            elif isinstance(node, ast.ClassDef):
                methods = []
                class_complexity = 1
                for subnode in node.body:
                    if isinstance(subnode, ast.FunctionDef):
                        func_info = ContextManager._extract_function_info(subnode, content)
                        methods.append(func_info)
                        class_complexity += func_info.complexity
                
                module_info.classes.append(ClassInfo(
                    name=node.name,
                    methods=methods,
                    docstring=ast.get_docstring(node),
                    complexity=class_complexity
                ))
                module_info.total_complexity += class_complexity
            
            elif isinstance(node, ast.FunctionDef):
                func_info = ContextManager._extract_function_info(node, content)
                module_info.functions.append(func_info)
                module_info.total_complexity += func_info.complexity
        
        # Heuristic 1 & 2: If there are no functions and no classes, it's not testable
        if not module_info.classes and not module_info.functions:
            module_info.is_testable = False
        
        return module_info

    @staticmethod
    def _extract_function_info(node: ast.FunctionDef, source_content: str) -> FunctionInfo:
        lines = source_content.splitlines()
        body_lines = lines[node.lineno - 1 : node.end_lineno]
        
        return FunctionInfo(
            name=node.name,
            args=[arg.arg for arg in node.args.args],
            docstring=ast.get_docstring(node),
            line_start=node.lineno,
            line_end=node.end_lineno,
            body="\n".join(body_lines),
            complexity=ContextManager.calculate_complexity(node)
        )

    @staticmethod
    def build_dependency_graph(root_dir: Path) -> nx.DiGraph:
        """
        Builds a Directed Acyclic Graph (DAG) of the codebase dependencies.
        """
        graph = nx.DiGraph()
        arch_map = ContextManager.build_architecture_map(root_dir)
        
        for rel_path, info in arch_map.items():
            graph.add_node(rel_path, info=info)
            
        for rel_path, info in arch_map.items():
            for dep in info.internal_dependencies:
                # Resolve module name to relative path (simplified)
                # e.g., testforge.core.context -> src/testforge/core/context.py
                dep_path = dep.replace(".", "/") + ".py"
                # Search for the best match in the graph
                for node in graph.nodes:
                    if node.endswith(dep_path):
                        graph.add_edge(node, rel_path)
                        break
        
        return graph

    @staticmethod
    def get_topological_sort(graph: nx.DiGraph) -> List[str]:
        """
        Returns modules in bottom-up order (leaf nodes first).
        """
        try:
            return list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            # Handle circular dependencies if they exist
            return list(graph.nodes)

    @staticmethod
    def build_architecture_map(root_dir: Path) -> Dict[str, ModuleInfo]:
        """
        Builds a structure map for the given path (file or directory).
        """
        arch_map = {}
        
        if root_dir.is_file():
            if root_dir.suffix == ".py":
                try:
                    # For a single file, the relative path is just its name
                    # or we can use the absolute path relative to CWD
                    project_root = root_dir.parent
                    arch_map[str(root_dir.name)] = ContextManager.analyze_file(root_dir, project_root)
                except Exception:
                    pass
            return arch_map

        # It's a directory
        # Prioritize 'src' if it exists
        search_path = root_dir / "src" if (root_dir / "src").exists() else root_dir
        
        for py_file in search_path.rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file) or "tests" in str(py_file):
                continue
            try:
                arch_map[str(py_file.relative_to(root_dir))] = ContextManager.analyze_file(py_file, root_dir)
            except Exception:
                pass
        return arch_map
