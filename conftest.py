import pytest
from django.db import connections

@pytest.fixture(autouse=True)
def close_db_connections():
    yield
    for conn in connections.all():
        conn.close()
