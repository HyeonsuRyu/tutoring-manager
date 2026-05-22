"""Fixtures for integration tests (database + HTTP)."""

from django.test import Client
from django.utils import timezone

import pytest
from rest_framework.test import APIClient

from tests.factories import ScheduleSlotFactory, StudentFactory, UserFactory

HOST = "127.0.0.1"


class HostClient:
    """Django test client that always sends ALLOWED_HOSTS-compatible Host."""

    def __init__(self, client: Client):
        self._client = client

    def get(self, path, data=None, follow=False, **extra):
        extra.setdefault("HTTP_HOST", HOST)
        return self._client.get(path, data=data, follow=follow, **extra)

    def post(self, path, data=None, follow=False, **extra):
        extra.setdefault("HTTP_HOST", HOST)
        return self._client.post(path, data=data, follow=follow, **extra)

    def patch(self, path, data=None, **extra):
        extra.setdefault("HTTP_HOST", HOST)
        return self._client.patch(path, data=data, content_type="application/json", **extra)

    def force_login(self, user):
        self._client.force_login(user)

    @property
    def session(self):
        return self._client.session


@pytest.fixture
def web_client(client):
    return HostClient(client)


@pytest.fixture
def logged_in_client(web_client, user):
    web_client.force_login(user)
    return web_client


@pytest.fixture
def user(db):
    return UserFactory(email="tutor@example.com", password="testpass123")


@pytest.fixture
def other_user(db):
    return UserFactory(email="other@example.com", password="testpass123")


@pytest.fixture
def student(user):
    return StudentFactory(owner=user, name="김학생", lessons_completed=2)


@pytest.fixture
def schedule_slot(student):
    return ScheduleSlotFactory(
        student=student,
        day_of_week=1,
        start_time=timezone.datetime(2000, 1, 1, 19, 0).time(),
        end_time=timezone.datetime(2000, 1, 1, 20, 30).time(),
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_api_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def jwt_api_client(api_client, user):
    res = api_client.post(
        "/api/v1/auth/token/",
        {"email": user.email, "password": "testpass123"},
        format="json",
    )
    assert res.status_code == 200, res.data
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    return api_client
