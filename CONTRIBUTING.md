# Contributing to wagtail-reusable-blocks

Thank you for your interest in contributing!

## Development Setup

### Prerequisites

- Python 3.10+
- uv (recommended) or pip

### Clone and Setup

```bash
git clone https://github.com/kkm-horikawa/wagtail-reusable-blocks.git
cd wagtail-reusable-blocks

# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Style

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy src/
```

## Project Structure

```
wagtail-reusable-blocks/
├── src/
│   └── wagtail_reusable_blocks/
│       ├── __init__.py
│       ├── models.py          # ReusableBlock model
│       ├── blocks.py          # StreamField blocks
│       ├── wagtail_hooks.py   # Admin integration
│       └── templates/
├── tests/
├── docs/
│   ├── ARCHITECTURE.md        # Design decisions
│   └── GLOSSARY.md            # Terminology
├── pyproject.toml
├── README.md
└── CONTRIBUTING.md
```

## Development Workflow

### 1. Check Existing Issues

Before starting work, check the [Issue Tracker](https://github.com/kkm-horikawa/wagtail-reusable-blocks/issues) and [Project Board](https://github.com/users/kkm-horikawa/projects/6).

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-fix-name
```

### 3. Make Changes

- Write tests for new functionality
- Follow existing code style
- Update documentation if needed

### 4. Test Your Changes

```bash
pytest
ruff check .
ruff format --check .
```

### 5. Commit

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add ReusableBlockChooserBlock"
git commit -m "fix: resolve circular reference detection"
git commit -m "docs: update installation guide"
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Milestones and Roadmap

| Milestone | Focus |
|-----------|-------|
| [v0.1.0](https://github.com/kkm-horikawa/wagtail-reusable-blocks/milestone/1) | MVP - Basic reusable blocks |
| [v0.2.0](https://github.com/kkm-horikawa/wagtail-reusable-blocks/milestone/2) | Slot-based templating |
| [v0.3.0](https://github.com/kkm-horikawa/wagtail-reusable-blocks/milestone/3) | Performance & production ready |

## Key Documents

- [README.md](README.md) - Project overview and quick start
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Design decisions and why
- [docs/GLOSSARY.md](docs/GLOSSARY.md) - Terminology definitions

## Questions?

Open an [Issue](https://github.com/kkm-horikawa/wagtail-reusable-blocks/issues) for questions or discussions.
