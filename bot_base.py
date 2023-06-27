# DISCORD LIBS
from nextcord import Interaction
from nextcord.ext import commands

# OS TOOLS
import os
from dotenv import load_dotenv

# env vars
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GENIUS_API_KEY = os.getenv("GENIUS_API_KEY")

# other consts
DEFAULT_EXTENSIONS: list[str] = ["player", "utils"]
DEFAULT_GUILD_IDS: list[int] = [699726889085960235, 949113046939336744]
ADMIN_USER_IDS: list[int] = [509737193749741588]

bot = commands.Bot(default_guild_ids=DEFAULT_GUILD_IDS)

# TODO AUTO EXTENSION RELOADER

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


# EXTENSION SETUP
for extension in DEFAULT_EXTENSIONS:
    bot.load_extension(f"extensions.{extension}")

bot.run(BOT_TOKEN)
