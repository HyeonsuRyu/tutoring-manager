import os


def resolve_domain() -> tuple[str, bool]:
    """Return (domain_str, is_localhost_only). Empty or 'local' => localhost mode."""
    raw = os.environ.get("DOMAIN", "").strip()
    if not raw or raw.lower() == "local":
        return "", True
    return raw, False


def get_allowed_hosts() -> list[str]:
    domain, local = resolve_domain()
    if local:
        return ["localhost", "127.0.0.1"]
    return [domain]


def get_csrf_trusted_origins() -> list[str]:
    domain, local = resolve_domain()
    if local:
        return ["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8080", "http://127.0.0.1:8080"]
    return [f"https://{domain}", f"http://{domain}"]
