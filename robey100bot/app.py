import discord
from discord import app_commands
import aiohttp
from pathlib import Path
import random
import asyncio

from .message_pool import ROTATING_MESSAGES
from .media import get_platform_name, get_submission_thumbnail
from .validators import is_valid_clip_url
from .views import SubmissionActionsView

IMAGES_DIR = Path(__file__).resolve().parent.parent / "assets" / "images"
ROBEY_DIR = IMAGES_DIR / "robey"
ROBEY_EXTENSIONS = {".gif", ".png", ".jpg", ".jpeg", ".webp"}


class Robey100Bot(discord.Client):
    def __init__(
        self,
        logs_channel_id: int,
        rotating_messages_channel_id: int,
        rotating_messages_min_seconds: int,
        rotating_messages_max_seconds: int,
        intents: discord.Intents,
    ):
        super().__init__(intents=intents)
        self.logs_channel_id = logs_channel_id
        self.rotating_messages_channel_id = rotating_messages_channel_id
        self.rotating_messages_min_seconds = rotating_messages_min_seconds
        self.rotating_messages_max_seconds = rotating_messages_max_seconds
        self.http_session: aiohttp.ClientSession | None = None
        self.rotating_messages_task: asyncio.Task | None = None
        self.tree = app_commands.CommandTree(self)
        self._register_commands()

    async def setup_hook(self):
        timeout = aiohttp.ClientTimeout(total=6)
        self.http_session = aiohttp.ClientSession(timeout=timeout)
        self.add_view(SubmissionActionsView())
        self.rotating_messages_task = asyncio.create_task(self._run_rotating_messages())

    async def close(self):
        if self.rotating_messages_task:
            self.rotating_messages_task.cancel()
            try:
                await self.rotating_messages_task
            except asyncio.CancelledError:
                pass

        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
        await super().close()

    async def _run_rotating_messages(self) -> None:
        await self.wait_until_ready()

        while not self.is_closed():
            wait_time = random.randint(
                self.rotating_messages_min_seconds,
                self.rotating_messages_max_seconds,
            )
            await asyncio.sleep(wait_time)

            channel = self.get_channel(self.rotating_messages_channel_id)
            if channel is None:
                try:
                    channel = await self.fetch_channel(self.rotating_messages_channel_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    continue

            if not isinstance(channel, (discord.TextChannel, discord.Thread)):
                continue

            if not ROTATING_MESSAGES:
                continue

            message = random.choice(ROTATING_MESSAGES)
            try:
                await channel.send(message)
            except (discord.Forbidden, discord.HTTPException):
                continue

    def _register_commands(self) -> None:
        @self.tree.command(name="ping", description="Responds with pong")
        async def ping(interaction: discord.Interaction):
            await interaction.response.send_message("pong")

        @self.tree.command(name="talk", description="Talk through the bot")
        @app_commands.describe(message="Message for the bot to say")
        @app_commands.default_permissions(administrator=True)
        @app_commands.checks.has_permissions(administrator=True)
        async def talk(interaction: discord.Interaction, message: str):
            await interaction.response.send_message("Message Sent.", ephemeral=True)
            await interaction.channel.send(message)

        @self.tree.command(name="robey", description="Robey moment")
        async def robey(interaction: discord.Interaction):
            if not ROBEY_DIR.exists() or not ROBEY_DIR.is_dir():
                await interaction.response.send_message(
                    "Robey directory not found.",
                    ephemeral=True,
                )
                return

            robey_files = [
                path
                for path in ROBEY_DIR.iterdir()
                if path.is_file() and path.suffix.lower() in ROBEY_EXTENSIONS
            ]

            if not robey_files:
                await interaction.response.send_message(
                    "No robey images found.",
                    ephemeral=True,
                )
                return

            image_path = random.choice(robey_files)

            await interaction.response.send_message(file=discord.File(image_path))

        @self.tree.command(name="submit_clip", description="Submit a clip for review")
        @app_commands.describe(url="URL of the clip")
        async def submit_clip(interaction: discord.Interaction, url: str):
            if not is_valid_clip_url(url):
                await interaction.response.send_message(
                    "Please provide a valid YouTube, TikTok, or Instagram URL.",
                    ephemeral=True,
                )
                return

            logs_channel = self.get_channel(self.logs_channel_id)
            if logs_channel:
                platform = get_platform_name(url)

                embed = discord.Embed(
                    title="New Clip Submission",
                    description="A new clip was submitted for review.",
                    color=discord.Color.blurple(),
                    timestamp=discord.utils.utcnow(),
                )
                embed.add_field(name="Creator", value=interaction.user.mention, inline=True)
                embed.add_field(name="Platform", value=platform, inline=True)
                embed.add_field(name="Clip URL", value=f"[Open clip]({url})", inline=False)
                thumbnail_url = await get_submission_thumbnail(url, self.http_session)
                if thumbnail_url:
                    embed.set_image(url=thumbnail_url)
                embed.set_author(
                    name=f"{interaction.user.display_name} ({interaction.user.id})",
                    icon_url=interaction.user.display_avatar.url,
                )
                embed.set_footer(text="Clip Review Queue")

                await logs_channel.send(embed=embed, view=SubmissionActionsView())

            await interaction.response.send_message("Clip submitted for review!", ephemeral=True)

    async def on_ready(self):
        await self.tree.sync()
        print(f"Logged in as {self.user}")