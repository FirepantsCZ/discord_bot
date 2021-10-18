import discord
from discord.ext import commands
import time
import json
import threading
import atexit
import sched
import googletrans
import datetime
from googletrans import Translator
import pprint
from threading import Timer, Thread
import youtube_dl
from youtube_easy_api.easy_wrapper import *
from youtubesearchpython import *
import os
import asyncio
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
from pyyoutube import Api
from youtube_api import YouTubeDataAPI
import pafy #TODO: MAYBE TRY USING LESS THAN 30 YT APIs?

BOT_TOKEN = os.getenv("BOT_TOKEN")
print(BOT_TOKEN)
YT_API_KEY = os.getenv("YT_API_KEY")
print(YT_API_KEY)

easy_wrapper = YoutubeEasyWrapper()
api = Api(api_key=YT_API_KEY)
easy_wrapper.initialize(api_key=YT_API_KEY)
yt = YouTubeDataAPI(YT_API_KEY)
pafy.set_api_key(YT_API_KEY)

s = sched.scheduler(time.time, asyncio.sleep)

youtube_dl.utils.bug_reports_message = lambda: ''
tim = int(open("time.txt").read())

ytdl_format_options = {
    'age_limit': '30',
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': False,
    'cookiefile': r'cookies.txt',
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn -ss 0',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

print(pafy.new("https://www.youtube.com/watch?v=4bvLaYLD1HI", ydl_opts=ytdl_format_options).length) #Pafy test


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
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

tchan = 701758711407837214
vchan = 699726889559785590

#tchan and vchan are outdated, instead use ctx to get channels

translator = Translator()
langs = googletrans.LANGUAGES
client = discord.Client()
lang = json.loads(open("callsign.json", "r").read())[0].get("tolang")
callsign = json.loads(open("callsign.json", "r").read())[0].get("callsign")
last = json.loads(open("callsign.json", "r").read())[0].get("last")
fromlang = json.loads(open("callsign.json", "r").read())[0].get("fromlang")
playlists = json.loads(open("playlists.json", "r").read())
print(playlists[0])
print(playlists[1])
#print(tim)
queuelist = []  
vc = False
timer = False
stopflag = False
token = False
prev = ""
curtime = 0
curmin = 0
loopone = False
loopqueueflag = False
#print(callsign)
#print(type(callsign))
#opus.load_opus()

def switch(x):
    return {
        '1': 1,
        '2': 2,
    }[x]

def exfunc():
    print("stopped d")
    #client.get_channel(tchan).send(":octagonal_sign: **Bot stopped**")
    #tes
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

bot = commands.Bot(command_prefix=callsign)
slash = SlashCommand(bot, sync_commands=True)
guild_ids = [699726889085960235]
#print(callsign)

bot.remove_command("help")

###HELP COMMANDS###
@bot.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title="Help", description="Use $help <command> for extended info on a command.", color=0xff0000)
    em.add_field(name="Playback control", value="np,playlist,remove,queue,seek,fs,loop,play")
    await ctx.send(embed = em)

