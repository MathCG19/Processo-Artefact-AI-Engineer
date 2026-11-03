from datetime import date

import pytest

from emporio_agent.data import load_store_data

# Fixed "today" so date-based assertions are reproducible.
TODAY = date(2026, 11, 3)


@pytest.fixture(scope="session")
def data():
    return load_store_data()
