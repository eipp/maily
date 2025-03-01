# Maily Database Package

This package contains the database models and migrations for the Maily platform.

## Database Strategy Decision

After evaluating both SQLAlchemy and Prisma, we have decided to standardize on **SQLAlchemy** as our primary database strategy for the following reasons:

1. **More Complete Implementation**: The SQLAlchemy models are more fully developed with comprehensive relationships and business logic.
2. **Python-Native**: As our backend is primarily Python-based, SQLAlchemy provides a more natural integration.
3. **Flexibility**: SQLAlchemy offers more flexibility for complex queries and database operations.
4. **Existing Migration Path**: We already have SQL migrations in place for SQLAlchemy models.

## Structure

- `src/models.py`: Contains all SQLAlchemy models
- `migrations/`: Contains SQL migration files
- `src/migrations.py`: Migration utilities

## Usage

Import models from the package:

```python
from packages.database.src.models import User, Campaign, EmailTemplate
```

## Migrations

To run migrations:

```bash
# From the root directory
python -m packages.database.src.migrations run
```

To create a new migration:

```bash
# From the root directory
python -m packages.database.src.migrations create "description_of_changes"
```
