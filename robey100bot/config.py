import os
from dataclasses import dataclass

from dotenv import load_dotenv

@dataclass(frozen=True)
class BotSettings:
    token: str
    logs_channel_id: int
    rotating_messages_channel_id: int
    rotating_messages_min_seconds: int
    rotating_messages_max_seconds: int


def load_settings() -> BotSettings:
    load_dotenv()

    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set in the environment.")

    logs_channel_id = int(
        os.getenv("LOGS_CHANNEL_ID")
    )

    rotating_messages_channel_id = int(
        os.getenv("ROTATING_MESSAGES_CHANNEL_ID")
    )
    rotating_messages_min_seconds = 2700
    rotating_messages_max_seconds = 5400

    if rotating_messages_min_seconds <= 0 or rotating_messages_max_seconds <= 0:
        raise RuntimeError("Rotating message interval values must be positive integers.")

    if rotating_messages_min_seconds > rotating_messages_max_seconds:
        raise RuntimeError(
            "ROTATING_MESSAGES_MIN_SECONDS cannot be greater than ROTATING_MESSAGES_MAX_SECONDS."
        )

    return BotSettings(
        token=token,
        logs_channel_id=logs_channel_id,
        rotating_messages_channel_id=rotating_messages_channel_id,
        rotating_messages_min_seconds=rotating_messages_min_seconds,
        rotating_messages_max_seconds=rotating_messages_max_seconds,
    )