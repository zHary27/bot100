from __future__ import annotations

import re
from urllib.parse import parse_qs, quote, urlparse

import aiohttp

OG_IMAGE_PATTERNS = [
    re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', re.IGNORECASE),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image(?::src)?["\']', re.IGNORECASE),
]


def get_platform_name(url: str) -> str:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if "youtu" in host:
        return "YouTube"
    if "tiktok" in host:
        return "TikTok"
    if "instagram" in host:
        return "Instagram"
    return "Unknown"


def get_youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")

    if host == "youtu.be":
        video_id = parsed.path.strip("/")
        return video_id or None

    if host == "youtube.com":
        if parsed.path == "/watch":
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            return video_id

        if parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/shorts/", 1)[1].split("/", 1)[0]
            return video_id or None

    return None


def get_youtube_thumbnail(url: str) -> str | None:
    video_id = get_youtube_video_id(url)
    if video_id:
        return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    return None


async def _fetch_oembed_thumbnail(url: str, session: aiohttp.ClientSession) -> str | None:
    host = (urlparse(url).hostname or "").lower()
    if "tiktok" not in host:
        return None

    endpoint = f"https://www.tiktok.com/oembed?url={quote(url, safe='')}"

    try:
        async with session.get(endpoint) as response:
            if response.status != 200:
                return None
            payload = await response.json(content_type=None)
            return payload.get("thumbnail_url")
    except (aiohttp.ClientError, ValueError):
        return None


async def _fetch_html_thumbnail(url: str, session: aiohttp.ClientSession) -> str | None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/132.0.0.0 Safari/537.36"
        )
    }
    try:
        async with session.get(url, headers=headers) as response:
            if response.status >= 400:
                return None

            html = await response.text(errors="ignore")
            for pattern in OG_IMAGE_PATTERNS:
                match = pattern.search(html)
                if match:
                    return match.group(1)
    except aiohttp.ClientError:
        return None

    return None


async def get_submission_thumbnail(url: str, session: aiohttp.ClientSession | None) -> str | None:
    platform = get_platform_name(url)
    if platform == "Instagram":
        return None

    youtube_thumbnail = get_youtube_thumbnail(url)
    if youtube_thumbnail:
        return youtube_thumbnail

    if session is None:
        return None

    oembed_thumbnail = await _fetch_oembed_thumbnail(url, session)
    if oembed_thumbnail:
        return oembed_thumbnail

    return await _fetch_html_thumbnail(url, session)