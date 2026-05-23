"""Progress chart hub: pick student from sidebar flow."""

import pytest


@pytest.mark.integration
def test_progress_hub_lists_students(logged_in_client, student):
    res = logged_in_client.get("/students/progress/")
    assert res.status_code == 200
    html = res.content.decode()
    assert student.name in html
    assert f"/students/progress/{student.pk}/" in html
