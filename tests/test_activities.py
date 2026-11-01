from copy import deepcopy

import pytest

from src.app import activities


def test_root_redirects_to_static_page(client):
    endpoint = "/"
    expected_location = "/static/index.html"

    response = client.get(endpoint, follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_static_page_is_served(client):
    endpoint = "/static/index.html"
    expected_title = "<title>Mergington High School Activities</title>"

    response = client.get(endpoint)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert expected_title in response.text


def test_get_activities_returns_details_without_mutation(client, activity_state):
    endpoint = "/activities"
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    response = client.get(endpoint)

    assert response.status_code == 200
    assert response.json() == activity_state
    for details in response.json().values():
        assert set(details) == expected_fields
        assert isinstance(details["description"], str)
        assert isinstance(details["schedule"], str)
        assert isinstance(details["max_participants"], int)
        assert isinstance(details["participants"], list)
        assert all(isinstance(email, str) for email in details["participants"])
    assert activities == activity_state


def test_signup_adds_only_selected_participant(client, activity_state):
    activity_name = "Art Club"
    email = "student+art@mergington.edu"
    endpoint = f"/activities/{activity_name}/signup"
    expected_state = deepcopy(activity_state)
    expected_state[activity_name]["participants"].append(email)
    expected_message = f"Signed up {email} for {activity_name}"

    response = client.post(endpoint, params={"email": email})
    listing = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {"message": expected_message}
    assert listing.status_code == 200
    assert listing.json() == expected_state
    assert activities == expected_state


def test_unregister_removes_only_selected_participant(client, activity_state):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    endpoint = f"/activities/{activity_name}/unregister"
    expected_state = deepcopy(activity_state)
    expected_state[activity_name]["participants"].remove(email)
    expected_message = f"Unregistered {email} from {activity_name}"

    response = client.delete(endpoint, params={"email": email})
    listing = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {"message": expected_message}
    assert listing.status_code == 200
    assert listing.json() == expected_state
    assert activities == expected_state


@pytest.mark.parametrize(
    "method, activity_name, action, email, expected_status, expected_detail",
    [
        ("POST", "Unknown", "signup", "student@mergington.edu", 404, "Activity not found"),
        (
            "POST", "Chess Club", "signup", "michael@mergington.edu",
            400, "Student is already signed up",
        ),
        (
            "DELETE", "Unknown", "unregister", "michael@mergington.edu",
            404, "Activity not found",
        ),
        (
            "DELETE", "Chess Club", "unregister", "missing@mergington.edu",
            400, "Student is not signed up",
        ),
    ],
)
def test_rejected_mutations_preserve_state(
    client, activity_state, method, activity_name, action, email,
    expected_status, expected_detail,
):
    endpoint = f"/activities/{activity_name}/{action}"
    params = {"email": email}
    expected_error = {"detail": expected_detail}

    response = client.request(method, endpoint, params=params)
    listing = client.get("/activities")

    assert response.status_code == expected_status
    assert response.json() == expected_error
    assert listing.status_code == 200
    assert listing.json() == activity_state
    assert activities == activity_state


@pytest.mark.parametrize("method, action", [("POST", "signup"), ("DELETE", "unregister")])
def test_mutations_require_email(client, activity_state, method, action):
    endpoint = f"/activities/Chess Club/{action}"
    expected_location = ["query", "email"]

    response = client.request(method, endpoint)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["loc"] == expected_location
    assert errors[0]["type"] == "missing"
    assert activities == activity_state


def test_unregister_last_participant_leaves_empty_list(client, activity_state):
    activity_name = "Art Club"
    email = "student+art@mergington.edu"
    activities[activity_name]["participants"] = [email]
    endpoint = f"/activities/{activity_name}/unregister"
    expected_state = deepcopy(activity_state)
    expected_state[activity_name]["participants"] = []

    response = client.delete(endpoint, params={"email": email})
    listing = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert listing.status_code == 200
    assert listing.json() == expected_state
    assert activities == expected_state


def test_signup_unregister_and_signup_again(client, activity_state):
    activity_name = "Art Club"
    email = "student+art@mergington.edu"
    endpoint = f"/activities/{activity_name}"
    params = {"email": email}
    registered_state = deepcopy(activity_state)
    registered_state[activity_name]["participants"].append(email)
    expected_signup = {"message": f"Signed up {email} for {activity_name}"}
    expected_unregister = {"message": f"Unregistered {email} from {activity_name}"}

    signup = client.post(f"{endpoint}/signup", params=params)
    after_signup = client.get("/activities")
    duplicate_signup = client.post(f"{endpoint}/signup", params=params)
    after_duplicate = client.get("/activities")
    unregister = client.delete(f"{endpoint}/unregister", params=params)
    after_unregister = client.get("/activities")
    repeated_unregister = client.delete(f"{endpoint}/unregister", params=params)
    after_repeated_unregister = client.get("/activities")
    signup_again = client.post(f"{endpoint}/signup", params=params)
    after_signup_again = client.get("/activities")

    assert signup.status_code == 200
    assert signup.json() == expected_signup
    assert duplicate_signup.status_code == 400
    assert duplicate_signup.json() == {"detail": "Student is already signed up"}
    assert unregister.status_code == 200
    assert unregister.json() == expected_unregister
    assert repeated_unregister.status_code == 400
    assert repeated_unregister.json() == {"detail": "Student is not signed up"}
    assert signup_again.status_code == 200
    assert signup_again.json() == expected_signup
    for listing in (
        after_signup, after_duplicate, after_unregister,
        after_repeated_unregister, after_signup_again,
    ):
        assert listing.status_code == 200
    assert after_signup.json() == registered_state
    assert after_duplicate.json() == registered_state
    assert after_unregister.json() == activity_state
    assert after_repeated_unregister.json() == activity_state
    assert after_signup_again.json() == registered_state
    assert activities == registered_state
