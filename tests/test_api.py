"""
Tests for the FastAPI application endpoints
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test cases for the /activities GET endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 OK"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that the activities list contains expected activities"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Club",
            "Debate Team",
            "Science Club",
            "Art Studio",
            "Music Ensemble"
        ]
        
        for activity in expected_activities:
            assert activity in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"

    def test_participants_is_list(self):
        """Test that participants field is a list"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list), \
                f"Participants in {activity_name} is not a list"


class TestSignupEndpoint:
    """Test cases for the /activities/{activity_name}/signup POST endpoint"""

    def test_signup_for_valid_activity_returns_200(self):
        """Test signing up for a valid activity returns 200"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_returns_success_message(self):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]

    def test_signup_for_invalid_activity_returns_404(self):
        """Test signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up with same email twice returns 400"""
        email = "duplicate@mergington.edu"
        activity = "Chess%20Club"
        
        # First signup should succeed
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "addedstudent@mergington.edu"
        activity = "Soccer%20Club"
        
        # Get initial participant count
        response_before = client.get("/activities")
        participants_before = response_before.json()["Soccer Club"]["participants"]
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Get updated participant count
        response_after = client.get("/activities")
        participants_after = response_after.json()["Soccer Club"]["participants"]
        
        assert len(participants_after) == len(participants_before) + 1
        assert email in participants_after

    def test_signup_with_special_characters_in_email(self):
        """Test signup with email containing special characters"""
        email = "student+plus@mergington.edu"
        response = client.post(
            f"/activities/Science%20Club/signup?email={email.replace('+', '%2B')}"
        )
        assert response.status_code == 200

    def test_signup_with_invalid_email_no_at_symbol(self):
        """Test that signup with invalid email (no @ symbol) returns 400"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=invalidemail"
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid email format" in data["detail"]

    def test_signup_with_invalid_email_no_domain(self):
        """Test that signup with invalid email (no domain) returns 400"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=student@"
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid email format" in data["detail"]

    def test_signup_with_invalid_email_no_tld(self):
        """Test that signup with invalid email (no TLD) returns 400"""
        response = client.post(
            "/activities/Gym%20Class/signup?email=student@domain"
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid email format" in data["detail"]

    def test_signup_with_spaces_in_email(self):
        """Test that signup with spaces in email returns 400"""
        response = client.post(
            "/activities/Basketball%20Team/signup?email=student%20email@domain.com"
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid email format" in data["detail"]

    def test_signup_preserves_existing_participants(self):
        """Test that signup doesn't remove existing participants"""
        response = client.get("/activities")
        music_ensemble = response.json()["Music Ensemble"]
        original_count = len(music_ensemble["participants"])
        
        client.post(
            "/activities/Music%20Ensemble/signup?email=newmusician@mergington.edu"
        )
        
        response = client.get("/activities")
        music_ensemble_after = response.json()["Music Ensemble"]
        
        assert len(music_ensemble_after["participants"]) == original_count + 1
        # Check that all original participants are still there
        for original_participant in music_ensemble["participants"]:
            assert original_participant in music_ensemble_after["participants"]


class TestRemoveParticipantEndpoint:
    """Test cases for the DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_participant_returns_200(self):
        """Test that removing a participant returns 200"""
        # First sign up
        client.post(
            "/activities/Chess%20Club/signup?email=toremove@mergington.edu"
        )
        
        # Then remove
        response = client.delete(
            "/activities/Chess%20Club/participants/toremove%40mergington.edu"
        )
        assert response.status_code == 200

    def test_remove_participant_returns_success_message(self):
        """Test that remove returns a success message"""
        email = "removeme@mergington.edu"
        
        # Sign up first
        client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        
        # Remove
        response = client.delete(
            f"/activities/Programming%20Class/participants/{email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Removed" in data["message"]

    def test_remove_nonexistent_participant_returns_404(self):
        """Test that removing non-existent participant returns 404"""
        response = client.delete(
            "/activities/Chess%20Club/participants/nothere%40mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_from_nonexistent_activity_returns_404(self):
        """Test that removing from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Club/participants/email%40mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_remove_participant_actually_removes(self):
        """Test that remove actually removes the participant"""
        email = "todelete@mergington.edu"
        activity = "Soccer%20Club"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Get initial count
        response_before = client.get("/activities")
        participants_before = response_before.json()["Soccer Club"]["participants"]
        
        # Remove
        remove_response = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert remove_response.status_code == 200
        
        # Get updated count
        response_after = client.get("/activities")
        participants_after = response_after.json()["Soccer Club"]["participants"]
        
        assert len(participants_after) == len(participants_before) - 1
        assert email not in participants_after

    def test_remove_preserves_other_participants(self):
        """Test that removing one participant doesn't affect others"""
        email_to_remove = "removeonly@mergington.edu"
        
        # Get original participants
        response_before = client.get("/activities")
        original_participants = response_before.json()["Science Club"]["participants"].copy()
        
        # Sign up new participant
        client.post(
            f"/activities/Science%20Club/signup?email={email_to_remove}"
        )
        
        # Remove the new participant
        client.delete(
            f"/activities/Science%20Club/participants/{email_to_remove}"
        )
        
        # Check that original participants are still there
        response_after = client.get("/activities")
        participants_after = response_after.json()["Science Club"]["participants"]
        
        for original_participant in original_participants:
            assert original_participant in participants_after

    def test_remove_same_participant_twice_returns_404(self):
        """Test that removing the same participant twice returns 404"""
        email = "removetwice@mergington.edu"
        activity = "Debate%20Team"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Remove first time
        response1 = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert response1.status_code == 200
        
        # Remove second time should fail
        response2 = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert response2.status_code == 404


class TestRootEndpoint:
    """Test cases for the root endpoint"""

    def test_root_redirects_to_static_index(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestDataIntegrity:
    """Test cases for data integrity"""

    def test_max_participants_field_is_positive_integer(self):
        """Test that max_participants is a positive integer"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            max_participants = activity_data["max_participants"]
            assert isinstance(max_participants, int), \
                f"max_participants in {activity_name} is not an integer"
            assert max_participants > 0, \
                f"max_participants in {activity_name} is not positive"

    def test_participants_do_not_exceed_max(self):
        """Test that current participants don't exceed max capacity"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            participant_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            assert participant_count <= max_participants, \
                f"{activity_name} has {participant_count} participants but max is {max_participants}"

    def test_schedule_field_is_not_empty(self):
        """Test that schedule field is not empty"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert activity_data["schedule"], \
                f"Schedule is empty for {activity_name}"

    def test_description_field_is_not_empty(self):
        """Test that description field is not empty"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert activity_data["description"], \
                f"Description is empty for {activity_name}"
