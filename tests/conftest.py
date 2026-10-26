import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requirements(pkg): mark test as requiring the specified package"
    )

def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--show", action="store", default=False)


@pytest.fixture(scope="session")
def show(request: pytest.FixtureRequest):
    return request.config.getoption("--show") == "False"

