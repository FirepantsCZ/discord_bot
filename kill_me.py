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
#from youtube_easy_api.easy_wrapper import *
from youtubesearchpython import *
import os
import asyncio
from lyricsgenius import Genius
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
#from pyyoutube import Api
from youtube_api import YouTubeDataAPI
import pafy #TODO: MAYBE TRY USING LESS THAN 30 YT APIs? Try to maybe change all APIs to pytube

###IDEAS###
#
#Use datetime.now() difference instead of your own timer dumbass
#
###########


BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"Bot token: {BOT_TOKEN}")
YT_API_KEY = os.getenv("YT_API_KEY")
print(f"Youtube API key: {YT_API_KEY}")
GENIUS_API_KEY = os.getenv("GENIUS_API_KEY")
print(f"Genius API key: {GENIUS_API_KEY}")


#easy_wrapper = YoutubeEasyWrapper()
#api = Api(api_key=YT_API_KEY)
#easy_wrapper.initialize(api_key=YT_API_KEY)
yt = YouTubeDataAPI(YT_API_KEY)
pafy.set_api_key(YT_API_KEY)
genius = Genius(GENIUS_API_KEY)

s = sched.scheduler(time.time, asyncio.sleep)

youtube_dl.utils.bug_reports_message = lambda: ''
#tim = int(open("time.txt").read())

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
    'options': '-vn',
    "before_options": "-ss 0 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

assert pafy.new("https://www.youtube.com/watch?v=4bvLaYLD1HI", ydl_opts=ytdl_format_options).length != 0 #Sanity check
#print(genius.search_song("I wanna be your slave", "Maneskin").lyrics)

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

#translator = Translator()
#langs = googletrans.LANGUAGES
#client = discord.Client()
#lang = json.loads(open("callsign.json", "r").read())[0].get("tolang")
callsign = json.loads(open("callsign.json", "r").read())[0].get("callsign")
#last = json.loads(open("callsign.json", "r").read())[0].get("last")
#fromlang = json.loads(open("callsign.json", "r").read())[0].get("fromlang")
playlists = json.loads(open("playlists.json", "r").read())
print(f"Loaded {len(playlists)} playlists")
#print(tim)
queuelist = []
vc = False
stopflag = False
prev = ""
curtime = 0
local_audio = False
loopone = False
loopqueueflag = False
#print(callsign)
#print(type(callsign))
#opus.load_opus()

""" def exfunc():
    print("stopped d")
    #client.get_channel(tchan).send(":octagonal_sign: **Bot stopped**")
    #tes
atexit.register(exfunc) """

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
    em.add_field(name="Playback control", value="`np`, `playlist`, `remove`, `queue`, `seek`, `fs`, `loop`, `play`, `pause`")
    await ctx.send(embed = em)

