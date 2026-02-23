# GitHub Configuration

This directory contains GitHub-specific configuration files.

## Contents

### Workflows (.github/workflows/)
- `tests.yml` - Automated testing on multiple Python versions and OS
  - Runs tests when pushing to main/develop
  - Checks code style
  - Builds Docker image
  - Reports coverage

### Issue Templates (.github/ISSUE_TEMPLATE/)
- `bug_report.yml` - Template for bug reports
- `feature_request.yml` - Template for feature requests

### PR Template
- `pull_request_template.md` - Template for pull requests

## How to Use

### Creating an Issue
1. Click "New issue" on GitHub
2. Choose "Bug Report" or "Feature Request"
3. Fill out the template
4. Submit

### Creating a Pull Request
1. Push your branch to your fork
2. Click "New pull request"
3. Fill out the PR template
4. Submit for review

## Automated Workflows

### On Push
- Code is automatically tested
- Style is checked
- Coverage is reported
- Docker image is built

### On Pull Request
- All checks must pass
- Code review is required
- At least one approval needed (configurable)

## Status Badges

Add these to your README:

```markdown
![Tests](https://github.com/dyukk-y/lilililililili/workflows/Tests/badge.svg)
[![Codecov](https://codecov.io/gh/dyukk-y/lilililililili/branch/main/graph/badge.svg)](https://codecov.io/gh/dyukk-y/lilililililili)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

## Configuring

### Branch Protection Rules
Go to Settings → Branches → Add rule
- Require status checks to pass
- Require code reviews
- Require branches to be up to date

### Workflow Permissions
Go to Settings → Actions → General
- Workflows: Read and write permissions

### Secrets
Add secrets to Settings → Secrets and variables
Example:
- `CODECOV_TOKEN` - For codecov reporting
