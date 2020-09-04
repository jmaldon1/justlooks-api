"""We can define the fixture functions in this
file to make them accessible across multiple test files.
"""
import pytest


@pytest.fixture
def api_endpoint():
    """Api endpoint that can be passed as a parameter to any test
    """
    return "http://localhost:5000/api/"
