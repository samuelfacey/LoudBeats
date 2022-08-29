import os
import threading
import discord
from discord.utils import get
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError
import datetime
import traceback
import speech_recognition as sr
import asyncio
import pvporcupine
import pyaudio
import struct
import time
from playsound import playsound


client = commands.Bot(command_prefix='!')

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
P_TOKEN = os.getenv('PICO_TOKEN')

# ----
access_key = P_TOKEN
keyword_paths = ['C:\\Users\\Epics\\Desktop\\LoudBeats\\wake_words\\Loud-beats_en_windows_v2_1_0.ppn']

handle = None
pa = None
audio_stream = None
# ----
queues = {}
qList = []
# ----

# Enables Speech commands
@client.command(pass_context=True)
async def listen(ctx):
        await join(ctx)
        print("listening for wake word...")
        try:
            handle = pvporcupine.create(access_key=access_key, keyword_paths=keyword_paths)
            pa = pyaudio.PyAudio()
            audio_stream = pa.open(rate=handle.sample_rate,channels=1,format=pyaudio.paInt16,input=True,frames_per_buffer=handle.frame_length)
            iterations = 0

            while True:
                pcm = audio_stream.read(handle.frame_length)
                pcm = struct.unpack_from("h" * handle.frame_length, pcm)
                keyword_index = handle.process(pcm)
                iterations += 1
                if keyword_index >= 0:
                    print("Hotword Detected")
                    playsound("audio\\Activated.wav")
                    listener = sr.Recognizer()
                    try:
                        with sr.Microphone() as source:
                            print("Listening") 
                            await ctx.send("Listening...")
                            voice = listener.listen(source, timeout=7)
                            command = listener.recognize_google(voice, language="en-US")
                            command = command.lower()
                            playsound("audio\\Understood.wav")
                            await ctx.send(f"You said: {command}")
                            if "play" and "right now" in command:
                                c = command.replace("play","")
                                await play_now(ctx=ctx, url=c)
                            elif "play" in command:
                                c = command.replace("play","")
                                await play(ctx=ctx, url=c)
                            elif "stop" in command:
                                await stop(ctx)
                            elif "pause" in command:
                                await pause(ctx)
                            elif "resume" in command:
                                await resume(ctx)
                            elif "skip" in command:
                                await skip(ctx)
                            elif "leave" in command:
                                await leave(ctx)
                            elif "queue" in command:
                                await list(ctx)
                            elif "clear" in command:
                                await clear(ctx)
                    except Exception as e:
                        print(e)
                    break
                if iterations >= 500:
                    await ctx.send("No longer listening! Try again if you want :)")
                    break
                          
        finally:  
                if handle is not None:
                    handle.delete()
                if audio_stream is not None:
                    audio_stream.close()
                if pa is not None:
                    pa.terminate()
                return

# Checks if anything is in queue
def check_queue(*args):
    try:
        if queues == {}:
            queues[args[1]] = args[2]
        else:
            if queues[args[1]] != []:
                voice = args[0].guild.voice_client
                source = queues[args[1]].pop(0)
                voice.play(source, after=lambda e: check_queue(args[0], args[0].message.guild.id))
            qList.pop(0)
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
        await join(ctx)
        
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

# Plays requested song immediately
@client.command(pass_context=True)
async def play_now(ctx,*,url):
    # Audio and search options
        FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        YDL_OPTS = {'format': 'bestaudio/best','noplaylist':'True', 'outtml': 'song.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192' }],'default_search':'auto'}
        voice = get(client.voice_clients, guild=ctx.guild)
        try:
                # Will download and play track
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

# Debug command to check if the bot is trying to play something
@client.command(pass_context=True)
async def check(ctx):
    voice = discord.utils.get(client.voice_clients,guild=ctx.guild)
    if voice.is_playing() == False:
        await ctx.send("Nothing seems to be playing!")
    elif voice.is_playing() == True:
        await ctx.send(f"Something is playing! {voice} // {qList(0)}")

client.run(TOKEN)
#--🚀 Loudbeats by Samuel Facey 2022 🚀--#