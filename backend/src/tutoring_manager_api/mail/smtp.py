import smtplib
from email.message import EmailMessage

from tutoring_manager_api.config import Settings
from tutoring_manager_api.mail.base import MailSender


class SmtpMailSender(MailSender):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send(self, *, to: str, subject: str, body_text: str, body_html: str | None = None) -> None:
        msg = EmailMessage()
        msg["From"] = self._settings.mail_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body_text)
        if body_html:
            msg.add_alternative(body_html, subtype="html")

        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port) as smtp:
            if self._settings.smtp_use_tls:
                smtp.starttls()
            if self._settings.smtp_user:
                smtp.login(self._settings.smtp_user, self._settings.smtp_password)
            smtp.send_message(msg)
