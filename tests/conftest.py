import pytest
import os
import tempfile

@pytest.fixture
def temp_profile():
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)
    yield path
    os.unlink(path)
