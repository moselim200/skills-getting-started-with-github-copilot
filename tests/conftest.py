from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def activity_state():
    original_activities = deepcopy(activities)
    try:
        yield original_activities
    finally:
        activities.clear()
        activities.update(original_activities)


@pytest.fixture
def client(activity_state):
    with TestClient(app) as test_client:
        yield test_client
