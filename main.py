import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from commands import Player
load_dotenv()

# Variable Declaration
TOKEN = os.getenv('DISCORD_TOKEN')
P_TOKEN = os.getenv('PICO_TOKEN')

access_key = P_TOKEN
keyword_paths = ['C:\\Users\\Epics\\Desktop\\LoudBeats\\wake_words\\Loud-beats_en_windows_v2_1_0.ppn']

handle = None
pa = None
audio_stream = None

queues = {}
qList = []

# Initializes Bot client, and Player object
client = commands.Bot(command_prefix='/')
player = Player(client=client, queues=queues, qList=qList,
                handle=handle, pa=pa, audio_stream=audio_stream,
                access_key=access_key, keyword_paths=keyword_paths)

# Enables Speech commands
@client.command(pass_context=True)
async def listen(ctx):
    await player.listen(ctx)
        
# Displays bot status
@client.event
async def on_ready():
    print("Loudbeats has arrived!")
    print("----------------------")
    await client.change_presence(status=discord.Status.online, activity=discord.Game("Audio for Discord"))
    
# Bot joins voice channel
@client.command(pass_context=True)
async def join(ctx):
    await player.join(ctx)

# Bot leaves voice channel
@client.command(pass_context=True)
async def leave(ctx):
    await player.leave(ctx)

# Pauses audio
@client.command(pass_content=True)
async def pause(ctx):
    await player.pause(ctx)

# Stops playback and clears queue 
@client.command(pass_content=True)
async def stop(ctx):
    await player.stop(ctx)

# Resumes audio if paused
@client.command(pass_content=True)
async def resume(ctx):
    await player.resume(ctx)

# Skips current song
@client.command(pass_content=True)
async def skip(ctx):
    await player.skip(ctx)

# Bot plays song
@client.command(pass_context=True)
async def play(ctx,*,url):
    await player.play(ctx=ctx,url=url)     

# Lists songs in queue
@client.command(pass_context=True)
async def list(ctx):
    await player.list(ctx)

# Clears the queue
@client.command(pass_context=True)
async def clear(ctx):
    await player.clear(ctx)

# Starts Bot
if __name__ == "__main__":
    client.run(TOKEN)

#--🚀 Loudbeats by Samuel Facey 2022 🚀--#