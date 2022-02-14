import os
import discord
from discord.utils import get
from dotenv import load_dotenv
from discord.ext import commands
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError


client = commands.Bot(command_prefix='!')

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# ----

queues = {}

# Checks if anything is in queue
def check_queue(ctx,id):
    if queues[id] != []:
        voice = ctx.guild.voice_client
        source = queues[id].pop(0)
        player = voice.play(source)

# Displays bot status
@client.event
async def on_ready():
    print("Loudbeats has arrived!")
    print("----------------------")

# Bot joins voice channel
@client.command(pass_context=True)
async def join(ctx):

    channel = ctx.author.voice.channel

    if ctx.author.voice is None:
        await ctx.send("Voice channel is empty! 😔")
    if ctx.voice_client is None:
        await channel.connect()
    else:
        await ctx.voice_client.move_to(channel)
        print("Joined channel")

# Bot leaves voice channel
@client.command(pass_context=True)
async def leave(ctx):
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        print("Left channel")
    else:
        await ctx.send("I'm not in a voice channel! 🤔")

# Pauses audio
@client.command(pass_content=True)
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        await ctx.send("Paused! ⏸")
        print("Paused")
    else:
        await ctx.send("There's nothing playing right now! 🤔")

# Stops playback and clears queue 
@client.command(pass_content=True)
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    queues.clear()
    voice.stop()
    await ctx.send("Stopped! ⏹")
    await ctx.guild.voice_client.disconnect()
    print("Stopped and queue cleared")

# Resumes audio if paused
@client.command(pass_content=True)
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
        await ctx.send("Resumed! ⏯")
        print("Resumed")
    else:
        await ctx.send("There's nothing paused right now! 🤔")

# Skips current song
@client.command(pass_content=True)
async def skip(ctx):
    id = ctx.message.guild.id
    voice = ctx.guild.voice_client
    if queues[id] != []:
        voice.stop()
        source = queues[id].pop(0)
        player = voice.play(source)
        await ctx.send("Skipped! ⏭️")
        print("Skipped, queue not empty")
    else:
        voice.stop()
        source = queues[id]
        player = voice.play(source)
        await ctx.send("Skipped! ⏭️")
        print("Skipped, queue empty") 


# Bot plays song
@client.command(pass_context=True)
async def play(ctx,*,url):
    
    # Joins voice channel
        if ctx.author.voice is None:
            await ctx.send("Hold up, the voice channel is empty! 😔")
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
        ctx.voice_client.stop()
        
    # Audio and search options
        FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        YDL_OPTS = {'format': 'bestaudio/best','noplaylist':'True', 'outtml': 'song.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192' }],'default_search':'auto'}
        voice = get(client.voice_clients, guild=ctx.guild)

        # If using search
        try:
            if not voice.is_playing():
                with YoutubeDL(YDL_OPTS) as ydl:
                    info = ydl.extract_info(url, download=False)['entries'][0]
                await ctx.send(f"Now playing! 🎉\n{info.get('webpage_url')}\n")
                URL = info['formats'][0]['url']
                source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                player = voice.play(source, after=lambda x=None: check_queue(ctx, ctx.message.guild.id))
                voice.is_playing()
            else:
                await ctx.send("Already playing song")
                return
        
        #If using URL
        except KeyError:
            if not voice.is_playing():
                with YoutubeDL(YDL_OPTS) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['formats'][0]['url']
                source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                player = voice.play(source)
                voice.is_playing()
            else:
                await ctx.send("Already playing song")
                return
        except IndexError:
                await ctx.send("Index Error! I can't find what you're looking for. 🤔")
                print("Index Error")
             
        except DownloadError:
                await ctx.send("Sorry, looks like your link is incomplete! 🤔")
                print("Incomplete link!")

# Queue function
@client.command(pass_context=True)
async def q(ctx,*,url):
    
     # Audio and search options
    FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    YDL_OPTS = {'format': 'bestaudio/best','noplaylist':'True', 'outtml': 'song.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192' }],'default_search':'auto'}
    voice = get(client.voice_clients, guild=ctx.guild)

    # If using search
    try:
        with YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)['entries'][0]
        await ctx.send(f"Coming right up! ▶️\n{info.get('webpage_url')}\n")
        URL = info['formats'][0]['url']
        source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
        print(voice)
        
        
    # If using URL
    except KeyError:
        with YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['formats'][0]['url']
        source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
        print(voice)
    except IndexError:
            await ctx.send("Index Error! I can't find what you're looking for. 🤔")
            print("Index Error")
             
    except DownloadError:
            await ctx.send("Sorry, looks like your link is incomplete! 🤔")
            print("Incomplete link!")
        
    guild_id = ctx.message.guild.id        
    
    # Checks if queue is empty
    if guild_id in queues:
        queues[guild_id].append(source)
    else:
        queues[guild_id] = [source]
    await ctx.send("Song queued! ✔️")
    print("Song added to queue")

# Lists songs in queue
@client.command(pass_context=True)
async def list(ctx):
    await ctx.send(queues)
    

# Clears the queue
@client.command(pass_context=True)
async def clear(ctx):
    queues.clear()
    await ctx.send("Queue cleared! 💥")
    print("Queue cleared")


@client.command(pass_context=True)
async def check(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    if voice.is_playing() == False:
        await ctx.send("Nothing seems to be playing!")
    elif voice.is_playing() == True:
        await ctx.send(f"Something is playing! {voice}")



client.run("ODkyOTY2ODgwODc5NDU2Mjk2.YVUmNg.Th7tNMdjn2phce1wCykeZUxteJ8")

