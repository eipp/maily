# Maily Python Requirements

This document outlines the Python requirements structure for the Maily project.

## Requirements Files

The project uses multiple requirements files to organize dependencies:

| File | Purpose |
|------|--------|
| `requirements.txt` | Base dependencies used across the project |
| `requirements-dev.txt` | Development-only dependencies |
| `apps/api/requirements.txt` | API-specific dependencies |
| `apps/api/requirements-ai-ml.txt` | AI and ML specific dependencies |
| `apps/workers/requirements.txt` | Worker-specific dependencies |

## Installation

### For Development

```bash
pip install -r requirements-dev.txt
```

### For API Service

```bash
pip install -r apps/api/requirements.txt
```

### For AI/ML Features

```bash
pip install -r apps/api/requirements-ai-ml.txt
```

### For Workers

```bash
pip install -r apps/workers/requirements.txt
```

## Dependency Management

We use pinned versions for all dependencies to ensure reproducibility. When adding new dependencies, please follow these guidelines:

1. Add the dependency to the appropriate requirements file
2. Use pinned versions (e.g., `package==1.2.3`)
3. Organize the dependency under the appropriate category
4. Run tests to ensure compatibility
