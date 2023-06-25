import datetime
import os.path

import nextcord
from nextcord import Embed, Colour, FFmpegOpusAudio, ClientException, VoiceClient, Message, Interaction, VoiceChannel
from nextcord.ui.button import Button, ButtonStyle
from nextcord.ext import menus

from datetime import timedelta, datetime

import threading
import asyncio

from yt_dlp import YoutubeDL

# TODO: possibly add pages?


class VideoSelectMenu(menus.ButtonMenu):
    def __init__(self, video: dict):
        self.preview_shown = False

        self.video = video
        self.start_time = None
        # self.voice_client: VoiceClient | None = None
        self.selected = False
        self.seeking = False
        self.video_url: str = ""
        self.voice_channel: VoiceChannel | None = None

        super().__init__(disable_buttons_after=True, delete_message_after=True)
        self.add_item(Button(label="Open", url=self.video["webpage_url"]))

    async def send_initial_message(self, ctx, channel):
        # could use interaction.followup.send() to show as responding to command
        # channel.send() cannot be ephemeral
        message = await self.interaction.channel.send(embed=Embed(
                colour=Colour.red(),
                title=self.video["title"],
                url=self.video["webpage_url"],
                #description=time(second=duration.get("seconds"), minute=duration.get("minutes") or 0, hour=duration.get("hours") or 0).strftime("%H:%M:%S")
                description=str(timedelta(seconds=int(self.video["duration"])))
            )
            .set_author(name=self.video["channel"], url=self.video["channel_url"], icon_url="")
            .set_thumbnail(self.video["thumbnail"]),
            view=self)
        return message

    @nextcord.ui.button(label="Play", style=ButtonStyle.primary, emoji="🎵")
    async def on_play(self, button, interaction: Interaction):
        self.selected = True
        await interaction.response.defer()

        self.stop()

    @nextcord.ui.button(label="Add to queue")
    async def on_preview_toggle(self, button, interaction):
        await interaction.response.edit_message(view=self)

    async def finalize(self, timed_out: bool):
        print("finalizing menu")
        # await self.interaction.delete_original_message()
        print(f"menu {self} finalized successfully")


class ControlMenu(menus.ButtonMenu):
    def __init__(self, video: dict, voice_client: VoiceClient):

        self.voice_client: VoiceClient = voice_client
        self.video: dict = video
        self.seeking: bool = False
        self.elapsed: datetime.timedelta | None = None

        # print(f"playing {self.video['webpage_url']}")
        # await interaction.send("Loading video...")

        ydl_options = {"outtmpl": "./ydl_out/out", "overwrites": True, "format": "ba", "nopart": True}

        # with YoutubeDL(ydl_options) as ydl:
        # download_thread = threading.Thread(target=ydl.download, args=(self.video["webpage_url"],))
        # download_thread.start()"""

        """await asyncio.sleep(3)  # delay to let file start downloading
        while not os.path.exists("ydl_out/out"):
            await asyncio.sleep(1)"""

        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -bufsize 1k"
        }
        best_quality = -1
        for i in self.video["formats"]:
            print(f"ext: {i.get('audio_ext')}, quality {i.get('quality')}")
            if i.get("audio_ext") != "none" and int(i.get("quality")) > best_quality:
                self.video_url = i["url"]
                best_quality = i["quality"]

        print(f"quality: {best_quality}")
        print(f"url: {self.video_url}")
        opus_source = FFmpegOpusAudio(self.video_url, **ffmpeg_options)

        self.voice_client.play(opus_source, after=self.handle_after)
        self.start_time: datetime.datetime = datetime.now()

        super().__init__(disable_buttons_after=True, delete_message_after=True, timeout=None)

    # maybe moving the start time isn't the best approach here, but it works for now
    async def increment_timer(self, message: Message):
        last_edit = datetime.now()
        while self.voice_client.is_connected():
            if self.voice_client.is_paused():
                self.start_time = -self.elapsed+datetime.now()
            else:
                self.elapsed = datetime.now() - self.start_time
                new_embed = message.embeds[0]
                new_embed.description = f"{str(self.elapsed).split('.')[0]}/{str(timedelta(seconds=int(self.video['duration'])))}"
                if datetime.now()-last_edit > timedelta(seconds=1):
                    await message.edit(embed=new_embed)
                    last_edit = datetime.now()

            await asyncio.sleep(0.5)
        self.stop()

    async def handle_after(self, error):
        if self.seeking:
            print("seeking, don't disconnect, resetting seeking")
            self.seeking = False
        else:
            await self.voice_client.disconnect()

    async def send_initial_message(self, ctx, channel):
        message = await self.interaction.channel.send(content="Now playing 🎵", embed=Embed(
            colour=Colour.red(),
            title=self.video["title"],
            url=self.video["webpage_url"],
            description=f"{str(self.elapsed)}/{str(timedelta(seconds=int(self.video['duration'])))}"
        )
        .set_author(name=self.video["channel"], url=self.video["channel_url"], icon_url="")
        .set_thumbnail(self.video["thumbnail"])
        ,
        view=self)
        asyncio.create_task(self.increment_timer(message))
        return message

    @nextcord.ui.button(label="Pause", style=ButtonStyle.primary, emoji="⏸")
    async def on_play_pause(self, button: Button, interaction):
        if self.voice_client.is_paused():
            button.label = "Pause"
            button.emoji = "⏸"
            button.style = ButtonStyle.primary
            self.voice_client.resume()
        else:
            button.label = "Play"
            button.emoji = "▶"
            button.style = ButtonStyle.green
            self.voice_client.pause()

        await interaction.response.edit_message(view=self)

    @nextcord.ui.button(label="Stop", style=ButtonStyle.red, emoji="⏹")
    async def on_audio_stop(self, button: Button, interaction):
        self.voice_client.stop()
        self.stop()

    async def finalize(self, timed_out: bool):
        print("finalizing menu")
        await self.interaction.delete_original_message()
        await self.message.delete()
        print(f"menu {self} finalized successfully")
