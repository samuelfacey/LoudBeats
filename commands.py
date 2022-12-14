import discord
from discord.utils import get
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError
import datetime
import traceback

class Player:
    def __init__(self, client, queues, qList) -> None:
        self.client = client
        self.queues = queues
        self.qList = qList

    # Checks if anything is in queue
    def check_queue(self, *args):
        try:
            if self.queues == {}:
                try:
                    self.queues[args[1]] = args[2]
                except IndexError:
                    pass
            else:
                if self.queues[args[1]] != []:
                    voice = args[0].guild.voice_client
                    source = self.queues[args[1]].pop(0)
                    try:
                        voice.play(source, after=lambda e: self.check_queue(args[0], args[0].message.guild.id))
                    except:
                        pass
                self.qList.pop(0)
        except Exception:
            traceback.print_exc()


    async def clear(self,ctx):
        self.queues.clear()
        self.qList.clear()
        await ctx.send("Queue cleared! 💥")
        print("Queue cleared")


    async def join(self,ctx):
        channel = ctx.author.voice.channel
        if ctx.author.voice is None:
            await ctx.send("Voice channel is empty! 😔")
        if ctx.voice_client is None:
            await channel.connect()
            print("Joined channel")
        else:
            await ctx.voice_client.move_to(channel)
            print("Joined channel")


    async def leave(self,ctx):
        if (ctx.voice_client):
            await ctx.guild.voice_client.disconnect()
            print("Left channel")
        else:
            await ctx.send("I'm not in a voice channel! 🤔")


    async def list(self,ctx):
        voice = discord.utils.get(self.client.voice_clients,guild=ctx.guild)
    
        if self.qList == []:
            await ctx.send("Queue appears to be empty! 🤔")

        listStr = ""
        listNum = 0
        
        for list in self.qList:
            listNum += 1
            listNumStr = str(listNum)
            listStr += str(listNumStr + ". " + list + "\n")
        
        listStr = listStr[:-1]
        await ctx.send(listStr)

        if not voice.is_playing() and not voice.is_paused() and self.queues == []:
            self.qList.clear()


    async def play(self,ctx,*,url):
        # Joins voice channel
        await self.join(ctx)
        
    # Audio and search options
        FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        YDL_OPTS = {'format': 'bestaudio/best','noplaylist':'True', 'outtml': 'song.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192' }],'default_search':'auto'}
        voice = get(self.client.voice_clients, guild=ctx.guild)

        # Called when user searches without a URL
        async def search_with_query():
            
            # If nothing is playing, will download and play track
            if not voice.is_playing():
                with YoutubeDL(YDL_OPTS) as ydl:
                    info = ydl.extract_info(url, download=False)['entries'][0]
                await ctx.send(f"Now playing! 🎉\n{info.get('webpage_url')}\n")
                durInt = int(f"{info.get('duration')}")
                durationCalc = str(datetime.timedelta(seconds=durInt))
                self.qList.append(f"{info.get('title')} | {durationCalc}")
                URL = info['formats'][0]['url']
                source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                voice.play(source, after=lambda e: self.check_queue(ctx, ctx.message.guild.id, source))
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
                    self.qList.append(f"{info.get('title')} | {durationCalc}")
                    URL = info['formats'][0]['url']
                    source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                    print("Search queue called")
                # If using URL
                except KeyError:
                    with YoutubeDL(YDL_OPTS) as ydl:
                        info = ydl.extract_info(url, download=False)
                    durInt = int(f"{info.get('duration')}")
                    durationCalc = str(datetime.timedelta(seconds=durInt))
                    self.qList.append(f"{info.get('title')} | {durationCalc}")
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
                        self.queues.clear()
                        self.qList.clear()
                        voice.stop()
                        await ctx.send("Sorry, something just went horrifically wrong! 😟 Please try again.")
                # ----------------- 
                guild_id = ctx.message.guild.id 
                
                # Checks if queue is empty
                try:
                    if guild_id in self.queues:
                        self.queues[guild_id].append(source)
                    else:
                        self.queues[guild_id] = [source]
                    await ctx.send("Song queued! 👍")
                    print("Song added to queue")
                except AttributeError:
                    await ctx.send("Sorry, the song failed to queue. Please try again.")
        
        # Called when user searches with a URL
        async def search_with_url():

            # If nothing is playing, will download and play track
            if not voice.is_playing():
                with YoutubeDL(YDL_OPTS) as ydl:
                    info = ydl.extract_info(url, download=False)
                await ctx.send(f"Now playing! 🎉\n{info.get('webpage_url')}\n")
                durInt = int(f"{info.get('duration')}")
                durationCalc = str(datetime.timedelta(seconds=durInt))
                self.qList.append(f"{info.get('title')} | {durationCalc}")
                URL = info['formats'][0]['url']
                source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                voice.play(source, after=lambda e: self.check_queue(ctx, ctx.message.guild.id, source))
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
                    self.qList.append(f"{info.get('title')} | {durationCalc}")
                    URL = info['formats'][0]['url']
                    source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                    print("Search queue called")
                # If using URL
                except KeyError:
                    with YoutubeDL(YDL_OPTS) as ydl:
                        info = ydl.extract_info(url, download=False)
                    durInt = int(f"{info.get('duration')}")
                    durationCalc = str(datetime.timedelta(seconds=durInt))
                    self.qList.append(f"{info.get('title')} | {durationCalc}")
                    URL = info['formats'][0]['url']
                    source = FFmpegPCMAudio(URL, **FFMPEG_OPTS)
                    print("URL queue called")
                except IndexError:
                        await ctx.send("Index Error! I can't find what you're looking for. 🤔")
                        print("Index Error")
                        
                except DownloadError:
                        await ctx.send("Sorry, looks like your link is incomplete! 🤔")
                        print("Incomplete link!")
                except:
                        self.queues.clear()
                        self.qList.clear()
                        voice.stop()
                        await ctx.send("Sorry, something just went horrifically wrong! 😟 Please try again.")

                guild_id = ctx.message.guild.id 

                # Checks if queue is empty
                if guild_id in self.queues:
                    self.queues[guild_id].append(source)
                else:
                    self.queues[guild_id] = [source]
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
                self.queues.clear()
                self.qList.clear()
                voice.stop()
                await ctx.send("Sorry, something just went horrifically wrong! 😟 Please try again.")


    async def pause(self,ctx):
        voice = discord.utils.get(self.client.voice_clients,guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            await ctx.send("Paused! ⏸")
            print("Paused")
        else:
            await ctx.send("There's nothing playing right now! 🤔")


    async def resume(self,ctx):
        voice = discord.utils.get(self.client.voice_clients,guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
            await ctx.send("Resumed! ⏯")
            print("Resumed")
        else:
            await ctx.send("There's nothing paused right now! 🤔")


    async def stop(self,ctx):
        voice = discord.utils.get(self.client.voice_clients,guild=ctx.guild)
        self.queues.clear()
        self.qList.clear()
        voice.stop()
        await ctx.send("Stopped! ⏹")
        await ctx.guild.voice_client.disconnect()
        print("Stopped and queue cleared")
    

    async def skip(self,ctx):
        id = ctx.message.guild.id
        voice = ctx.guild.voice_client
        if self.queues[id] != []:
            voice.stop()
            source = self.queues.get(id)
            if source != []:
                voice.play(source[0], after=lambda e: self.check_queue(ctx, ctx.message.guild.id))
            await ctx.send("Skipped! ⏭️")
            print("Skipped, queue not empty")
        else:
            voice.stop()
            self.qList.pop(0)
            await ctx.send("Skipped! ⏭️")
            print("Skipped, queue empty") 