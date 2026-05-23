from django import forms
from django.contrib.auth.forms import AuthenticationForm
from allauth.account.forms import ChangePasswordForm as AllauthChangePasswordForm

from accounts.models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="이메일", widget=forms.EmailInput(attrs={"autofocus": True}))


class ChangePasswordForm(AllauthChangePasswordForm):
    """Show field-level errors below inputs (Korean messages)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widget_class = "auth-password-input"
        for name in ("oldpassword", "password1", "password2"):
            self.fields[name].widget.attrs["class"] = widget_class

    def add_error(self, field, error):
        super().add_error(field, error)
        if field in self.fields:
            self.fields[field].widget.attrs["class"] = "auth-password-input auth-password-input--invalid"

    def clean_oldpassword(self):
        pwd = self.cleaned_data.get("oldpassword")
        if not pwd:
            raise forms.ValidationError("현재 비밀번호를 입력하세요.", code="required")
        if not self.user.check_password(pwd):
            raise forms.ValidationError("비밀번호가 틀렸습니다.", code="incorrect")
        return pwd


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(label="비밀번호", widget=forms.PasswordInput)
    password2 = forms.CharField(label="비밀번호 확인", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email",)

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
