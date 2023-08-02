from nextcord import slash_command, Interaction, SlashOption
from nextcord.ext.commands import Cog
from nextcord.ext.commands.bot import Bot
from nextcord.ext.commands.errors import ExtensionNotLoaded, ExtensionFailed

from bot_base import ADMIN_USER_IDS

import os


class Utils(Cog):
    def __init__(self, bot_client: Bot):
        self.bot = bot_client

    @slash_command(description="Send message to current channel")
    async def send_message(self, interaction: Interaction, message: str = SlashOption(
        name="message",
        description="Message to send",
        required=True
    )):
        # add channel selection from guild
        await interaction.send("Sending message...", ephemeral=True)
        await interaction.channel.send(message)

    @slash_command(description="Reload extension")
    async def reload_extension(self, interaction: Interaction, extension_name: str = SlashOption(
        name="extension",
        description="Reload given extension",
        required=True
    )):
        await interaction.send(f"🔄Reloading extension `{extension_name}`", ephemeral=True)

        if interaction.user.id not in ADMIN_USER_IDS:
            await interaction.send("❌You don't have the rights to use this command", ephemeral=True)
            return

        try:
            self.bot.reload_extension(f"extensions.{extension_name}")
        except ExtensionNotLoaded:
            await interaction.send(f"❌Extension `{extension_name}` not loaded", ephemeral=True)
        except ExtensionFailed:
            await interaction.send(f"❌Extension `{extension_name}` failed to load", ephemeral=True)
        else:
            await interaction.send(f"✅Extension `{extension_name}` reloaded successfully", ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(Utils(bot))
    print(f"Loaded extension: {os.path.basename(__file__)[:-3]}")
