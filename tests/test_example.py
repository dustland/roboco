"""
Example Test Module

This module demonstrates how to write tests for the Roboco application.
"""
import pytest


def test_example():
    """A simple example test to verify pytest is working."""
    assert True


def test_with_fixture(db_engine):
    """An example test that uses a fixture."""
    assert db_engine is not None


class TestExample:
    """A test class demonstrating class-based tests."""
    
    def test_in_class(self):
        """Test method in a class."""
        assert 1 + 1 == 2
    
    def test_with_fixture_in_class(self, db_engine):
        """Test method in a class that uses a fixture."""
        assert db_engine is not None


@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (2, 3, 5),
    (0, 0, 0),
])
def test_parametrized(a, b, expected):
    """Test that demonstrates parametrized tests."""
    assert a + b == expected 