"""Backup code generation and verification (hashed at rest)."""

from __future__ import annotations

import secrets

from django.contrib.auth.hashers import check_password, make_password

from accounts.models import BackupCode

BACKUP_CODE_COUNT = 8


def generate_backup_codes(user) -> list[str]:
    """Create one-time backup codes; only plaintext values are returned to the caller."""
    BackupCode.objects.filter(user=user).delete()
    plain_codes: list[str] = []
    for _ in range(BACKUP_CODE_COUNT):
        plain = secrets.token_hex(4)
        row = BackupCode(user=user)
        row.set_code(plain)
        row.save()
        plain_codes.append(plain)
    return plain_codes


def verify_backup_code(user, plain: str) -> bool:
    """Match plain input against stored hashes; mark the code used on success."""
    token = plain.strip()
    if not token:
        return False
    for backup in BackupCode.objects.filter(user=user, used=False):
        if check_password(token, backup.code_hash):
            backup.used = True
            backup.save(update_fields=["used"])
            return True
    return False
