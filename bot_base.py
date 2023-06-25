# DISCORD LIBS
from nextcord import Interaction
from nextcord.ext import commands

# OS TOOLS
import os
from dotenv import load_dotenv

# env vars
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# other consts
DEFAULT_EXTENSIONS: list[str] = ["player"]
DEFAULT_GUILD_IDS: list[int] = [699726889085960235]
ADMIN_USER_IDS: list[int] = [509737193749741588]

bot = commands.Bot(default_guild_ids=DEFAULT_GUILD_IDS)


# sync commands, maybe not needed but doesn't hurt
@bot.event
async def on_connect():
    await bot.sync_all_application_commands()


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.slash_command(description="Replies with pong!")
async def ping(interaction: Interaction):
    await interaction.send("Pong!", ephemeral=True)


@bot.slash_command(description="Reload extension")
async def reload_extension(interaction: Interaction, extension_name: str):
    if interaction.user.id not in ADMIN_USER_IDS:
        await interaction.send("You don't have the rights to use this command", ephemeral=True)
        return

    bot.reload_extension(f"extensions.{extension_name}")


def is_link(target: str) -> bool:
    if "https://" == target[:8]:
        return True
    else:
        return False


# EXTENSION SETUP
for extension in DEFAULT_EXTENSIONS:
    bot.load_extension(f"extensions.{extension}")
    print(f"Loaded extension: {extension}")

bot.run(BOT_TOKEN)
