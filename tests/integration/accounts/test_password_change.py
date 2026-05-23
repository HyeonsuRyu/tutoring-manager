"""Password change form shows field errors below current password input."""

import pytest


@pytest.mark.integration
def test_wrong_current_password_shows_field_error(logged_in_client, user):
    res = logged_in_client.post(
        "/accounts/password/change/",
        {
            "oldpassword": "wrong-password",
            "password1": "NewSecure123!",
            "password2": "NewSecure123!",
        },
    )
    assert res.status_code == 200
    html = res.content.decode()
    assert "비밀번호가 틀렸습니다." in html
    assert 'class="field-error"' in html
    assert "auth-password-input--invalid" in html or "auth-form-field--error" in html
