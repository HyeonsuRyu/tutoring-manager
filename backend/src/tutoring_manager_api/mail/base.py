from abc import ABC, abstractmethod


class MailSender(ABC):
    @abstractmethod
    def send(self, *, to: str, subject: str, body_text: str, body_html: str | None = None) -> None:
        """Send a transactional email. Swap SMTP for an API provider later."""


class LoggingMailSender(MailSender):
    """Dev fallback when SMTP is unavailable — never log full PII beyond the address needed to deliver."""

    def send(self, *, to: str, subject: str, body_text: str, body_html: str | None = None) -> None:
        # Intentionally omit body from logs (may contain tokens).
        print(f"[mail] to={to!r} subject={subject!r} chars={len(body_text)}")
