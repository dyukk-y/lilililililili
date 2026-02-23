# Contributing to AutoPost Bot

Thank you for your interest in contributing! This document provides guidelines and instructions.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [How to Contribute](#how-to-contribute)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)
8. [Reporting Issues](#reporting-issues)

## Code of Conduct

- Be respectful to all contributors
- Include people of all backgrounds and experience levels
- Focus on constructive feedback
- Report violations to maintainers

## Getting Started

### Fork the Repository

1. Go to [https://github.com/dyukk-y/lilililililili](https://github.com/dyukk-y/lililililitili)
2. Click "Fork" in top right
3. Clone your fork: `git clone https://github.com/YOUR_USERNAME/lililililitili.git`
4. Add upstream: `git remote add upstream https://github.com/dyukk-y/lilililililili.git`

### Create a Branch

```bash
# Update from upstream
git fetch upstream
git checkout upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or for fixes
git checkout -b fix/your-fix-name
```

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code improvements
- `test/description` - Test additions

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/dyukk-y/lililililitili.git
cd lililililitili
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-cov flake8 black mypy
```

### 4. Verify Setup

```bash
python -c "from bot import AutoPostBot; print('OK')"
pytest tests/ -v
```

## How to Contribute

### Adding Features

1. **Check existing issues** - Avoid duplicates
2. **Create an issue** - Describe your feature
3. **Get approval** - Wait for maintainer feedback
4. **Implement** - Follow coding standards
5. **Test thoroughly** - Add tests for your feature
6. **Submit PR** - Follow PR guidelines

### Fixing Bugs

1. **Report the issue** - If not reported yet
2. **Create a test** - That reproduces the bug
3. **Fix the bug** - Make the test pass
4. **Verify** - Run all tests
5. **Submit PR** - Reference the issue

### Improving Documentation

1. Edit relevant `.md` files
2. Run spell check (optional)
3. Preview changes
4. Submit PR with improvements

### Adding Tests

```bash
# Create test file in tests/
# Follow naming: test_*.py

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## Coding Standards

### Python Style

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/):

```bash
# Check style
flake8 bot.py

# Auto-format code
black bot.py --line-length 100
```

### Code Requirements

- **Clear variable names**: `post_id` not `p_id`
- **Meaningful messages**: "Published post" not "Done"
- **Type hints** (Python 3.7+): `def publish_post(self, content: str) -> str:`
- **Docstrings**: Explain what, why, how
- **Comments**: For complex logic only
- **DRY**: Don't repeat yourself
- **SOLID principles**: Single responsibility, etc.

### Example Function

```python
def publish_post(self, content: str, delete_after_hours: Optional[int] = None) -> str:
    """
    Publish a post immediately.
    
    Args:
        content (str): Post content
        delete_after_hours (int, optional): Auto-delete after N hours
    
    Returns:
        str: Post ID or None on error
    
    Raises:
        ValueError: If content is empty
    
    Example:
        >>> bot = AutoPostBot()
        >>> post_id = bot.publish_post("Hello")
        >>> log.info(f"Published: {post_id}")
    """
    if not content:
        raise ValueError("Content cannot be empty")
    
    # Implementation...
    return post_id
```

### Docstring Template

```python
def function_name(self, param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief description of what function does.
    
    Longer description if needed. Explain the purpose, behavior,
    and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ExceptionType: When this exception is raised
    
    Example:
        >>> result = function_name(value1, value2)
        >>> print(result)
    """
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_bot.py::TestAutoPostBot::test_publish_post -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run specific file
pytest tests/test_bot.py -v
```

### Writing Tests

```python
import unittest
from bot import AutoPostBot

class TestMyFeature(unittest.TestCase):
    """Test suite for new feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = AutoPostBot()
    
    def tearDown(self):
        """Clean up after tests"""
        self.bot.shutdown()
    
    def test_feature_works(self):
        """Test that feature works correctly"""
        result = self.bot.my_feature()
        self.assertTrue(result)
    
    def test_feature_error_handling(self):
        """Test error handling"""
        with self.assertRaises(ValueError):
            self.bot.my_feature(invalid_param)
```

### Test Coverage

- Aim for 80%+ coverage
- Test success cases and errors
- Test edge cases
- Test integration between components

## Pull Request Process

### 1. Prepare Your Changes

```bash
# Update from upstream
git fetch upstream
git rebase upstream/main

# Format code
black .

# Run tests
pytest tests/ -v

# Check style
flake8 .
```

### 2. Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

Body explaining the change (optional)

Fixes #123
```

Examples:
- `feat(publish): add batch publishing`
- `fix(timezone): correct UTC conversion`
- `docs(readme): update installation steps`
- `test(scheduler): improve test coverage`
- `refactor(storage): simplify JSON handling`

### 3. Create Pull Request

1. Push your branch: `git push origin feature/your-feature`
2. Go to GitHub repository
3. Click "New Pull Request"
4. Fill in the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation
- [ ] Refactoring
- [ ] Other

## Related Issues
Closes #123

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Tested on multiple Python versions

## Checklist
- [ ] Code follows style guidelines
- [ ] Docstrings added/updated
- [ ] No new warnings generated
- [ ] CHANGELOG.md updated
```

### 4. Code Review

- Respond to feedback promptly
- Make requested changes
- Don't force-push (append commits instead)
- Rebase when ready

### 5. Merge

- Maintainer merges PR
- PR appears in CHANGELOG.md
- Create release if needed

## Reporting Issues

### Bug Reports

**Title:** Brief description (e.g., "Bot crashes on invalid timezone")

**Body:**
```markdown
## Describe the Bug
Clear description of the problem

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: (Windows/macOS/Linux)
- Python: (3.7/3.8/3.9)
- Version: (1.0.0)

## Logs
```
Error message here
```
```

### Feature Requests

**Title:** Brief description (e.g., "Add cron scheduling support")

**Body:**
```markdown
## Description
Explain the feature and why it's useful

## Use Case
How would you use this feature?

## Alternatives
Are there current workarounds?

## Example
Show how the feature would be used
```

## Project Structure

```
lililililitili/
├── bot.py                 # Core bot class
├── tests/
│   ├── test_bot.py       # Main tests
│   └── __init__.py
├── examples.py            # Usage examples
├── quickstart.py          # Interactive guide
├── telegram_bot.py        # Telegram integration
├── platform_integrations.py # Other platforms
├── requirements.txt       # Dependencies
├── setup.py              # Package setup
├── README.md             # English docs
├── README_RU.md          # Russian docs
├── INSTALLING.md         # Installation guide
├── CHANGELOG.md          # Version history
├── CONTRIBUTING.md       # This file
├── LICENSE              # MIT License
└── .gitignore
```

## Development Tips

### Useful Commands

```bash
# Format code
black .

# Check style
flake8 bot.py

# Type checking
mypy bot.py

# Run tests
pytest tests/ -v

# Help with git
git status
git diff
git log --oneline
```

### IDE Setup

**VS Code:**
```json
{
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.linting.pylintEnabled": false,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python"
  }
}
```

**PyCharm:**
- Settings → Code Style → Python → set to PEP 8
- Settings → Tools → Python Integrated Tools → Default test runner → pytest

## Questions?

- Open a GitHub issue with label `question`
- Check existing discussions
- Read documentation thoroughly first

---

**Thank you for contributing!** 🎉
