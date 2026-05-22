"""FR-STU-04: timezone suggestion HTTP endpoint."""

import pytest


@pytest.mark.integration
def test_timezone_suggest_json(logged_in_client):
    res = logged_in_client.get("/students/timezone-suggest.json", {"timezone": "Asia/Seoul"})
    assert res.status_code == 200
    data = res.json()
    assert "suggestions" in data
    assert "Asia/Seoul" in data["suggestions"]
