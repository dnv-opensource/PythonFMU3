def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requirements(pkg): mark test as requiring the specified package"
    )
