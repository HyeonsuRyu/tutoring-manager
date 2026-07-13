from tutoring_manager_api.config import Settings
from tutoring_manager_api.mail.base import LoggingMailSender, MailSender
from tutoring_manager_api.mail.smtp import SmtpMailSender


def get_mail_sender(settings: Settings) -> MailSender:
    if settings.smtp_host:
        return SmtpMailSender(settings)
    return LoggingMailSender()
