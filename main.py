import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import os
import asyncio
from flask import Flask
from threading import Thread

# --- 24/7 Web Server (Koyeb Health Check සඳහා අත්‍යවශ්‍යයි) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online 24/7 with Docker!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Setup ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash Commands successfully synced!")

bot = MyBot()

# YouTube Cookies සහ FFmpeg සෙටින්ග්ස්
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'nocheckcertificate': True,
    'cookiefile': 'cookies.txt', # ඔබේ GitHub හි cookies.txt තිබිය යුතුය
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.tree.command(name="play", description="සින්දුවක් ප්ලේ කරන්න")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer(ephemeral=True)
    
    # වොයිස් චැනල් එකට සම්බන්ධ වීම
    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            return await interaction.followup.send("❌ මුලින්ම Voice channel එකකට සම්බන්ධ වෙන්න.")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}" if not search.startswith("http") else search, download=False)
            if 'entries' in info: info = info['entries'][0]
            url = info['url']
            title = info['title']
            
            # Audio Source එක සකස් කිරීම
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            
            # ප්ලේ කරන අතරතුර එන Errors බලා ගැනීමට
            def after_playing(error):
                if error: print(f'Player error: {error}')

            if interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.stop()
                
            interaction.guild.voice_client.play(source, after=after_playing)
            await interaction.followup.send(f"🎶 දැන් වාදනය වේ: **{title}**")
            
    except Exception as e:
        error_msg = str(e).lower()
        if "ffmpeg" in error_msg:
            await interaction.followup.send("❌ FFmpeg සොයාගත නොහැක. කරුණාකර Dockerfile එක පරීක්ෂා කරන්න.")
        else:
            await interaction.followup.send(f"❌ දෝෂයක්: {str(e)[:100]}")

@bot.tree.command(name="stop", description="සින්දුව නතර කරන්න")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("🛑 සින්දුව නතර කළා", ephemeral=True)

@bot.tree.command(name="leave", description="Channel එකෙන් ඉවත් වන්න")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 ඉවත් වුණා", ephemeral=True)

keep_alive()
# TOKEN එක Koyeb Environment Variables වල DISCORD_TOKEN ලෙස තිබිය යුතුයි
bot.run(os.getenv('DISCORD_TOKEN'))
