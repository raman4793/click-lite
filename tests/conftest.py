import pytest


@pytest.fixture(scope="session")
def valid_docstring_mock_function(a: int = 5, b: int = 5) -> int:
    """
    A valid mock function used to test docstring parser, for the sake of functionality
    it returns the sum of two arguments.
    Args:
        a: The first argument.
        b: The second argument.

    Returns:
        sum: int
    """
    return a + b