@help.command()
async def np(ctx):
    em = discord.Embed(title="Now playing", description="Shows info about the currently playing song", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$np`")

    await ctx.send(embed=em)

@help.command()
async def playlist(ctx):
    em = discord.Embed(title="Playlist", description="Adds a saved playlist to queue", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$playlist <playlist name>`")

    await ctx.send(embed=em)

@help.command()
async def remove(ctx):
    em = discord.Embed(title="Remove", description="Removes song from queue", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$remove <queue number>`")

    await ctx.send(embed=em)

@help.command()
async def queue(ctx):
    em = discord.Embed(title="Queue", description="Shows info about all queued songs", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$queue`")

    await ctx.send(embed=em)

@help.command()
async def seek(ctx):
    em = discord.Embed(title="Seek", description="Plays song from a certain time", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$seek <seconds>`")

    await ctx.send(embed=em)

@help.command()
async def fs(ctx):
    em = discord.Embed(title="Force skip", description="Skips currently playing song", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$fs`")

    await ctx.send(embed=em)

@help.command()
async def loop(ctx):
    em = discord.Embed(title="Loop", description="Toggles on loop for current song", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$loop`")

    await ctx.send(embed=em)

@help.command()
async def play(ctx):
    em = discord.Embed(title="Play", description="Plays a song", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$play <ULR or search>`")

    await ctx.send(embed=em)

###END HELP COMMANDS###


@bot.command()
async def np(ctx):
    #t = datetime.time(second=curtime, minute=curmin)
    vid_len = pafy.new(prev).length
    #vid_len = datetime.timedelta(seconds=pafy.new(prev).length)
    print(vid_len)
    #await ctx.send(f"```{t.minute}:{t.second:02d}```")
    try:
        if vc.is_playing():
            metadata = yt.get_video_metadata(prev.split('?v=')[1][:11])

            desc=""
            desc += f"[{metadata['video_title']}]({prev}) | `{format_time(curtime)} / {format_time(vid_len)}`"

            embed = discord.Embed(title="**Now playing** :musical_note:", description=desc, color=0xff0000)
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"Not playing anything")
    except Exception as e:
        print(e)
    await ctx.send(f"Not connected to VC")


@bot.command()
async def playlist(ctx, playlist_name):
    flg = False
    for i in playlists:
        if playlist_name == i.get("name"):
            print(f"got {playlist_name}")
            for j in i:
                if j != "name":
                    print(i.get(j))
                    queuelist.append(i.get(j))
            await ctx.send(f"Added playlist ```{playlist_name}```to queue")
            await playqueuelist(ctx)
        else:
            flg = True
    if flg:
        await ctx.send(f"Playlist ```{playlist_name}```not found")

def format_time(secs):
    formatted_time = time.strftime('%H:%M:%S', time.gmtime(secs))

    if int(str(formatted_time)[:2]) > 0:
        return formatted_time
    if int(str(formatted_time)[3]) == 0:
        return formatted_time[4:]
    else:
        return formatted_time[3:]

@bot.command()
async def remove(ctx, queue_index):
    global queuelist

    if len(queuelist) >= int(index):
        await ctx.send(f"Removed [{yt.get_video_metadata(video_id=queuelist[int(index)-1].split('?v=')[1][:11])['video_title']}]({queuelist[int(index)-1]})") #TODO: Optimise these lines to look a bit better
        del queuelist[int(index)-1]
    else:
        await ctx.send("Invalid queue position!")

@bot.command()
async def queue(ctx):
    nmlist = [] #I think nmlist here is probably the list of all names of songs in queue
    print(queuelist) #Queuelist should be the array of all queued links
    for i in queuelist:
        nmlist.append(yt.get_video_metadata(video_id=i.split("?v=")[1][:11])["video_title"])
    if len(nmlist) != 0: 
        txt = str(nmlist).replace('\'', '').strip('[]')
        #await ctx.send(f"```{txt}```")

        desc=""
        tot_time = 0

        desc += f"\n**Now playing:**\n[{yt.get_video_metadata(video_id=prev.split('?v=')[1][:11])['video_title']}]({prev}) | `{format_time(pafy.new(prev).length)}`\n\n⎯⎯⎯⎯⎯\n"

        for j in nmlist: #Add every song to queue embed
            indx = nmlist.index(j)

            vid_len = pafy.new(queuelist[indx]).length
            tot_time += vid_len
            dur = format_time(vid_len)

            desc += f"\n`{indx+1}.` [{j}]({queuelist[indx]}) | `{dur}`\n"

        desc += f"\n⎯⎯⎯⎯⎯\n\n**Total queue length**: `{format_time(tot_time)}`"

        embed = discord.Embed(title="**Queue** :musical_note:", description=desc, color=0xff0000)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Queue is empty")

@bot.command()
async def seek(ctx, pos): #TODO: Fix longer loading for longre skip times(0-10 instant, 60 takes long)
    global ffmpeg_options
    global queuelist
    global vc
    global curtime

    ffmpeg_options["options"] = f'-vn -ss {pos}'
    queuelist.insert(0, prev)
    try:
        vc.stop()
    except:
        await ctx.send("Error while seeking")
        del queuelist[0]
    if len(queuelist)-1 == 0:
        print("jumpstarting playqueuelist")
        await playqueuelist(ctx)
    else:
        print("playqueuelist should be looping")
    curtime = int(pos)

@bot.command()
async def fs(ctx):
    global vc
    vc.stop()

@bot.command()
async def loop(ctx):
    global loopone
    global queulist
    global prev

    loopone = not loopone

    if loopone:
        await ctx.send(f"loop enabled!")
        queuelist.insert(0, prev)
    else:
        await ctx.send(f"loop disabled!")
        if prev == queuelist[0]:
            del queuelist[0]

@bot.command()
async def loopqueue(ctx): #TODO: Add loopqueue function
    pass

@bot.command()
async def play(ctx, *, search):
    global vc

    if search.startswith("https://"):
        vidlink = search
        await ctx.send(f"Loading...```{search}```")
        #easy_wrapper.get_metadata(video_id)
        #metadata = easy_wrapper.get_metadata(video_id=search.split("?v=")[1][:11]) # this is also good
        metadata = yt.get_video_metadata(video_id=search.split("?v=")[1][:11])
    else:
        await ctx.send(f"Loading...```{search}```")
        vidlink = VideosSearch(search, limit=3).result().get("result")[0].get("link")
        #print(vidlink.split("?v=")[1][:11])
        #metadata = easy_wrapper.get_metadata(video_id=vidlink.split("?v=")[1][:11]) #this is the good one
        #metadata = easy_wrapper.get_metadata(video_id="T12ygsp9Mvg")
        metadata = yt.get_video_metadata(video_id=vidlink.split("?v=")[1][:11])
        #print(metadata)
    
    #title = "faking ok nebij me este to nefunguje nejlip jo ok"
    title = metadata["video_title"]
    thumb = metadata["video_thumbnail"]
    #print(metadata)
 
    """ msg = await ctx.history(limit=1).flatten()
    try:
        try:
            if len(queuelist) == 0 and not vc.playing():
                await msg[0].edit(content=f"Playing ```{title}```")
        except:
            await msg[0].edit(content=f"Playing ```{title}```")
        else:
            await msg[0].edit(content=f"Added to queue ```{title}```")
    except:
        print("can't edit message")
        await ctx.send(f"Added to queue ```{title}```") """
        
    queuelist.append(vidlink)
    #embed=discord.Embed(title="**Now playing** :musical_note:", description=f"[**{title}**]({vidlink})", color=0xff0000)
    #embed=discord.Embed(title="**Now playing** :musical_note:", description=f"[**Title**]({vidlink})", color=0xff0000)
    print(thumb)

    msg = await ctx.history(limit=1).flatten()
    try:
        if vc.is_playing():
            embed=discord.Embed(title="**Added to queue** :musical_note:", description=f"[**{title}**]({vidlink})", color=0xff0000)
        else:
            embed=discord.Embed(title="**Now playing** :musical_note:", description=f"[**{title}**]({vidlink})", color=0xff0000)
    except:
        embed=discord.Embed(title="**Now playing** :musical_note:", description=f"[**{title}**]({vidlink})", color=0xff0000)

    embed.set_image(url=thumb)
    await msg[0].edit(content="", embed=embed)
    #await ctx.send(embed=embed)
    await playqueuelist(ctx)

###EXPERIMENT TIME###
async def testinc(loop):
    while True:
        print("looping")
        await asyncio.sleep(1)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
asyncio.ensure_future(testinc(loop))
#loop.run_forever()

testth = Thread(target=loop.run_forever)
#testth.start()
###ACTUALLY WORKS TIME###

async def inctime(loop):
    while True:
        global curtime
        #print(f"{t.minute}:{t.second:02d}")

        curtime += 1

        #print(f"Stopflag is {stopflag}")
        if stopflag:
            print("stopping loop")
            loop.stop()

        await asyncio.sleep(1)

timeloop = asyncio.new_event_loop()
asyncio.set_event_loop(timeloop)
asyncio.ensure_future(inctime(timeloop))

###SLASH IS OLD, DONT USE
@slash.slash(name="ping", guild_ids=guild_ids, description="Ahaa jako zkus to co myslíš že to dělá asi")
async def _ping(ctx):
    await ctx.send(f"Pong! ({client.latency*1000}ms)")

@slash.slash(name="play", guild_ids=guild_ids, description="Přehraj ňákej jutub link", options=[create_option(name="playopt", description="link or search term", option_type=3, required=True)])
async def _play(ctx, playopt: str, vc=vc):
    mes = playopt
    res = VideosSearch(mes, limit=3).result()
    if mes.startswith("https://"):
        await ctx.send(f"Loading...```{mes}```")
        print("SHITE")
        vidlink = mes
        print(vidlink)

    else:
        await ctx.send(f"Loading...```{mes}```")
        print("SHITE")
        vidlink = res.get("result")[0].get("link")
        print(vidlink)

    queuelist.append(vidlink)
    await playqueuelist(ctx)
    #embed=discord.Embed(title="**Now playing** :musical_note:", description=f"[**{title}**]({vidlink})", color=0xff0000)
    embed=discord.Embed(title="**Now playing** :musical_note:", description=f"[**Title**]({vidlink})", color=0xff0000)
    #print(thumb)
    #embed.set_image(url=thumb)
    #await ctx.send(embed=embed) 
    
    msg = await client.get_channel(tchan).history(limit=1).flatten()
    msg = msg[0]
    await msg.edit(content=f"Playing ```{title}```")

async def playqueuelist(ctx):
    global vc
    global prev
    global curtime
    global curmin
    global stopflag

    #print("Checking for stopped player")

    if len(queuelist) == 0:
        print("queuelist is empty, quitting")
        return
    try:
        player = await YTDLSource.from_url(queuelist[0], stream=True)
    except Exception as e:
        print("player doesnt work")
        print(e)
    try:
        vc_list = ctx.guild.voice_channels
        #print(f"connecting to {vc_list[0]}")
        #voicechannel = bot.get_channel(vchan)
        vc = await vc_list[0].connect()
        print(f"connected to {vc}")
    except Exception as e:
        #print(e) #ususally "already connected to VC"
        pass
    try:
        if vc.is_paused():
            await ctx.send("You shouldn't ever see this message")
            print("WTF did you do")
            return
        elif vc.is_playing():
            #print("Already playing, added to queuelist and waiting")
            pass
        else:
            print("Nothing playing, going to next song...")
            stopflag = True
            await asyncio.sleep(1) #Set to 2 to be safe, 1 seems to work
            pt = Thread(target=vc.play, args=(player,)) #Try starting player on different thread?
            pt.start()
            #vc.play(player) #TODO: FIX STUTTERING AND SKIPPING ISSUE (holy shit maybe threading actually works)
            if not loopone and not loopqueueflag:
                prev = queuelist[0]
                del queuelist[0]
                print(f"prev {prev}")
            curtime = 0
            print("starting timer")
            stopflag = False
            #await inctime() #Maybe try to multithread the inctime? idk anymore shit's hard
            #t = Thread(target=asyncio.run, args=(inctime(),)) #Old inctime, reaches recursion limit
            t = Thread(target=timeloop.run_forever)
            t.start()
            print("after inctime")
            #timer.cancel()

    except Exception as e:
        await ctx.send("Error in player!")
        print(e)
    await asyncio.sleep(1) #1 Sec is experimental, for stability use 5 secs
    await playqueuelist(ctx)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
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
        if loopone == True:
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
    
bot.run(BOT_TOKEN)
