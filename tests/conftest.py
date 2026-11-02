from pathlib import Path
import pytest
import os, sys

sys.path.insert(0, str(Path(__file__).parent.resolve()))
from simulation import _simulateCS


@pytest.fixture(scope="session", autouse=True)
def chdir():
    """
    Fixture that changes the current working directory to the 'test_working_directory' folder.
    This fixture is automatically used for the entire session.
    """
    original_cwd = Path.cwd()
    os.chdir(Path(__file__).parent.absolute() / "test_working_directory")
    try:
        yield
    finally:
        os.chdir(original_cwd)  # reset to original working directory after tests

def pytest_addoption(parser: pytest.Parser):
    """Define a parameter 'show', so that results can be shown when running tests 'manually'."""
    parser.addoption("--show", action="store", default=False)


@pytest.fixture(scope="session")
def show(request: pytest.FixtureRequest):
    return request.config.getoption("--show") == "False"

