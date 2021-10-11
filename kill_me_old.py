import discord
import time
import json
import threading
import atexit
import googletrans
from googletrans import Translator
import pprint
from threading import Timer
import youtube_dl
from youtubesearchpython import *
import os
import asyncio
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option

youtube_dl.utils.bug_reports_message = lambda: ''
tim = int(open("V:/bot/time.txt").read())

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options, executable=r"V:\ffmpeg\bin\ffmpeg.exe"), data=data)

tchan = 701758711407837214
vchan = 699726889559785590
translator = Translator()
langs = googletrans.LANGUAGES
client = discord.Client()
lang = json.loads(open("V:/bot/callsign.json", "r").read())[0].get("tolang")
callsign = json.loads(open("V:/bot/callsign.json", "r").read())[0].get("callsign")
last = json.loads(open("V:/bot/callsign.json", "r").read())[0].get("last")
fromlang = json.loads(open("V:/bot/callsign.json", "r").read())[0].get("fromlang")
#print(tim)
queue = []
vc = False
timer = False
token = False
loop = False
print(callsign)
print(type(callsign))
#opus.load_opus()

def switch(x):
    return {
        '1': 1,
        '2': 2,
    }[x]

def exfunc():
    print("stopped d")
    client.get_channel(tchan).send(":octagonal_sign: **Bot stopped**")
atexit.register(exfunc)

OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']

COMMANDS = {
    "help": "Show all commands",
    "lang [language code]": "Change language",
    "translate [text]": "Translate some text",
    "langlist": "List all languages",
    "callsign [new callsing]": "Change the callsign",
    "l": "Show current language",
    "diskprd": "do you are have stupid?",
    "reverse": "Reverse previous translation",
    "fak": "oof",
    "hello": "hello!",
    "kubus": "Tak já jdu na tebe"
}

FILES = {
    "1": "trubič",
    "2": "bordel",
    "3": "zahrádka",
    "4": "panel",
    "5": "okenajs"
}

slash = SlashCommand(client, sync_commands=True)
guild_ids = [699726889085960235]
bot = commands.Bot(command_prefix=callsign)

@bot.command()
async def _play(ctx, search):
    await ctx.send(search)

@slash.slash(name="ping", guild_ids=guild_ids, description="Ahaa jako zkus to co myslíš že to dělá asi")
async def _ping(ctx):
    await ctx.send(f"Pong! ({client.latency*1000}ms)")

@slash.slash(name="play", guild_ids=guild_ids, description="Přehraj ňákej jutub link", options=[create_option(name="playopt", description="link or search term", option_type=3, required=True)])
async def _play(ctx, playopt: str, vc=vc):
    mes = playopt
    res = VideosSearch(mes, limit=3).result()
    if mes.startswith("https://"):
        await ctx.send(f"Loading...```{mes}```")
        vidlink = mes
        print(vidlink)
        #await message.edit(content=f"{callsign}play <{vidlink}>")
        print("link in message")
        #video = json.loads(Video.get(vidlink, mode = ResultMode.json))
        #video = json.loads(Video.get("https://www.youtube.com/watch?v=goQtQb-U7OI", mode=ResultMode.json))
        #print(video)
        #title = video.get("title")
        title = "oof titel"
        #thumb = video.get("thumbnails")[4].get("url")
    else:
        await ctx.send(f"Loading...```{mes}```")
        vidlink = res.get("result")[0].get("link")
        print("found link")
        print(vidlink)
        title = res.get("result")[0].get("title")
        thumb = res.get("result")[0].get("thumbnails")[0].get("url")
    queue.append(vidlink)
    print(queue)
    await playqueue(ctx, vc)
    #embed=discord.Embed(title="**Now playing** :musical_note:", description=f"[**{title}**]({vidlink})", color=0xff0000)
    embed=discord.Embed(title="**Now playing** :musical_note:", description=f"[**Title**]({vidlink})", color=0xff0000)
    #print(thumb)
    #embed.set_image(url=thumb)
    #await ctx.send(embed=embed) 
    
    msg = await client.get_channel(tchan).history(limit=1).flatten()
    msg = msg[0]
    await msg.edit(content=f"Playing ```{title}```")

