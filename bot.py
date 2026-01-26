import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os

TOKEN = os.getenv('DISCORD_TOKEN')
YOUTUBE_URL = 'https://www.youtube.com/live/xf9Ejt4OmWQ?si=1t_PXPMienFqVtal'

# FFmpeg සහ YouTube settings
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=1.0): # Volume 1.0 (Full)
        super().__init__(source, volume)
        self.data = data

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.tree.command(name="join", description="Join voice channel and play YouTube live")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("ඔයා voice channel එකකට join වෙලා ඉන්න ඕනේ!")
        return

    await interaction.response.defer()
    
    channel = interaction.user.voice.channel
    if interaction.guild.voice_client:
        vc = await interaction.guild.voice_client.move_to(channel)
    else:
        vc = await channel.connect()

    await interaction.followup.send(f"Joined {channel}! සද්දේ ඇහෙන්න ටික වෙලාවක් යන්න පුළුවන්...")

    # --- මියුසික් ප්ලේ කරන කොටස ---
    while vc.is_connected():
        if not vc.is_playing():
            try:
                player = await YTDLSource.from_url(YOUTUBE_URL, loop=bot.loop, stream=True)
                vc.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            except Exception as e:
                print(f"Error: {e}")
        await asyncio.sleep(5)

bot.run(TOKEN)
