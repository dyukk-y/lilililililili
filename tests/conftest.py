"""
Pytest configuration and shared fixtures
"""

import os
import tempfile
import pytest
from bot import AutoPostBot


@pytest.fixture
def temp_storage():
    """Create a temporary storage file for tests"""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def bot(temp_storage):
    """Create a bot instance with temporary storage"""
    bot_instance = AutoPostBot(storage_file=temp_storage)
    yield bot_instance
    # Cleanup
    bot_instance.shutdown()


@pytest.fixture
def sample_post_data():
    """Sample post data for testing"""
    return {
        "id": "1",
        "content": "Test post content",
        "status": "published",
        "published_at": "2026-02-23T15:30:00+07:00"
    }


@pytest.fixture
def multiple_posts_data():
    """Multiple sample posts for testing"""
    return {
        "1": {
            "id": "1",
            "content": "First post",
            "status": "published",
        },
        "2": {
            "id": "2",
            "content": "Second post",
            "status": "scheduled",
        },
        "3": {
            "id": "3",
            "content": "Third post",
            "status": "published",
        }
    }
