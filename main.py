import discord
from discord import app_commands # Slash commands සඳහා
from discord.ext import commands
import yt_dlp
import asyncio
from flask import Flask
from threading import Thread
import os

# --- 24/7 Web Server ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"

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
        # මෙතනින් තමයි commands ටික Discord එකට sync කරන්නේ
        await self.tree.sync()
        print("Slash Commands Synced!")

bot = MyBot()

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': False, 'quiet': True, 'default_search': 'auto'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# --- Slash Commands ---

@bot.tree.command(name="join", description="Voice channel එකට සම්බන්ධ වේ")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"✅ {channel.name} වෙත සම්බන්ධ වුණා!")
    else:
        await interaction.response.send_message("❌ මුලින්ම Voice channel එකකට සම්බන්ධ වෙන්න.")

@bot.tree.command(name="play", description="සින්දුවක් ප්ලේ කරන්න")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer() # ලෝඩ් වෙන්න වෙලාව ලබා දීම
    
    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            return await interaction.followup.send("❌ Voice channel එකක නැත.")

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
        url = info['url']
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        interaction.guild.voice_client.stop()
        interaction.guild.voice_client.play(source)
    
    await interaction.followup.send(f"🎵 ප්ලේ වෙනවා: **{info['title']}**")

@bot.tree.command(name="stop", description="නතර කර ඉවත් වන්න")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("🛑 නතර කළා.")
    else:
        await interaction.response.send_message("❌ මම voice channel එකක නැහැ.")

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
