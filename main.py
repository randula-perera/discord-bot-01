import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import os
from flask import Flask
from threading import Thread

# --- 24/7 Server Setup ---
app = Flask('')
@app.route('/')
def home(): return "Premium Music Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run).start()

# --- Bot Setup ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.is_247 = {}

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# --- Commands ---

@bot.tree.command(name="join", description="Voice channel එකට සම්බන්ධ වේ")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"✅ **{channel.name}** වෙත සම්බන්ධ වුණා", ephemeral=True)
    else:
        await interaction.response.send_message("❌ මුලින්ම Voice channel එකකට සම්බන්ධ වෙන්න.", ephemeral=True)

@bot.tree.command(name="play", description="සින්දුවක් ප්ලේ කරන්න")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.send_message(f"🔍 සෙවුම් කරමින්: {search}", ephemeral=True)
    
    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            return

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(search, download=False)
        if 'entries' in info: info = info['entries'][0]
        url = info['url']
        
        # බොට්ගේ Status එකේ සින්දුවේ නම පෙන්වීම
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=info['title']))
        
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        interaction.guild.voice_client.stop()
        interaction.guild.voice_client.play(source)

@bot.tree.command(name="stop", description="සින්දුව නතර කරන්න")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("🛑 සින්දුව නතර කළා", ephemeral=True)
    else:
        await interaction.response.send_message("❌ මම සින්දුවක් ප්ලේ කරමින් නොවේ ඉන්නේ.", ephemeral=True)

@bot.tree.command(name="leave", description="Channel එකෙන් ඉවත් වන්න")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        bot.is_247[interaction.guild.id] = False # Leave වෙද්දී 24/7 mode එක ඕෆ් කරයි
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 ඉවත් වුණා", ephemeral=True)
    else:
        await interaction.response.send_message("❌ මම Voice channel එකක නැත.", ephemeral=True)

@bot.tree.command(name="247", description="24/7 Mode එක සක්‍රිය/අක්‍රිය කරන්න")
async def mode_247(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    bot.is_247[guild_id] = not bot.is_247.get(guild_id, False)
    status = "සක්‍රියයි" if bot.is_247[guild_id] else "අක්‍රියයි"
    await interaction.response.send_message(f"♾️ 24/7 Mode {status}", ephemeral=True)

# 24/7 Auto Reconnect Logic
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and after.channel is None:
        if bot.is_247.get(member.guild.id, False):
            await before.channel.connect()

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
