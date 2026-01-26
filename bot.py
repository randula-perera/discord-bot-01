import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os  # Environment variables කියවන්න ඕනේ

# --- SETTINGS (Environment Variables වලින් ගනී) ---
TOKEN = os.getenv('DISCORD_TOKEN') # Koyeb එකේ ඔයා දුන්න Key එක 'DISCORD_TOKEN' නම්
YOUTUBE_URL = 'https://www.youtube.com/live/xf9Ejt4OmWQ?si=1t_PXPMienFqVtal'

# Bot Intents setup
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="/", intents=intents)

ytdl_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def join(ctx):
    """Voice channel එකට join වී streaming ආරම්භ කරයි"""
    if not ctx.author.voice:
        await ctx.send("ඔයා voice channel එකකට join වෙලා ඉන්න ඕනේ!")
        return

    channel = ctx.author.voice.channel
    
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send(f"Joined {channel}! ආරම්භ කරමින්...")

    vc = ctx.voice_client
    
    # පරණ player එකක් තිබ්බොත් නතර කරන්න
    if vc.is_playing():
        vc.stop()

    while vc.is_connected():
        if not vc.is_playing():
            try:
                async with ctx.typing():
                    player = await YTDLSource.from_url(YOUTUBE_URL, loop=bot.loop, stream=True)
                    vc.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            except Exception as e:
                print(f"Streaming Error: {e}")
        
        await asyncio.sleep(10) # තත්පර 10කට වරක් status එක බලනවා

@bot.command()
async def leave(ctx):
    """Bot අයින් කරන්න"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected!")

# Token එක නැත්නම් error එකක් පෙන්වන්න
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_TOKEN සොයාගත නොහැක. Koyeb Environment Variables පරීක්ෂා කරන්න.")
