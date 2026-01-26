import discord
from discord.ext import commands
import yt_dlp
import asyncio

# --- SETTINGS ---
TOKEN = 'YOUR_BOT_TOKEN_HERE'
YOUTUBE_URL = 'https://www.youtube.com/live/xf9Ejt4OmWQ?si=1t_PXPMienFqVtal'

# Bot Intents setup
intents = discord.Intents.default()
intents.message_content = True  # Command කියවන්න මේක ඕනේ
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
    print(f'{bot.user.name} is online and ready!')

@bot.command()
async def join(ctx):
    """ඔයා ඉන්න voice channel එකට bot ව ගෙන්න ගන්න"""
    if not ctx.author.voice:
        await ctx.send("මුලින්ම ඔයා voice channel එකකට join වෙලා ඉන්න ඕනේ!")
        return

    channel = ctx.author.voice.channel
    
    # දැනටමත් වෙන channel එකක ඉන්නවා නම් එතනට යනවා
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send(f"Joined {channel}! Playing YouTube Live 24/7...")

    # Play logic
    vc = ctx.voice_client
    while vc.is_connected():
        if not vc.is_playing():
            try:
                player = await YTDLSource.from_url(YOUTUBE_URL, loop=bot.loop, stream=True)
                vc.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            except Exception as e:
                print(f"Error: {e}")
        await asyncio.sleep(5)

@bot.command()
async def leave(ctx):
    """Bot ව channel එකෙන් අයින් කරන්න"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected!")
    else:
        await ctx.send("මම voice channel එකක නෙවෙයි ඉන්නේ.")

bot.run(TOKEN)
