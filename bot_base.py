# DISCORD LIBS
from nextcord import Interaction
from nextcord.ext import commands

# OS TOOLS
import os
from dotenv import load_dotenv
from threading import Thread, Event

# env vars
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GENIUS_API_KEY = os.getenv("GENIUS_API_KEY")

# other consts
DEFAULT_EXTENSIONS: list[str] = ["player", "utils"]
DEFAULT_GUILD_IDS: list[int] = [699726889085960235, 949113046939336744, 1118954839146242260]
ADMIN_USER_IDS: list[int] = [509737193749741588]

bot = commands.Bot(default_guild_ids=DEFAULT_GUILD_IDS)

# TODO FIX AUTO EXTENSION RELOADER
# TODO add proper cleanup after bot finish (remove hanging messages etc.)

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


def hotreaload_extensions(event: Event) -> None:
    changes = {extension_file: os.path.getmtime(f"extensions/{extension_file}.py") for extension_file in
                   DEFAULT_EXTENSIONS}

    while not event.is_set():
        for name, time_changed in changes.items():
            if time_changed < os.path.getmtime(f"extensions/{name}.py"):
                print(f"extension {name} modified, reloading...")
                bot.reload_extension(f"extensions.{name}")
                changes[name] = os.path.getmtime(f"extensions/{name}.py")


outer_event = Event()
hotreaload_thread = Thread(target=hotreaload_extensions, args=(outer_event,))
hotreaload_thread.start()

bot.run(BOT_TOKEN)
