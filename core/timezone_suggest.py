"""IANA timezone suggestions from country/city. See docs/students.md."""

from __future__ import annotations

from zoneinfo import available_timezones

# Country default + city overrides (MVP mapping table)
_COUNTRY_DEFAULT: dict[str, str] = {
    "KR": "Asia/Seoul",
    "JP": "Asia/Tokyo",
    "US": "America/New_York",
    "GB": "Europe/London",
    "CN": "Asia/Shanghai",
    "AU": "Australia/Sydney",
    "CA": "America/Toronto",
    "DE": "Europe/Berlin",
    "FR": "Europe/Paris",
    "SG": "Asia/Singapore",
    "VN": "Asia/Ho_Chi_Minh",
    "TH": "Asia/Bangkok",
}

_CITY_OVERRIDES: dict[tuple[str, str], str] = {
    ("KR", "서울"): "Asia/Seoul",
    ("KR", "부산"): "Asia/Seoul",
    ("KR", "제주"): "Asia/Seoul",
    ("US", "Los Angeles"): "America/Los_Angeles",
    ("US", "New York"): "America/New_York",
    ("US", "Chicago"): "America/Chicago",
    ("US", "Seattle"): "America/Los_Angeles",
    ("GB", "London"): "Europe/London",
    ("AU", "Sydney"): "Australia/Sydney",
    ("AU", "Melbourne"): "Australia/Melbourne",
    ("CA", "Vancouver"): "America/Vancouver",
    ("CA", "Toronto"): "America/Toronto",
}


def suggest_timezone(country: str, city: str = "") -> list[str]:
    country = (country or "KR").strip().upper()
    city_key = (city or "").strip()
    suggestions: list[str] = []

    if city_key:
        override = _CITY_OVERRIDES.get((country, city_key))
        if override:
            suggestions.append(override)
        # partial city match
        for (c, city_name), tz in _CITY_OVERRIDES.items():
            if c == country and city_key.lower() in city_name.lower():
                if tz not in suggestions:
                    suggestions.append(tz)

    default = _COUNTRY_DEFAULT.get(country, "UTC")
    if default not in suggestions:
        suggestions.append(default)

    # common zones for country prefix
    prefix = country[:2].lower() if len(country) >= 2 else ""
    for tz in sorted(available_timezones()):
        if tz.startswith("Asia/") and country in ("KR", "JP", "CN", "SG", "VN", "TH"):
            if tz not in suggestions and len(suggestions) < 8:
                suggestions.append(tz)
        elif tz.startswith("America/") and country == "US" and len(suggestions) < 10:
            if tz not in suggestions:
                suggestions.append(tz)

    return suggestions[:10]


# Web form datalist (country/city 없이 직접 선택)
COMMON_TIMEZONES: list[str] = [
    "Asia/Seoul",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Asia/Ho_Chi_Minh",
    "Asia/Bangkok",
    "Asia/Dubai",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Paris",
    "America/New_York",
    "America/Chicago",
    "America/Los_Angeles",
    "America/Toronto",
    "Australia/Sydney",
    "Pacific/Auckland",
    "UTC",
]


def list_common_timezones(current: str = "") -> list[str]:
    """Deduplicated common IANA zones; current value first when set."""
    out: list[str] = []
    if current and current not in COMMON_TIMEZONES:
        out.append(current)
    for tz in COMMON_TIMEZONES:
        if tz not in out:
            out.append(tz)
    return out


TIMEZONE_LABELS_KO: dict[str, str] = {
    "Asia/Seoul": "대한민국 · 서울",
    "Asia/Tokyo": "일본 · 도쿄",
    "Asia/Shanghai": "중국 · 상하이",
    "Asia/Singapore": "싱가포르",
    "Asia/Ho_Chi_Minh": "베트남 · 호치민",
    "Asia/Bangkok": "태국 · 방콕",
    "Asia/Dubai": "아랍에미리트 · 두바이",
    "Europe/London": "영국 · 런던",
    "Europe/Berlin": "독일 · 베를린",
    "Europe/Paris": "프랑스 · 파리",
    "America/New_York": "미국 · 뉴욕(동부)",
    "America/Chicago": "미국 · 시카고(중부)",
    "America/Los_Angeles": "미국 · 로스앤젤레스(태평양)",
    "America/Toronto": "캐나다 · 토론토",
    "Australia/Sydney": "호주 · 시드니",
    "Pacific/Auckland": "뉴질랜드 · 오클랜드",
    "UTC": "UTC (협정 세계시)",
}


def timezone_label_ko(tz: str) -> str:
    return TIMEZONE_LABELS_KO.get(tz, tz.replace("_", " ").replace("/", " · "))


def timezone_choices_ko(current: str = "") -> list[tuple[str, str]]:
    """Select choices: (IANA id, Korean label)."""
    choices: list[tuple[str, str]] = [("", "시간대 선택")]
    for tz in list_common_timezones(current):
        choices.append((tz, timezone_label_ko(tz)))
    return choices
