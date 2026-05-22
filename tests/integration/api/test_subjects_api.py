"""FR-STU-06, STU-12: subject master API."""

import pytest

from students.models import Subject


@pytest.mark.integration
@pytest.mark.api
def test_create_and_list_subjects(jwt_api_client, user):
    res = jwt_api_client.post("/api/v1/subjects/", {"name": "수학"}, format="json")
    assert res.status_code == 201, res.content
    res = jwt_api_client.get("/api/v1/subjects/")
    assert res.status_code == 200
    names = [s["name"] for s in res.json()["results"]]
    assert "수학" in names


@pytest.mark.integration
@pytest.mark.api
def test_subjects_scoped_to_owner(jwt_api_client, other_user):
    Subject.objects.create(owner=other_user, name="비밀과목")
    res = jwt_api_client.get("/api/v1/subjects/")
    assert all(s["name"] != "비밀과목" for s in res.json()["results"])
