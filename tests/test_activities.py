import unittest
from copy import deepcopy

from fastapi.testclient import TestClient

from src.app import activities, app


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.original_activities = deepcopy(activities)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.addCleanup(self.restore_activities)

    def restore_activities(self):
        activities.clear()
        activities.update(self.original_activities)

    def test_unregister_removes_only_selected_participant(self):
        response = self.client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "message": "Unregistered michael@mergington.edu from Chess Club"
        })
        current = self.client.get("/activities").json()
        self.assertEqual(
            current["Chess Club"]["participants"], ["daniel@mergington.edu"]
        )
        self.assertEqual(current["Programming Class"], self.original_activities["Programming Class"])

    def test_unregister_unknown_activity(self):
        response = self.client.delete(
            "/activities/Unknown/unregister", params={"email": "michael@mergington.edu"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Activity not found"})
        self.assertEqual(activities, self.original_activities)

    def test_unregister_missing_participant(self):
        response = self.client.delete(
            "/activities/Chess Club/unregister", params={"email": "missing@mergington.edu"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Student is not signed up"})
        self.assertEqual(activities, self.original_activities)

    def test_signup_unregister_and_signup_again(self):
        endpoint = "/activities/Art Club"
        params = {"email": "student+art@mergington.edu"}
        self.assertEqual(self.client.post(f"{endpoint}/signup", params=params).status_code, 200)
        self.assertEqual(self.client.post(f"{endpoint}/signup", params=params).status_code, 400)
        self.assertEqual(self.client.delete(f"{endpoint}/unregister", params=params).status_code, 200)
        self.assertEqual(activities["Art Club"]["participants"], [])
        self.assertEqual(self.client.delete(f"{endpoint}/unregister", params=params).status_code, 400)
        self.assertEqual(self.client.post(f"{endpoint}/signup", params=params).status_code, 200)

    def test_unregister_requires_email(self):
        self.assertEqual(
            self.client.delete("/activities/Chess Club/unregister").status_code, 422
        )
        self.assertEqual(activities, self.original_activities)