async def playqueue(ctx, vc):
    if len(queue) == 0:
        print("Queue is empty, quitting")
        return
    try:
        player = await YTDLSource.from_url(queue[0], stream=True)
    except Exception as e:
        print("player doesnt work")
        print(e)
    try:
        voicechannel = client.get_channel(vchan)
        vc = await voicechannel.connect()
    except Exception as e:
        print(e)
    try:
        if vc.is_paused():
            await ctx.send("Already playing audio, but playback is paused!")
            return
        elif vc.is_playing():
            print("Already playing, added to queue and waiting")
        else:
            print(queue)
            vc.play(player)
            del queue[0]
            #timer = RepeatTimer(1, addtime)
            #timer.start()
    except:
        await ctx.send("Error in player!")
        return
    print("Repeating playqueue in 5 Secs")
    await asyncio.sleep(5)
    await playqueue(ctx, vc)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    #await client.get_channel(tchan).send(":white_check_mark: **Bot started**")

async def hinzil(vc, sauce):
    print(vc)
    if vc == False:
        vc = await voicechannel.connect()
        print(vc)
    if vc.is_playing() == True: 
        vc.stop()
        # disafter()
    else:
        AudioSrc = discord.FFmpegPCMAudio(executable=r"C:\Users\paolo\OneDrive\Dokumenty\ffmpeg\bin\ffmpeg.exe", source=sauce)
        AudioSrcVol = discord.PCMVolumeTransformer(AudioSrc, 1.0)
        vc.play(AudioSrcVol)
        print("Opus:")
        print(AudioSrc.is_opus())
        while vc.is_playing():
            time.sleep(0.5)
        if loop == True:
            @client.event
            async def on_message(message):
                channel = client.get_channel(tchan)  
                voicechannel = client.get_channel(vchan)
                if (message.channel.id == tchan):
                    if message.content == "ok":
                        await channel.send("ne")
            await hinzil(vc, sauce)
        print("Setting vc to false...")
        await vc.disconnect()
        vc = False
        # print("ok")
        # disafter()

