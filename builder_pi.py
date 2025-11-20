#!/usr/bin/env python3
"""
Builder PI - CLI tool for scaffolding new AI engines and components

This tool helps developers quickly scaffold new engines, modules,
and components for the AshborneSDK.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EngineBuilder:
    """Builds new engine scaffolds for the SDK."""

    def __init__(self, base_path: str = "."):
        """
        Initialize the EngineBuilder.

        Args:
            base_path: Base directory for creating files
        """
        self.base_path = Path(base_path)
        self.sdk_path = self.base_path / "sdk"

    def create_engine(self, name: str, description: str = "") -> bool:
        """
        Create a new engine module.

        Args:
            name: Name of the engine
            description: Description of the engine

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Creating new engine: {name}")

        # Sanitize name
        module_name = name.lower().replace(" ", "_").replace("-", "_")
        file_name = f"{module_name}.py"
        file_path = self.sdk_path / file_name

        if file_path.exists():
            logger.error(f"Engine already exists: {file_path}")
            return False

        # Create engine template
        template = self._generate_engine_template(module_name, description)

        try:
            with open(file_path, "w") as f:
                f.write(template)
            logger.info(f"Engine created successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating engine: {str(e)}")
            return False

    def _generate_engine_template(self, name: str, description: str) -> str:
        """
        Generate engine template code.

        Args:
            name: Module name
            description: Module description

        Returns:
            Template string
        """
        class_name = "".join(word.capitalize() for word in name.split("_"))

        template = f'''"""
{class_name} Module

{description or f"Custom engine module: {class_name}"}
"""

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class {class_name}:
    """
    {class_name} implementation.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the {class_name}.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {{}}
        logger.info(f"{class_name} initialized")

    def process(self, data: Any) -> Dict[str, Any]:
        """
        Process data using this engine.

        Args:
            data: Input data to process

        Returns:
            Processing result dictionary
        """
        logger.info("Processing data...")

        # TODO: Implement your processing logic here

        return {{
            "status": "success",
            "data": data,
            "engine": "{name}"
        }}

    def validate(self, data: Any) -> bool:
        """
        Validate input data.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        # TODO: Implement validation logic
        return True

    def configure(self, config: Dict) -> None:
        """
        Update engine configuration.

        Args:
            config: New configuration parameters
        """
        self.config.update(config)
        logger.info("Configuration updated")
'''
        return template

    def create_test_file(self, engine_name: str) -> bool:
        """
        Create a test file for an engine.

        Args:
            engine_name: Name of the engine

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Creating test file for engine: {engine_name}")

        module_name = engine_name.lower().replace(" ", "_").replace("-", "_")
        test_dir = self.base_path / "tests"
        test_dir.mkdir(exist_ok=True)

        test_file_path = test_dir / f"test_{module_name}.py"

        if test_file_path.exists():
            logger.warning(f"Test file already exists: {test_file_path}")
            return False

        class_name = "".join(word.capitalize() for word in module_name.split("_"))

        template = f'''"""
Tests for {class_name} module
"""

import pytest
from sdk.{module_name} import {class_name}


def test_{module_name}_initialization():
    """Test {class_name} initialization."""
    engine = {class_name}()
    assert engine is not None
    assert engine.config == {{}}


def test_{module_name}_with_config():
    """Test {class_name} with configuration."""
    config = {{"test_param": "value"}}
    engine = {class_name}(config)
    assert engine.config == config


def test_{module_name}_process():
    """Test {class_name} process method."""
    engine = {class_name}()
    result = engine.process("test data")
    assert result["status"] == "success"
    assert result["engine"] == "{module_name}"


def test_{module_name}_validate():
    """Test {class_name} validate method."""
    engine = {class_name}()
    assert engine.validate("test data") is True


def test_{module_name}_configure():
    """Test {class_name} configure method."""
    engine = {class_name}()
    new_config = {{"new_param": "new_value"}}
    engine.configure(new_config)
    assert "new_param" in engine.config
'''

        try:
            with open(test_file_path, "w") as f:
                f.write(template)
            logger.info(f"Test file created successfully: {test_file_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating test file: {str(e)}")
            return False


def create_engine_command(args):
    """Handle create-engine command."""
    builder = EngineBuilder(args.path)

    if not builder.sdk_path.exists():
        logger.error(f"SDK directory not found: {builder.sdk_path}")
        logger.info("Run this command from the project root directory")
        return 1

    success = builder.create_engine(args.name, args.description)

    if success and args.with_tests:
        builder.create_test_file(args.name)

    return 0 if success else 1


def list_engines_command(args):
    """Handle list-engines command."""
    sdk_path = Path(args.path) / "sdk"

    if not sdk_path.exists():
        logger.error(f"SDK directory not found: {sdk_path}")
        return 1

    engines = [
        f.stem for f in sdk_path.glob("*.py")
        if f.stem not in ["__init__", "__pycache__"]
    ]

    print("\nAvailable Engines:")
    print("-" * 40)
    for engine in sorted(engines):
        print(f"  - {engine}")
    print()

    return 0


def init_project_command(args):
    """Handle init-project command."""
    project_path = Path(args.path)

    logger.info(f"Initializing new AshborneSDK project at: {project_path}")

    # Create directory structure
    directories = [
        project_path / "sdk",
        project_path / "tests",
        project_path / "docs",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

    # Create basic files
    files = {
        project_path / "README.md": "# AshborneSDK Project\n\nYour AI Governance SDK project.\n",
        project_path / "sdk" / "__init__.py": '"""SDK Package"""\n',
        project_path / ".gitignore": "*.pyc\n__pycache__/\n.env\n",
    }

    for file_path, content in files.items():
        if not file_path.exists():
            with open(file_path, "w") as f:
                f.write(content)
            logger.info(f"Created file: {file_path}")

    logger.info("Project initialized successfully!")
    return 0


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Builder PI - AshborneSDK scaffolding tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new engine
  python builder_pi.py create-engine MyEngine --description "My custom engine"

  # Create an engine with tests
  python builder_pi.py create-engine MyEngine --with-tests

  # List available engines
  python builder_pi.py list-engines

  # Initialize a new project
  python builder_pi.py init-project --path ./my_project
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create engine command
    create_parser = subparsers.add_parser(
        "create-engine",
        help="Create a new engine module"
    )
    create_parser.add_argument("name", help="Name of the engine")
    create_parser.add_argument(
        "--description",
        default="",
        help="Description of the engine"
    )
    create_parser.add_argument(
        "--with-tests",
        action="store_true",
        help="Create test file for the engine"
    )
    create_parser.add_argument(
        "--path",
        default=".",
        help="Base path for the project (default: current directory)"
    )

    # List engines command
    list_parser = subparsers.add_parser(
        "list-engines",
        help="List available engines"
    )
    list_parser.add_argument(
        "--path",
        default=".",
        help="Base path for the project (default: current directory)"
    )

    # Init project command
    init_parser = subparsers.add_parser(
        "init-project",
        help="Initialize a new AshborneSDK project"
    )
    init_parser.add_argument(
        "--path",
        default="./ashborne_project",
        help="Path for the new project"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == "create-engine":
        return create_engine_command(args)
    elif args.command == "list-engines":
        return list_engines_command(args)
    elif args.command == "init-project":
        return init_project_command(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
