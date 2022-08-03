import os
import discord
from discord.utils import get
from dotenv import load_dotenv
from discord.ext import commands
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError
import datetime
import traceback

client = commands.Bot(command_prefix='!')

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# ----
queues = {}
qList = []
# ----

# Checks if anything is in queue
def check_queue(*args):
    print(args[1])
    try:
        if queues == {}:
            queues[args[1]] = args[2]
        else:
            if queues[args[1]] != []:
                voice = args[0].guild.voice_client
                source = queues[args[1]].pop(0)
                voice.play(source, after=lambda e: check_queue(args[0], args[0].message.guild.id))
                print("check_queue function CALLED AND UTILIZED")
            qList.pop(0)
            print("qList popped")
    except Exception:
        traceback.print_exc()
        
# Displays bot status
@client.event
async def on_ready():
    print("Loudbeats has arrived!")
    print("----------------------")
    await client.change_presence(status=discord.Status.online, activity=discord.Game("Audio for Discord"))

# Bot joins voice channel
@client.command(pass_context=True)
async def join(ctx):

    channel = ctx.author.voice.channel

    if ctx.author.voice is None:
        await ctx.send("Voice channel is empty! 😔")
    if ctx.voice_client is None:
        await channel.connect()
        print("Joined channel")
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
    qList.clear()
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
        source = queues.get(id)
        voice.play(source, after=lambda e: check_queue(ctx, ctx.message.guild.id))
        await ctx.send("Skipped! ⏭️")
        print("Skipped, queue not empty")
    else:
        voice.stop()
        qList.pop(0)
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
        # ctx.voice_client.stop()
        
    # Audio and search options
        FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        YDL_OPTS = {'format': 'bestaudio/best','noplaylist':'True', 'outtml': 'song.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192' }],'default_search':'auto'}
        voice = get(client.voice_clients, guild=ctx.guild)

        # Called when user searches without a URL
        async def search_with_query():
            
            # If nothing is playing, will download and play track
            if not voice.is_playing():
                with YoutubeDL(YDL_OPTS) as ydl:
                    info = ydl.extract_info(url, download=False)['entries'][0]
                await ctx.send(f"Now playing! 🎉\n{info.get('webpage_url')}\n")
                durInt = int(f"{info.get('duration')}")
                durationCalc = str(datetime.timedelta(seconds=durInt))
                qList.append(f"{info.get('title')} | {durationCalc}")
                URL = info['formats'][0]['url']
                source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                voice.play(source, after=lambda e: check_queue(ctx, ctx.message.guild.id, source))
                voice.is_playing()
                print("Search play called")

            # If something is already playing, add the requested track to queue
            else:
                 # If using search
                try:
                    with YoutubeDL(YDL_OPTS) as ydl:
                        info = ydl.extract_info(url, download=False)['entries'][0]
                    await ctx.send(f"Coming right up! ▶️\n{info.get('webpage_url')}\n")
                    durInt = int(f"{info.get('duration')}")
                    durationCalc = str(datetime.timedelta(seconds=durInt))
                    qList.append(f"{info.get('title')} | {durationCalc}")
                    URL = info['formats'][0]['url']
                    source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                    print(voice)
                    print("Search queue called")
                # If using URL
                except KeyError:
                    with YoutubeDL(YDL_OPTS) as ydl:
                        info = ydl.extract_info(url, download=False)
                    durInt = int(f"{info.get('duration')}")
                    durationCalc = str(datetime.timedelta(seconds=durInt))
                    qList.append(f"{info.get('title')} | {durationCalc}")
                    URL = info['formats'][0]['url']
                    source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                    print(voice)
                    print("URL queue called")
                except IndexError:
                        await ctx.send("Index Error! I can't find what you're looking for. 🤔")
                        print("Index Error")
                        
                except DownloadError:
                        await ctx.send("Sorry, looks like your link is incomplete! 🤔")
                        print("Incomplete link!")
                except:
                        queues.clear()
                        qList.clear()
                        voice.stop()
                        await ctx.send("Sorry, something just went horrifically wrong! 😟 Please try again.")
                # ----------------- 
                guild_id = ctx.message.guild.id 
                
                # Checks if queue is empty
                if guild_id in queues:
                    queues[guild_id].append(source)
                else:
                    queues[guild_id] = [source]
                await ctx.send("Song queued! 👍")
                print("Song added to queue")
        
        # Called when user searches with a URL
        async def search_with_url():

            # If nothing is playing, will download and play track
            if not voice.is_playing():
                with YoutubeDL(YDL_OPTS) as ydl:
                    info = ydl.extract_info(url, download=False)
                await ctx.send(f"Now playing! 🎉\n{info.get('webpage_url')}\n")
                durInt = int(f"{info.get('duration')}")
                durationCalc = str(datetime.timedelta(seconds=durInt))
                qList.append(f"{info.get('title')} | {durationCalc}")
                URL = info['formats'][0]['url']
                source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                voice.play(source, after=lambda e: check_queue(ctx, ctx.message.guild.id, source))
                voice.is_playing()
                print("URL play called")
            # If something is already playing, add the requested track to queue
            else:
                # If using search
                try:
                    with YoutubeDL(YDL_OPTS) as ydl:
                        info = ydl.extract_info(url, download=False)['entries'][0]
                    await ctx.send(f"Coming right up! ▶️\n{info.get('webpage_url')}\n")
                    durInt = int(f"{info.get('duration')}")
                    durationCalc = str(datetime.timedelta(seconds=durInt))
                    qList.append(f"{info.get('title')} | {durationCalc}")
                    URL = info['formats'][0]['url']
                    source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                    print(voice)
                    print("Search queue called")
                # If using URL
                except KeyError:
                    with YoutubeDL(YDL_OPTS) as ydl:
                        info = ydl.extract_info(url, download=False)
                    durInt = int(f"{info.get('duration')}")
                    durationCalc = str(datetime.timedelta(seconds=durInt))
                    qList.append(f"{info.get('title')} | {durationCalc}")
                    URL = info['formats'][0]['url']
                    source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                    print(voice)
                    print("URL queue called")
                except IndexError:
                        await ctx.send("Index Error! I can't find what you're looking for. 🤔")
                        print("Index Error")
                        
                except DownloadError:
                        await ctx.send("Sorry, looks like your link is incomplete! 🤔")
                        print("Incomplete link!")
                except:
                        queues.clear()
                        qList.clear()
                        voice.stop()
                        await ctx.send("Sorry, something just went horrifically wrong! 😟 Please try again.")

                guild_id = ctx.message.guild.id 

                # Checks if queue is empty
                if guild_id in queues:
                    queues[guild_id].append(source)
                else:
                    queues[guild_id] = [source]
                await ctx.send("Song queued! 👍")
                print("Song added to queue")

        try:
           await search_with_query()
            
        except KeyError:
            await search_with_url()

        except IndexError:
                await ctx.send("Index Error! I can't find what you're looking for. 🤔")
                print("Index Error")
             
        except DownloadError:
                await ctx.send("Sorry, looks like your link is incomplete! 🤔")
                print("Incomplete link!")
        except Exception:
                traceback.print_exc()
                queues.clear()
                qList.clear()
                voice.stop()
                await ctx.send("Sorry, something just went horrifically wrong! 😟 Please try again.")

# Lists songs in queue
@client.command(pass_context=True)
async def list(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    
    if qList == []:
        await ctx.send("Queue appears to be empty! 🤔")

    listStr = ""
    listNum = 0
    
    for list in qList:
        listNum += 1
        listNumStr = str(listNum)
        listStr += str(listNumStr + ". " + list + "\n")
    
    listStr = listStr[:-1]
    await ctx.send(listStr)

    if not voice.is_playing() and not voice.is_paused() and queues == []:
        qList.clear()

    print(queues)

# Clears the queue
@client.command(pass_context=True)
async def clear(ctx):
    queues.clear()
    qList.clear()
    await ctx.send("Queue cleared! 💥")
    print("Queue cleared")

@client.command(pass_context=True)
async def check(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    if voice.is_playing() == False:
        await ctx.send("Nothing seems to be playing!")
    elif voice.is_playing() == True:
        await ctx.send(f"Something is playing! {voice} // {qList(0)}")

client.run(TOKEN)

#--🚀 Loudbeats by Samuel Facey 2022 🚀--#