@help.command()
async def np(ctx):
    em = discord.Embed(title="Now playing", description="Shows info about the currently playing song", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$np`")

    await ctx.send(embed=em)

@help.command()
async def playlist(ctx):
    em = discord.Embed(title="Playlist", description="Playlist operations", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$playlist <action> [playlist name]`")
    em.add_field(name="**Actions**", value="`create`, `remove`, `play`, `list`")

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
    em = discord.Embed(title="Seek", description="Plays song from a certain time (still a bit buggy, use at own risk)", color=0xff0000)

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

@help.command()
async def pause(ctx):
    em = discord.Embed(title="Pause", description="Toggles pause and resume", color=0xff0000)

    em.add_field(name="**Syntax**", value="`$pause`")

    await ctx.send(embed=em)

###BOT COMMANDS###

@bot.command()
async def np(ctx):
    #t = datetime.time(second=curtime, minute=curmin)
    vid_len = pafy.new(prev).length
    #vid_len = datetime.timedelta(seconds=pafy.new(prev).length)
    #print(vid_len)
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
async def playlist(ctx, action, playlist_name=""): #TODO: Add listing every playlist, and list every playlist's individual songs like queue
    global playlists

    if (action == "play" or action == "Play") and playlist_name != "":
        #Add playlist to queue
        flg = False
        for i in playlists:
            if playlist_name == i.get("name"):
                print(f"got {playlist_name}")
                for j in i:
                    if j != "name":
                        print(i.get(j))
                        queuelist.append(i.get(j))
                em = discord.Embed(title="Playing :musical_note:", description=f"Adding playlist `{playlist_name}` to queue", color=0xff0000)
                await ctx.send(embed=em)
                await playqueuelist(ctx) #TODO: FIX: WHEN SEEKING A SONG WITH SONGS IN QUEUE AFTER IT, IT GETS SKIPPED SOMETIMES
            else:
                flg = True
        if flg:
            em = discord.Embed(title="Error :octagonal_sign:", description=f"Playlist `{playlist_name}` not found", color=0xff0000)
            await ctx.send(embed=em)
            flg = False
    elif (action == "remove" or action == "Remove") and playlist_name != "":
        #Remove named playlist
        flg = False
        for playlist in playlists:
            print(playlist.get("name")) #playlist here is a dict of songs, so use .get(key) instad of [index]
            if playlist.get("name") == playlist_name:
                del playlists[playlists.index(playlist)]
                print(playlists)
                open("playlists.json", "w").write(json.dumps(playlists))
                em = discord.Embed(title="Success :white_check_mark:", description=f"Succesfuly deleted playlist `{playlist_name}`", color=0xff0000)
                await ctx.send(embed=em)
                return
            else:
                flg = True
        if flg:
            print("flag was true, didnt find")
            em = discord.Embed(title="Error :octagonal_sign:", description=f"No playlist with name `{playlist_name}`", color=0xff0000)
            await ctx.send(embed=em)
            flg = False
    elif (action == "create" or action == "Create") and playlist_name != "":
        #Create a new playlist from queue, including the currently playing song
        try:
            if vc.is_paused() or vc.is_playing():
                playlist = {"name":playlist_name}
                playlist["0"] = prev
                for song in queuelist:
                    playlist[queuelist.index(song)+1] = song
                #print(playlist)
                playlists.append(playlist)
                #print(playlists)
                open("playlists.json", "w").write(json.dumps(playlists))
                em = discord.Embed(title="Success :white_check_mark:", description=f"Succesfuly created playlist `{playlist_name}`", color=0xff0000)
                await ctx.send(embed=em)
            else:
                em = discord.Embed(title="Error :octagonal_sign:", description="Not currently playing anything", color=0xff0000)
                await ctx.send(embed=em)
        except Exception as e:
            print(e)
            em = discord.Embed(title="Error :octagonal_sign:", description="Not connected to any VC", color=0xff0000)
            await ctx.send(embed=em)

    elif action == "list" or action == "List":
        #List all playlists, or individual playlist songs
        if playlist_name == "":
            desc = ""
            for playlist in playlists: #Add every playlist to embed
                index = playlists.index(playlist)

                desc += f"\n`{index+1}.` {playlist.get('name')} | `{len(playlist)-1}` songs\n"

            #desc += f"\n⎯⎯⎯⎯⎯\n\n**Total queue length**: `{format_time(tot_time)}`"

            em = discord.Embed(title="Playlists", description=desc, color=0xff0000)
            await ctx.send(embed=em)
        else:
            flg = False
            for playlist in playlists:
                #print(playlist.get("name")) #playlist here is a dict of songs, so use .get(key) instad of [index]
                if playlist.get("name") == playlist_name:
                    desc = ""
                    index = 1
                    #print(playlist)
                    for song in playlist:
                        #print(song)
                        if song != "name":
                            song = playlist.get(song)
                            desc += f"\n`{index}.` [{get_title(song)}]({song}) | `{format_time(pafy.new(song).length)}` \n"
                            index += 1
                    em = discord.Embed(title=f"Songs in `{playlist_name}`", description=desc, color=0xff0000)
                    await ctx.send(embed=em)
                    return
                else:
                    flg = True
            if flg:
                print("flag was true, didnt find")
                em = discord.Embed(title="Error :octagonal_sign:", description=f"No playlist with name `{playlist_name}`", color=0xff0000)
                await ctx.send(embed=em)
                flg = False
    else:
        em = discord.Embed(title="Error :octagonal_sign:", description="Invalid syntax, refer to $help list", color=0xff0000)
        await ctx.send(embed=em)

@bot.command()
async def lyrics(ctx, song, artist):
    if song and artist:
        result = genius.search_song(song, artist)
        if result:
            em = discord.Embed(title=f"{result.title} by {result.artist}", description=f"```{result.lyrics}```", color=0xff0000)
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Error :octagonal_sign:", description="Song not found")
            await ctx.send(embed=em)    


@bot.command()
async def remove(ctx, queue_index):
    global queuelist

    if len(queuelist) >= int(queue_index):
        await ctx.send(f"Removed [{yt.get_video_metadata(video_id=queuelist[int(queue_index)-1].split('?v=')[1][:11])['video_title']}]({queuelist[int(queue_index)-1]})") #TODO: Optimise these lines to look a bit better
        del queuelist[int(queue_index)-1]
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
async def seek(ctx, pos): #TODO: Speedup is almost fixed, maybe possible to get time down even more, AGAIN FIX FUCKING SEEKING SKIPPING SONGS
    global ffmpeg_options
    global queuelist
    global vc
    global curtime

    try:
        if vc.is_paused():
            em = discord.Embed(title="Error :octagonal_sign:", description="Cannot seek while player is paused", color=0xff0000)
            await ctx.send(embed=em)
            return
    except:
        em = discord.Embed(title="Error :octagonal_sign:", description="Not connected to any VC", color=0xff0000)
        await ctx.send(embed=em)
        return

    pos = time_to_seconds(pos)

    ffmpeg_options["before_options"] = f"-ss {pos} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5" #Changed from after options to before options, ffmpeg wiki "seeking"
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

    try:
        print("cycling playback")
        vc.pause()
        await asyncio.sleep(1.5) #Possibly could go lower, needs more experimenting
        vc.resume()
    except:
        print("Couldn't cycle")

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
async def pause(ctx):
    global stopflag

    try:
        if vc.is_paused():
            #print("Threads before:")
            #for thread in threading.enumerate(): 
                #print(thread.name)
            stopflag = False
            timeloop = asyncio.new_event_loop()
            asyncio.set_event_loop(timeloop)
            asyncio.ensure_future(inctime(timeloop))
            t = Thread(target=timeloop.run_forever)
            t.start()
            print("started thread")

            vc.resume()
            em = discord.Embed(title="Resumed :arrow_forward:", description=f"[{get_title(prev)}]({prev}) | `{format_time(curtime)} / {format_time(pafy.new(prev).length)}`", color=0xff0000)
            await ctx.send(embed=em)
        else:
            vc.pause()

            stopflag = True

            em = discord.Embed(title="Paused :pause_button:", description=f"[{get_title(prev)}]({prev}) | `{format_time(curtime)} / {format_time(pafy.new(prev).length)}`", color=0xff0000)
            await ctx.send(embed=em)

    except:
        await ctx.send("Not connected to VC")

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

###UTILITY FUNCTIONS###
def time_to_seconds(foramtted_time):
    if foramtted_time.count(":") == 0:
        return foramtted_time
    elif foramtted_time.count(":") == 1:
        return int(datetime.timedelta(minutes=int(foramtted_time.split(":")[0]), seconds=int(foramtted_time.split(":")[1])).total_seconds())
    elif foramtted_time.count(":") == 2:
        return int(datetime.timedelta(hours=int(foramtted_time.split(":")[0]), minutes=int(foramtted_time.split(":")[1]), seconds=int(foramtted_time.split(":")[2])).total_seconds())
    else:
        raise ValueError("Invalid time format")



def get_title(url):
    return yt.get_video_metadata(video_id=url.split("?v=")[1][:11])["video_title"]

def format_time(secs):
    formatted_time = time.strftime('%H:%M:%S', time.gmtime(secs))

    if int(str(formatted_time)[:2]) > 0:
        return formatted_time
    if int(str(formatted_time)[3]) == 0:
        return formatted_time[4:]
    else:
        return formatted_time[3:]

async def inctime(loop):
    while True:
        global curtime
        #print(f"{t.minute}:{t.second:02d}")

        curtime += 1
        #print(curtime)

        #print(f"Stopflag is {stopflag}")
        if stopflag:
            print("stopping loop")
            loop.stop()
            break

        await asyncio.sleep(1)

timeloop = asyncio.new_event_loop()
asyncio.set_event_loop(timeloop)
asyncio.ensure_future(inctime(timeloop))

t = Thread(target=timeloop.run_forever)
t.start()

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
            print("Player is paused, returning")
            return
        elif vc.is_playing():
            #print("Already playing, added to queuelist and waiting")
            pass
        else:
            print("Nothing playing, going to next song...")
            await asyncio.sleep(0.5) #Set to 2 to be safe, 1 seems to work, IF IT DOESN'T WORK, TURN BACK ON
            pt = Thread(target=vc.play, args=(player,)) #Try starting player on different thread?
            pt.start()
            ffmpeg_options["before_options"] = f"-ss 0 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5" #Set start position to 0
            #vc.play(player) #TODO: FIX STUTTERING AND SKIPPING ISSUE (holy shit maybe threading actually works)
            if not loopone and not loopqueueflag:
                prev = queuelist[0]
                del queuelist[0]
            curtime = 0
            print("restarting timer")
            #await inctime() #Maybe try to multithread the inctime? idk anymore shit's hard
            #t = Thread(target=asyncio.run, args=(inctime(),)) #Old inctime, reaches recursion limit

            #t = Thread(target=timeloop.run_forever) #these 2 lines work
            #t.start()
            
            #timer.cancel()

    except Exception as e:
        await ctx.send("Error in player!")
        print(e)
    await asyncio.sleep(1) #1 Sec is experimental, for stability use 5 secs
    await playqueuelist(ctx)


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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.change_presence(status=discord.Status.invisible)
    #await client.get_channel(tchan).send(":white_check_mark: **Bot started**")

@bot.event
async def on_voice_state_update(member, before, after):

    info = member, before, after
    onlymemb = str(member).split("[", 1)[0]
    print(onlymemb)

bot.run(BOT_TOKEN)
