"""FR-ACC-05: protected web routes require login."""

import pytest


@pytest.mark.integration
def test_weekly_report_requires_login(web_client):
    res = web_client.get("/reports/weekly/")
    assert res.status_code == 302
    assert "/accounts/login" in res.url


@pytest.mark.integration
def test_calendar_events_json_requires_login(web_client):
    res = web_client.get("/events.json", {"start": "2026-01-01", "end": "2026-01-31"})
    assert res.status_code == 302


@pytest.mark.integration
def test_subject_settings_requires_login(web_client):
    res = web_client.get("/students/settings/subjects/")
    assert res.status_code == 302
