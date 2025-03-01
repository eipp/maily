#!/usr/bin/env python3
"""
Standardize Python requirements files across the Maily project.

This script:
1. Creates a base requirements.txt with common dependencies
2. Creates specialized requirements files for different components
3. Ensures consistent versioning across all files
4. Organizes dependencies by category
5. Adds comments for better readability
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# Define the project root and backup directory
PROJECT_ROOT = Path(__file__).parent.parent
BACKUP_DIR = PROJECT_ROOT / f"requirements_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Define the requirements structure
REQUIREMENTS = {
    "base": {
        "path": PROJECT_ROOT / "requirements.txt",
        "categories": {
            "Core Backend Framework": [
                "fastapi==0.95.1",
                "uvicorn==0.22.0",
                "pydantic==1.10.7",
                "python-dotenv==1.0.0",
                "python-multipart==0.0.6",
                "email-validator==2.0.0.post2",
            ],
            "Database": [
                "sqlalchemy==2.0.12",
                "alembic==1.10.4",
                "psycopg2-binary==2.9.6",
                "asyncpg==0.28.0",
            ],
            "Authentication": [
                "python-jose[cryptography]==3.3.0",
                "passlib[bcrypt]==1.7.4",
                "bcrypt==4.0.1",
            ],
            "Caching & Messaging": [
                "redis==4.5.5",
                "aioredis==2.0.1",
                "pika==1.3.2",
            ],
            "HTTP & API": [
                "requests==2.30.0",
                "aiohttp==3.8.5",
            ],
            "Testing": [
                "pytest==7.3.1",
                "pytest-asyncio==0.21.0",
                "httpx==0.24.0",
                "pytest-cov==4.1.0",
                "pytest-mock==3.12.0",
                "factory-boy==3.3.0",
            ],
            "Monitoring": [
                "prometheus-client==0.20.0",
                "prometheus-fastapi-instrumentator==7.0.0",
                "opentelemetry-api==1.23.0",
                "opentelemetry-sdk==1.23.0",
            ],
            "Utilities": [
                "loguru==0.7.0",
                "tenacity==8.2.2",
                "python-dateutil==2.8.2",
            ],
            "Code Quality": [
                "black==23.3.0",
                "flake8==6.0.0",
                "isort==5.12.0",
                "mypy==1.3.0",
                "pre-commit==3.6.0",
            ],
        }
    },
    "api": {
        "path": PROJECT_ROOT / "apps/api/requirements.txt",
        "categories": {
            "API Dependencies": [
                "-r ../../requirements.txt",
                "",
            ],
            "API-specific AI Dependencies": [
                "pyautogen==0.7.5",
                "google-generativeai==0.3.2",
                "replicate==0.22.0",
                "together==0.2.8",
                "huggingface-hub==0.21.3",
                "fireworks-ai==0.12.0",
                "ray==2.9.3",
            ],
            "AI Optimization": [
                "onnxruntime-gpu==1.17.0  # For NVIDIA GPU support",
            ],
            "OpenTelemetry Specific": [
                "opentelemetry-instrumentation-fastapi==0.44b0",
                "opentelemetry-exporter-prometheus==1.23.0",
            ],
            "Content Processing": [
                "python-docx==0.8.11",
                "python-pptx==0.6.21",
                "openpyxl==3.1.0",
                "reportlab==4.0.0",
                "aiofiles==23.1.0",
            ],
            "Email Providers": [
                "resend==0.5.0",
                "sendgrid==6.10.0",
            ],
            "OctoTools Integration": [
                "octotools==1.0.0",
            ],
        }
    },
    "ai-ml": {
        "path": PROJECT_ROOT / "apps/api/requirements-ai-ml.txt",
        "categories": {
            "AI & ML Enhancement Components": [
                "# Include base API requirements",
                "-r requirements.txt",
                "",
            ],
            "Model Versioning & Tracking": [
                "wandb==0.16.0",
                "dvc==3.30.1",
                "dvc-s3==2.23.0",
            ],
            "ML Observability": [
                "arize==7.0.0",
            ],
            "LLM Providers": [
                "anthropic==0.8.0",
                "openai==1.3.0",
                "google-generativeai==0.3.0",
                "litellm==1.10.0",
            ],
            "Image Generation": [
                "pillow==10.0.0",
            ],
            "Async Support": [
                "asyncio==3.4.3",
            ],
        }
    },
    "workers": {
        "path": PROJECT_ROOT / "apps/workers/requirements.txt",
        "categories": {
            "Worker Dependencies": [
                "# Include base requirements",
                "-r ../../requirements.txt",
                "",
            ],
            "Queue Processing": [
                "celery==5.3.1",
                "flower==2.0.1",
                "redis==4.5.5",
            ],
            "Email Processing": [
                "beautifulsoup4==4.12.2",
                "lxml==4.9.3",
                "premailer==3.10.0",
            ],
            "Data Processing": [
                "pandas==2.0.3",
                "numpy==1.24.3",
                "polars==0.19.3",
            ],
            "Storage": [
                "boto3==1.28.38",
                "minio==7.1.15",
            ],
        }
    },
    "dev": {
        "path": PROJECT_ROOT / "requirements-dev.txt",
        "categories": {
            "Development Dependencies": [
                "# Include base requirements",
                "-r requirements.txt",
                "",
            ],
            "Testing": [
                "pytest-xdist==3.3.1",
                "pytest-sugar==0.9.7",
                "pytest-cov==4.1.0",
                "pytest-mock==3.12.0",
                "pytest-timeout==2.1.0",
            ],
            "Linting & Formatting": [
                "black==23.3.0",
                "flake8==6.0.0",
                "isort==5.12.0",
                "mypy==1.3.0",
                "pylint==2.17.4",
            ],
            "Documentation": [
                "sphinx==7.1.2",
                "sphinx-rtd-theme==1.3.0",
                "mkdocs==1.5.3",
                "mkdocs-material==9.4.6",
            ],
            "Development Tools": [
                "ipython==8.14.0",
                "jupyter==1.0.0",
                "pip-tools==7.3.0",
                "pre-commit==3.6.0",
            ],
        }
    },
}

def create_backup():
    """Create a backup of existing requirements files."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    for req_type, config in REQUIREMENTS.items():
        if config["path"].exists():
            backup_path = BACKUP_DIR / config["path"].name
            shutil.copy2(config["path"], backup_path)
            print(f"Backed up {config['path']} to {backup_path}")

