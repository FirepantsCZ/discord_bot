import asyncio
import os

import nextcord
from nextcord import VoiceClient, Interaction, SlashOption, FFmpegOpusAudio, Message
from nextcord.ext import commands
from nextcord.ext.commands.bot import Bot
from yt_dlp import YoutubeDL

from bot_menus import ControlMenu, VideoSelectMenu

from bot_base import DEFAULT_GUILD_IDS


class Player(commands.Cog):
    def __init__(self, bot_client: Bot):
        self.bot = bot_client
        self.control_menu: ControlMenu | None = None

    @nextcord.slash_command(description="Seek to a specific time in the playing video", guild_ids=DEFAULT_GUILD_IDS)
    async def seek(self, interaction: Interaction, time: str = SlashOption(
        name="time",
        description="Time to seek to [hh:mm:ss]"
    )):
        voice_client: VoiceClient | None = self.bot.voice_clients[0] if len(self.bot.voice_clients) else None

        if not voice_client:
            await interaction.send("Not playing anything!", ephemeral=True)
            return

        await interaction.send(f"seeking to `{time}`", ephemeral=True)

        # TODO maybe convert/check user input time

        # tell video select menu we are seeking
        # stop player and restart it at desired position
        self.control_menu.seeking = True
        voice_client.stop()

        # TODO investigate speedup/stuttering issue
        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": f"-ss {time} -vn -bufsize 1k"  # bufsize may not do anything here, but it shouldn't hurt
        }
        opus_source = FFmpegOpusAudio(self.control_menu.video_url, **ffmpeg_options)
        voice_client.play(opus_source, after=self.control_menu.handle_after)

    @nextcord.slash_command(description="Play something from YouTube", guild_ids=DEFAULT_GUILD_IDS)
    async def play(self, interaction: Interaction, query: str = SlashOption(
        name="query",
        description="YouTube search or link",
        required=True
    )):
        await interaction.response.defer()

        if not is_link(query):
            remove_message = await run_once(interaction.delete_original_message)

            video_menus = []
            for video in search_youtube(query, 3):
                video_info = get_video_info(video["url"])
                menu = VideoSelectMenu(video_info)
                video_menus.append(menu)
                await menu.start(interaction=interaction)
                await remove_message()

            # could probably be done better without delay, maybe some event listener??
            # TODO redo without delays
            while not any([menu.is_finished() for menu in video_menus]):
                await asyncio.sleep(1)

            # await interaction.delete_original_message()

            # at this point one menu has finished
            # stop all other menus
            # transfer playing info from first menu
            video = None
            for menu in video_menus:
                menu.stop()
                if menu.selected:
                    video = menu.video
        else:
            video = get_video_info(query)

        if not interaction.user.voice:
            await interaction.followup.send("Not in any voice channel", ephemeral=True)
            return

        # at this point a video is picked

        voice_channel = interaction.user.voice.channel
        voice_client = await voice_channel.connect()

        # now all menus are finalized and deleted
        # make player controls
        self.control_menu = ControlMenu(video, voice_client)

        # bot.add_view(control_menu)
        await self.control_menu.start(interaction=interaction)
        print(f"persistence: {self.control_menu.is_persistent()}")

    @nextcord.message_command(name="Play on YouTube")
    async def play_from_message(self, interaction: Interaction, message: Message):
        await self.play(interaction, message.content)


# HELPER FUNCTIONS
YTDLP_ARGS = {
    "format": "ba",
    "noplaylist": True,
    "extractor_args": {
        "youtube": {
            "skip": ["dash", "hls", "translated_subs"],
            "player_client": ["android"]
        }
    }
}


def search_youtube(query: str, limit: int):
    with YoutubeDL(YTDLP_ARGS) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False, process=False)["entries"]
        return info


def get_video_info(url):
    with YoutubeDL(YTDLP_ARGS) as ydl:
        result = ydl.extract_info(url, download=False)
        return result


def is_link(target: str) -> bool:
    if "https://" == target[:8]:
        return True
    else:
        return False


async def run_once(f):
    async def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return await f(*args, **kwargs)
    wrapper.has_run = False
    return wrapper


# SETUP EXTENSION
def setup(bot: Bot):
    bot.add_cog(Player(bot))
    print(f"Loaded extension: {os.path.basename(__file__)[:-3]}")
