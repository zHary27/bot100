import discord

from robey100bot import Robey100Bot, load_settings


def main() -> None:
    settings = load_settings()
    intents = discord.Intents.default()
    bot = Robey100Bot(
        logs_channel_id=settings.logs_channel_id,
        rotating_messages_channel_id=settings.rotating_messages_channel_id,
        rotating_messages_min_seconds=settings.rotating_messages_min_seconds,
        rotating_messages_max_seconds=settings.rotating_messages_max_seconds,
        intents=intents,
    )
    bot.run(settings.token)


if __name__ == "__main__":
    main()