def write_requirements_file(req_type, config):
    """Write a requirements file with organized categories."""
    path = config["path"]

    # Create parent directory if it doesn't exist
    os.makedirs(path.parent, exist_ok=True)

    with open(path, "w") as f:
        f.write(f"# Maily {req_type.upper()} Requirements\n")
        f.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for category, packages in config["categories"].items():
            f.write(f"# {category}\n")
            for package in packages:
                f.write(f"{package}\n")
            f.write("\n")

        print(f"Created {path}")

def create_requirements_md():
    """Create a README.md file explaining the requirements structure."""
    readme_path = PROJECT_ROOT / "REQUIREMENTS.md"

    with open(readme_path, "w") as f:
        f.write("# Maily Python Requirements\n\n")
        f.write("This document outlines the Python requirements structure for the Maily project.\n\n")

        f.write("## Requirements Files\n\n")
        f.write("The project uses multiple requirements files to organize dependencies:\n\n")

        f.write("| File | Purpose |\n")
        f.write("|------|--------|\n")
        f.write("| `requirements.txt` | Base dependencies used across the project |\n")
        f.write("| `requirements-dev.txt` | Development-only dependencies |\n")
        f.write("| `apps/api/requirements.txt` | API-specific dependencies |\n")
        f.write("| `apps/api/requirements-ai-ml.txt` | AI and ML specific dependencies |\n")
        f.write("| `apps/workers/requirements.txt` | Worker-specific dependencies |\n\n")

        f.write("## Installation\n\n")
        f.write("### For Development\n\n")
        f.write("```bash\n")
        f.write("pip install -r requirements-dev.txt\n")
        f.write("```\n\n")

        f.write("### For API Service\n\n")
        f.write("```bash\n")
        f.write("pip install -r apps/api/requirements.txt\n")
        f.write("```\n\n")

        f.write("### For AI/ML Features\n\n")
        f.write("```bash\n")
        f.write("pip install -r apps/api/requirements-ai-ml.txt\n")
        f.write("```\n\n")

        f.write("### For Workers\n\n")
        f.write("```bash\n")
        f.write("pip install -r apps/workers/requirements.txt\n")
        f.write("```\n\n")

        f.write("## Dependency Management\n\n")
        f.write("We use pinned versions for all dependencies to ensure reproducibility. ")
        f.write("When adding new dependencies, please follow these guidelines:\n\n")

        f.write("1. Add the dependency to the appropriate requirements file\n")
        f.write("2. Use pinned versions (e.g., `package==1.2.3`)\n")
        f.write("3. Organize the dependency under the appropriate category\n")
        f.write("4. Run tests to ensure compatibility\n")

        print(f"Created {readme_path}")

def main():
    """Main function to standardize requirements files."""
    print("Standardizing Python requirements files...")

    # Create backup of existing files
    create_backup()

    # Create each requirements file
    for req_type, config in REQUIREMENTS.items():
        write_requirements_file(req_type, config)

    # Create README.md for requirements
    create_requirements_md()

    print("\nRequirements standardization complete!")
    print(f"Backup created at: {BACKUP_DIR}")
    print("Please review the generated files and make any necessary adjustments.")

if __name__ == "__main__":
    main()
