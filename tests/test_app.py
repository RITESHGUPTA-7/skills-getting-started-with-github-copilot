import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

# keep a pristine copy of the activities map so tests can restore it
_original_activities = copy.deepcopy(activities)


def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))


def test_root_redirect():
    # Arrange
    reset_activities()

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    # the root endpoint should redirect to the static index page
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    # Arrange
    reset_activities()

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # keys should match the original activities set
    assert data.keys() == _original_activities.keys()


def test_signup_and_duplicate_prevention():
    # Arrange
    reset_activities()
    activity = "Chess Club"
    email = "newstudent@example.com"

    # Act - first signup
    resp1 = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert - first signup succeeded
    assert resp1.status_code == 200
    assert resp1.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in activities[activity]["participants"]

    # Act - duplicate signup attempt
    resp2 = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert - should error with 400
    assert resp2.status_code == 400
    assert "already signed up" in resp2.json()["detail"]


def test_remove_participant_and_404_cases():
    # Arrange
    reset_activities()
    activity = "Programming Class"
    existing_email = "emma@mergington.edu"
    non_existing_activity = "Nonexistent"
    non_existing_email = "ghost@example.com"

    # Act - remove existing participant
    resp1 = client.delete(f"/activities/{activity}/participants", params={"email": existing_email})

    # Assert - removal succeeded
    assert resp1.status_code == 200
    assert resp1.json() == {"message": f"Removed {existing_email} from {activity}"}
    assert existing_email not in activities[activity]["participants"]

    # Act - remove from non-existent activity
    resp2 = client.delete(f"/activities/{non_existing_activity}/participants", params={"email": existing_email})

    # Assert - 404 for activity
    assert resp2.status_code == 404

    # Act - remove non-participant from real activity
    resp3 = client.delete(f"/activities/{activity}/participants", params={"email": non_existing_email})

    # Assert - 404 for missing participant
    assert resp3.status_code == 404
