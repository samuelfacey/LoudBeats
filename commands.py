from discord.utils import get
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError
import datetime
import traceback

class Player:
    def __init__(self, client, audio_queue, audio_list) -> None:
        self.client = client
        self.audio_queue = audio_queue
        self.audio_list = audio_list

    def check_queue(self, *args):
        try:
            if self.audio_queue == {}:
                try:
                    self.audio_queue[args[1]] = args[2]
                except IndexError:
                    pass
            else:
                if self.audio_queue[args[1]] != []:
                    voice = args[0].guild.voice_client
                    source = self.audio_queue[args[1]].pop(0)
                    try:
                        voice.play(source, after=lambda e: self.check_queue(args[0], args[0].message.guild.id))
                    except:
                        pass
                
                if self.audio_list != []:
                    self.audio_list.pop(0)

        except Exception:
            traceback.print_exc()


    async def clear(self,ctx):
        self.audio_queue.clear()
        self.audio_list.clear()
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

        voice = get(self.client.voice_clients,guild=ctx.guild)
    
        if self.audio_list == []:
            await ctx.send("Queue appears to be empty! 🤔")

        listStr = ""
        listNum = 0
        
        for list in self.audio_list:
            listNum += 1
            listNumStr = str(listNum)
            listStr += str(listNumStr + ". " + list + "\n")
        
        listStr = listStr[:-1]
        await ctx.send(listStr)

        if not voice.is_playing() and not voice.is_paused() and self.audio_queue == []:
            self.audio_list.clear()


    async def play(self,ctx,*,youtube_url):
        # Joins voice channel
        await self.join(ctx)
        
    # Audio and search options for YT-DL
        FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        YDL_OPTS = {'format': 'bestaudio/best','noplaylist':'True', 'outtml': 'song.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192' }],'default_search':'auto'}
        voice = get(self.client.voice_clients, guild=ctx.guild)
        guild_id = ctx.message.guild.id

        # Called when user searches using the song title instead of a URL
        async def search_with_title():
            
            # If nothing is playing, will download and play track
            if not voice.is_playing():
                source = await getSong(query_type='title', youtube_URL=youtube_url)
                voice.play(source, after=lambda e: self.check_queue(ctx, ctx.message.guild.id, source))
                voice.is_playing()

            # If something is already playing, add the requested track to queue
            else:
                source = await getSong(query_type='title', youtube_URL=youtube_url)
                
                # Checks if queue is empty
                try:
                    await queueSong(guild_id=guild_id, source=source)
                except Exception:
                    traceback.print_exc()
                    await ctx.send("Sorry, the song failed to queue. Please try again.")
        
        # Called when user searches with a URL
        async def search_with_url():

            # If nothing is playing, will download and play track
            if not voice.is_playing():
                source = await getSong(query_type='URL', youtube_URL=youtube_url)
                voice.play(source, after=lambda e: self.check_queue(ctx, ctx.message.guild.id, source))
                voice.is_playing()

            # If something is already playing, add the requested track to queue
            else:
                source = await getSong(query_type='URL', youtube_URL=youtube_url)

                # Checks if queue is empty
                await queueSong(guild_id=guild_id, source=source)
        
        async def getSong(query_type, youtube_URL):
            try:
                if query_type == 'title':
                    with YoutubeDL(YDL_OPTS) as ydl:
                        info = ydl.extract_info(youtube_URL, download=False)['entries'][0]
                
                else:
                    with YoutubeDL(YDL_OPTS) as ydl:
                        info = ydl.extract_info(youtube_URL, download=False)
                        

                await ctx.send(f"Coming right up! ▶️\n{info.get('webpage_url')}\n")

                audio_duration = info.get('duration')
                audio_duration_seconds = str(datetime.timedelta(seconds=int(audio_duration)))

                self.audio_list.append(f"{info.get('title')} | {audio_duration_seconds}")
                URL = info['formats'][0]['url']

                return FFmpegPCMAudio(URL, **FFMPEG_OPTS)
            
            except IndexError:
                await ctx.send("Index Error! I can't find what you're looking for. 🤔")
                print("Index Error")
             
            except DownloadError:
                await ctx.send("Sorry, looks like your link is incomplete! 🤔")
                print("Incomplete link!")

            except Exception:
                raise Exception('Failed to fetch song.')


        async def queueSong(guild_id, source):
            if guild_id in self.audio_queue:
                self.audio_queue[guild_id].append(source)
            else:
                self.audio_queue[guild_id] = [source]
            await ctx.send("Song queued! 👍")
            
        try:
            if 'https://' in youtube_url:
                await search_with_url()
            else:
                await search_with_title()

        
        except Exception:
                traceback.print_exc()
                self.audio_queue.clear()
                self.audio_list.clear()
                voice.stop()
                await ctx.send("Sorry, something just went horrifically wrong! 😟 Please try again.")


    async def pause(self,ctx):
        voice = get(self.client.voice_clients,guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            await ctx.send("Paused! ⏸")
            print("Paused")
        else:
            await ctx.send("There's nothing playing right now! 🤔")


    async def resume(self,ctx):
        voice = get(self.client.voice_clients,guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
            await ctx.send("Resumed! ⏯")
            print("Resumed")
        else:
            await ctx.send("There's nothing paused right now! 🤔")


    async def stop(self,ctx):
        voice = get(self.client.voice_clients,guild=ctx.guild)
        self.audio_queue.clear()
        self.audio_list.clear()
        voice.stop()
        await ctx.send("Stopped! ⏹")
        await ctx.guild.voice_client.disconnect()
    

    async def skip(self,ctx):

        id = ctx.message.guild.id
        voice = ctx.guild.voice_client

        if self.audio_queue == {}:
             await ctx.send('There isn\'t anything to skip! 🤔')
             return

        if self.audio_queue[id] != []:
            voice.stop()
            source = self.audio_queue.get(id)
            if source != []:
                voice.play(source[0], after=lambda e: self.check_queue(ctx, ctx.message.guild.id))
            await ctx.send("Skipped! ⏭️")

        else:
            voice.stop()
            self.audio_list.pop(0)
            await ctx.send("Skipped! ⏭️")