@client.event
async def on_message(message):
    global lang
    global callsign
    global last
    global fromlang
    global vc
    global timer
    global voicechannel
    global loop

    channel = client.get_channel(tchan)
    voicechannel = client.get_channel(vchan)

    if (message.channel.id == tchan):
        if message.author == client.user:
            if message.content.startswith("fak"):
                await message.add_reaction("<:oof:699767809533804565>")

        if message.content == (callsign + 'hello'):
            await message.channel.send('Hello!')

        if message.content == (callsign + "mov"):
            print(message.author)
            vc = await voicechannel.connect()

        if message.content.startswith (callsign + "play"):
            if message.content == (callsign + "play"):
                #pprint.pformat(FILES[curr], 0).replace("\'", "")
                await channel.send(pprint.pformat(FILES, 0).strip("{}").replace("\'", "").replace(",", ""))
            else:
                mes = message.content.replace(callsign + "play ", "")
                print(mes)
                if mes == "1":
                    await hinzil(False, r"V:\bot\ketef.mp3")
                elif mes == "2":
                    await hinzil(False, r"V:\bot\cirk.mp3")
                elif mes == "3":
                    await hinzil(False, r"V:\bot\buh.mp3")
                elif mes == "4":
                    await hinzil(False, r"V:\bot\cirk2.mp3")
                elif mes == "5":
                    await hinzil(False, r"V:\bot\okenajs.mp3")
                else:
                    #print("yout")
                    res = VideosSearch(mes, limit=3).result()
                    if mes.startswith("https://"):
                        vidlink = mes
                        #await message.edit(content=f"{callsign}play <{vidlink}>")
                        print("link in message")
                        video = json.loads(Video.get(vidlink, mode = ResultMode.json))
                        print(video)
                        title = video.get("title")
                        thumb = video.get("thumbnails")[4].get("url")
                    else:
                        vidlink = res.get("result")[0].get("link")
                        print("found link")
                        print(vidlink)
                        title = res.get("result")[0].get("title")
                        thumb = res.get("result")[0].get("thumbnails")[0].get("url")
                    try:
                        player = await YTDLSource.from_url(vidlink, stream=True)
                    except Exception as e:
                        print("player doesnt work")
                    try:
                        vc = await voicechannel.connect()
                    except Exception as e:
                        print("already connected to vc")
                        print(e)
                    try:
                        if vc.is_paused():
                            await channel.send("Already playing audio, but playback is paused!")
                            return
                        else:
                            vc.play(player)
                            print("test1")
                            timer = RepeatTimer(1, addtime)
                            timer.start()
                    except:
                        await channel.send("Already playing audio!")
                        return
                    embed=discord.Embed(title="**Now playing** :musical_note:", description=f"[**{title}**]({vidlink})", color=0xff0000)
                    #print(thumb)
                    embed.set_image(url=thumb)
                    await channel.send(embed=embed)
        if message.content == (callsign + "stop"):
            try:
                await channel.send("Stopping audio...")
                vc.stop()
            except:
                print("couldn't stop audio")
        if message.content == (callsign + "pause"):
            #print(vc.is_paused())
            try:
                if vc.is_paused():
                    await channel.send("Already paused!")
                elif vc.is_playing():
                    await channel.send("Pausing playback... :pause_button:")
                    vc.pause()
                else:
                    await channel.send("Nothing to pause!")
            except:
                print("couldn't stop audio")
                await channel.send("Nothing to pause!")

        if message.content == (callsign + "resume"):
            try:
                if vc.is_paused():
                    await channel.send("Resuming playback... :arrow_forward:")
                    vc.resume()
                else:
                    await channel.send("Playback isn't paused!")
            except:
                print("couldn't stop audio")
    
        
        if message.content.startswith (callsign + "здфя"):
            if message.content == (callsign + "здфя"):
                #pprint.pformat(FILES[curr], 0).replace("\'", "")
                await channel.send(pprint.pformat(FILES, 0).strip("{}").replace("\'", "").replace(",", ""))
            else:
                mes = message.content.replace(callsign + "здфя ", "")
                if mes == "1":
                    await hinzil(False, r"V:\bot\ketef.mp3")
                elif mes == "2":
                    await hinzil(False, r"V:\bot\cirk.mp3")
                elif mes == "3":
                    await hinzil(False, r"V:\bot\buh.mp3")
                elif mes == "4":
                    await hinzil(False, r"V:\bot\cirk2.mp3")
                elif mes == "5":
                    await hinzil(False, r"V:\bot\okenajs.mp3")
                elif mes == "yt":
                    print("yout")
                else:
                    await channel.send("Error: Pawel je denzil a neumí programovat")

        if message.content.startswith(callsign + "callsign"):
            callsign = [{ "callsign" : message.content.replace(callsign + "callsign ", ""), "tolang": lang, "last": last, "fromlang": fromlang}]
            print(callsign)
            open("V:/bot/callsign.json", "w").write(json.dumps(callsign))
            callsign = json.loads(open("V:/bot/callsign.json", "r").read())[0].get("callsign")
            await channel.send("Callsign changed to " + callsign)

        if message.content == (callsign + "w"):
            await channel.send(input("Write to channel: "))

        if message.content.startswith(callsign + 'translate'):
            if message.content == (callsign + "translate"):
                await channel.send("Tak to jsme si jako nedomluvili hele")
            else:
                # await channel.send("fuck")
                totrans = message.content.replace(callsign + "translate ", "")
                fromtrans = translator.translate(totrans, dest=lang)
                await channel.send("```\n" + fromtrans.text + "\n```")

                last = [{ "callsign": callsign, "tolang": lang, "last": fromtrans.text, "fromlang": fromlang}]
                open("V:/bot/callsign.json", "w").write(json.dumps(last))
                last = json.loads(open("V:/bot/callsign.json", "r").read())[0].get("last")

                fromlang = [{ "callsign": callsign, "tolang": lang, "last": last, "fromlang": fromtrans.src}]
                open("V:/bot/callsign.json", "w").write(json.dumps(fromlang))
                fromlang = json.loads(open("V:/bot/callsign.json", "r").read())[0].get("fromlang")

        if message.content == (callsign + "loop"):
            if loop == False:
                loop = True
                await channel.send("Loop enabled!")
            else:
                loop = False
                await channel.send("Loop disabled!")

        if message.content == (callsign + "reverse"):
            print(last)
            print(fromlang)
            await channel.send("```\n" + translator.translate(last, dest=fromlang, src=lang).text + "\n```")

            # def disafter():
            # global vc
            # global timer
            # global token
            # if token == True:
            #     if timer.is_alive() == True:
            #         time.sleep(1)
            #         disafter()
            # print("Status of play: ")
            # print(vc.is_playing())
            # if vc.is_playing() == True:
            #     timer = threading.Timer(3, disafter())
            #     timer.start()
            #     print("started timer")
            #     token = True
            # else:
            #     vc.disconnect()
            #     vc = False
            #     token = False

        if message.content == (callsign + "kubus"):
            print(vc)
            if vc == False:
                vc = await voicechannel.connect()
                print(vc)
            if vc.is_playing() == True: 
                vc.stop()
                # disafter()
            else:
                vc.play(discord.FFmpegPCMAudio(executable=r"C:\Users\paolo\OneDrive\Dokumenty\ffmpeg\bin\ffmpeg.exe", source=r"V:\bot\ketef.mp3"))
                while vc.is_playing():
                    time.sleep(3)
                print("Setting vc to false...")
                await vc.disconnect()
                vc = False
                # print("ok")
                # disafter()

        if message.content == (callsign + "langlist"):
            await channel.send(pprint.pformat(googletrans.LANGUAGES, 0).strip("{}").replace("\'", ""))

        if message.content == (callsign + "leave"):
            os._exit(1)

        elif message.content.startswith(callsign + 'lang'):
            if message.content == (callsign + 'lang'):
                await channel.send("Current output language is " + langs.get(lang))
            else:
                lang = [{ "callsign": callsign, "tolang": message.content.replace(callsign + "lang ", ""), "last": last, "fromlang": fromlang}]
                print(lang)
                open("V:/bot/callsign.json", "w").write(json.dumps(lang))
                lang = json.loads(open("V:/bot/callsign.json", "r").read())[0].get("tolang")
                await channel.send("Output language changed to " + langs.get(lang))

        elif message.content == (callsign + "l"):
            await channel.send("Current output language is " + langs.get(lang))

        if message.content.startswith(callsign + "help"):
            await channel.send(pprint.pformat(COMMANDS, 0).strip("{}").replace("\'", "").replace(",", ""))

        if message.content == (callsign + "override"):
            while True:
                command = input("Command: ")
                if command == "send":
                    await channel.send(input("Message: "))
                elif command == "vconnect":
                    try:
                        vc = await voicechannel.connect()
                    except:
                        print("Already connected!")
                elif command == "vdisconnect":
                    try:
                        await vc.disconnect()
                    except:
                        print("Not connected!")
                elif command == "exit":
                    print("Exiting...")
                    break

        if message.content.startswith(callsign + "diskprd"):
            await message.add_reaction("<:oof:699767809533804565>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:hammerandsickle:699739171652239360>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:aranzovacipena:701741295680356352>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:peeper:700104175928868938>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:chankadanka:701494999740842084>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:cocain:700041059396485160>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:gopnikface:699763462192234618>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:fuze:699761947234795521>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:kapkan:699760484534190213>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:youarefakenews:699754393334972457>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:no:699752901354192965>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:gimp:699752476022276110>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:Ubisoft:699752305133748324>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:tachanka:699751131819016222>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:bandit:699747471554904185>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:sad:699745835323359272>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:Angery:699744765721182240>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:glazstuck:699744273578590248>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:LordAdidas:699742016203915315>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:LordTriggered:699740981120991304>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:pulse:699740638287102002>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:fuzethehostage:699741767779614830>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:semo:699739900827926640>")
            time.sleep(1)
            await message.clear_reactions()
            await message.add_reaction("<:hammerandsickle:699739171652239360>")

@client.event
async def on_voice_state_update(member, before, after):
    channel = client.get_channel(tchan)
    voicechannel = client.get_channel(vchan)

    info = member, before, after
    #print(type(member))
    #await channel.send(info)
    onlymemb = str(member).split("[", 1)[0]
    #print(onlymemb)
    #print("member type start")
    #print(voicechannel.members[0])
    #print("member type end")
    
    for i in voicechannel.members:
        #print(i)
        #print(type(i))
        if str(i) == "placeholder naem":
            await i.move_to(client.get_channel(758401425062756353))
            #print("ok")
        else:
            #print("not ok")
            pass
    #maybe time.sleep(1) here? test if it disconnects async
    
client.run('NzAxNzQyMjUzNjc2NDI5MzEz.Xp18IA.Lkx8Pcb4HHMWJXiFWf2EZfJXR3M')
