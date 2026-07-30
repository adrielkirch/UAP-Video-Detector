"""
Unit tests for loose coupling import constraints.

Tests that UI/orchestration components don't directly import ultralytics,
ensuring proper abstraction and replaceable detector architecture.
"""

import pytest
import ast
import os
from pathlib import Path


class TestLooseCouplingImports:
    """Test import graph excludes ultralytics from UI components."""

    def test_ui_components_dont_import_ultralytics(self):
        """Should verify UI components don't directly import ultralytics."""
        # Get all Python files in src/ui/
        ui_dir = Path("src/ui")
        python_files = list(ui_dir.rglob("*.py"))

        ultralytics_imports = []

        for file_path in python_files:
            if file_path.name == "__init__.py" and file_path.stat().st_size == 0:
                continue  # Skip empty __init__.py files

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse AST to find imports
                tree = ast.parse(content, filename=str(file_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            if "ultralytics" in name.name:
                                ultralytics_imports.append((str(file_path), name.name))

                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "ultralytics" in node.module:
                            ultralytics_imports.append((str(file_path), node.module))

            except (SyntaxError, UnicodeDecodeError):
                # Skip files with syntax errors or encoding issues
                pass

        # Should find no ultralytics imports in UI
        if ultralytics_imports:
            import_list = "\n".join(
                [f"  {file}: {module}" for file, module in ultralytics_imports]
            )
            pytest.fail(f"Found ultralytics imports in UI components:\n{import_list}")

    def test_orchestration_components_dont_import_ultralytics(self):
        """Should verify orchestration components don't directly import ultralytics."""
        # Get all Python files in src/orchestration/
        orchestration_dir = Path("src/orchestration")

        if not orchestration_dir.exists():
            pytest.skip("Orchestration directory doesn't exist")

        python_files = list(orchestration_dir.rglob("*.py"))

        ultralytics_imports = []

        for file_path in python_files:
            if file_path.name == "__init__.py" and file_path.stat().st_size == 0:
                continue  # Skip empty __init__.py files

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse AST to find imports
                tree = ast.parse(content, filename=str(file_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            if "ultralytics" in name.name:
                                ultralytics_imports.append((str(file_path), name.name))

                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "ultralytics" in node.module:
                            ultralytics_imports.append((str(file_path), node.module))

            except (SyntaxError, UnicodeDecodeError):
                # Skip files with syntax errors or encoding issues
                pass

        # Should find no ultralytics imports in orchestration
        if ultralytics_imports:
            import_list = "\n".join(
                [f"  {file}: {module}" for file, module in ultralytics_imports]
            )
            pytest.fail(
                f"Found ultralytics imports in orchestration components:\n{import_list}"
            )

    def test_ingestion_components_dont_import_ultralytics(self):
        """Should verify ingestion components don't directly import ultralytics."""
        # Get all Python files in src/ingestion/
        ingestion_dir = Path("src/ingestion")
        python_files = list(ingestion_dir.rglob("*.py"))

        ultralytics_imports = []

        for file_path in python_files:
            if file_path.name == "__init__.py" and file_path.stat().st_size == 0:
                continue  # Skip empty __init__.py files

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse AST to find imports
                tree = ast.parse(content, filename=str(file_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            if "ultralytics" in name.name:
                                ultralytics_imports.append((str(file_path), name.name))

                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "ultralytics" in node.module:
                            ultralytics_imports.append((str(file_path), node.module))

            except (SyntaxError, UnicodeDecodeError):
                # Skip files with syntax errors or encoding issues
                pass

        # Should find no ultralytics imports in ingestion
        if ultralytics_imports:
            import_list = "\n".join(
                [f"  {file}: {module}" for file, module in ultralytics_imports]
            )
            pytest.fail(
                f"Found ultralytics imports in ingestion components:\n{import_list}"
            )

    def test_only_detector_module_imports_ultralytics(self):
        """Should verify only src/inference/detector.py imports ultralytics."""
        # Get all Python files in the project
        src_dir = Path("src")
        python_files = list(src_dir.rglob("*.py"))

        ultralytics_imports = []

        for file_path in python_files:
            if file_path.name == "__init__.py" and file_path.stat().st_size == 0:
                continue  # Skip empty __init__.py files

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse AST to find imports
                tree = ast.parse(content, filename=str(file_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            if "ultralytics" in name.name:
                                ultralytics_imports.append(str(file_path))

                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "ultralytics" in node.module:
                            ultralytics_imports.append(str(file_path))

            except (SyntaxError, UnicodeDecodeError):
                # Skip files with syntax errors or encoding issues
                pass

        # Remove duplicates
        ultralytics_imports = list(set(ultralytics_imports))

        # Should only import ultralytics in detector.py and factory.py
        allowed_files = [
            str(Path("src/inference/detector.py")),
            str(Path("src/inference/factory.py")),
        ]

        # Normalize paths for comparison
        normalized_imports = [os.path.normpath(path) for path in ultralytics_imports]
        normalized_allowed = [os.path.normpath(path) for path in allowed_files]

        unexpected_imports = [
            path for path in normalized_imports if path not in normalized_allowed
        ]

        if unexpected_imports:
            import_list = "\n".join([f"  {file}" for file in unexpected_imports])
            pytest.fail(
                f"Found ultralytics imports in unexpected files:\n{import_list}"
            )

    def test_factory_pattern_enforced(self):
        """Should verify that detector creation goes through factory pattern."""
        # Check that UltralyticsDetector is not directly instantiated outside factory
        src_dir = Path("src")
        python_files = list(src_dir.rglob("*.py"))

        direct_instantiations = []

        for file_path in python_files:
            # Skip the detector.py and factory.py files themselves
            if file_path.name in ["detector.py", "factory.py"]:
                continue

            if file_path.name == "__init__.py" and file_path.stat().st_size == 0:
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Look for direct UltralyticsDetector instantiation
                if "UltralyticsDetector(" in content:
                    direct_instantiations.append(str(file_path))

            except UnicodeDecodeError:
                # Skip files with encoding issues
                pass

        # Should find no direct instantiations outside factory
        if direct_instantiations:
            import_list = "\n".join([f"  {file}" for file in direct_instantiations])
            pytest.fail(
                f"Found direct UltralyticsDetector instantiation in:\n{import_list}"
            )

    def test_abstract_detector_protocol_used(self):
        """Should verify components use AerialDetector protocol, not concrete classes."""
        # Check type hints in orchestration and UI files
        component_dirs = [Path("src/ui"), Path("src/orchestration")]

        concrete_type_usage = []

        for component_dir in component_dirs:
            if not component_dir.exists():
                continue

            python_files = list(component_dir.rglob("*.py"))

            for file_path in python_files:
                if file_path.name == "__init__.py" and file_path.stat().st_size == 0:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Look for concrete detector class usage in type hints
                    if "UltralyticsDetector" in content or "NullDetector" in content:
                        # Parse to check if it's in type annotations
                        tree = ast.parse(content, filename=str(file_path))

                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                # Check function arguments and return annotations
                                if node.args.args:
                                    for arg in node.args.args:
                                        if arg.annotation and ast.unparse(
                                            arg.annotation
                                        ) in ["UltralyticsDetector", "NullDetector"]:
                                            concrete_type_usage.append(
                                                (str(file_path), f"argument {arg.arg}")
                                            )

                                if node.returns and ast.unparse(node.returns) in [
                                    "UltralyticsDetector",
                                    "NullDetector",
                                ]:
                                    concrete_type_usage.append(
                                        (str(file_path), "return type")
                                    )

                except (SyntaxError, UnicodeDecodeError, AttributeError):
                    # Skip files with parsing issues
                    pass

        # Should find no concrete detector type usage in components
        if concrete_type_usage:
            usage_list = "\n".join(
                [f"  {file}: {usage}" for file, usage in concrete_type_usage]
            )
            pytest.fail(
                f"Found concrete detector type usage in components:\n{usage_list}"
            )
