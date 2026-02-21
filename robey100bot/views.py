import discord


class SubmissionActionsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Mark as Reviewed",
        style=discord.ButtonStyle.success,
        custom_id="clip_submission_reviewed",
    )
    async def mark_as_reviewed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "You need `Manage Messages` permission to review submissions.",
                ephemeral=True,
            )
            return

        if interaction.message is None:
            await interaction.response.send_message(
                "Could not find this submission message.",
                ephemeral=True,
            )
            return

        if not interaction.message.embeds:
            await interaction.response.send_message(
                "This submission has no embed to update.",
                ephemeral=True,
            )
            return

        embed = interaction.message.embeds[0].copy()
        embed.color = discord.Color.green()
        embed.title = "✅ Clip Submission Reviewed"
        embed.description = "This clip has been reviewed."
        embed.add_field(name="Reviewed By", value=interaction.user.mention, inline=True)
        embed.add_field(
            name="Reviewed At",
            value=discord.utils.format_dt(discord.utils.utcnow(), style="f"),
            inline=True,
        )
        embed.set_footer(text="Clip Review Queue • Reviewed")

        button.disabled = True
        button.label = "Reviewed"

        await interaction.response.edit_message(embed=embed, view=self)