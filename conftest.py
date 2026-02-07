"""
Root conftest.py - re-exports all fixtures from tests/conftest.py
so they are available to all test directories listed in pytest.ini testpaths.
"""
from tests.conftest import *  # noqa: F401, F403
