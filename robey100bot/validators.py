from urllib.parse import urlparse

ALLOWED_CLIP_DOMAINS = {
    "youtube.com": ["/watch", "/shorts"],
    "youtu.be": [],
    "tiktok.com": [],
    "instagram.com": [],
}


def is_valid_clip_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    host = parsed.hostname
    if not host:
        return False

    host = host.lower()
    return any(
        (host == domain or host.endswith(f".{domain}"))
        and (
            not required_contents
            or any(parsed.path.startswith(path) for path in required_contents)
        )
        for domain, required_contents in ALLOWED_CLIP_DOMAINS.items()
    )