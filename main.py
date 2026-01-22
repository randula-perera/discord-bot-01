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
def home(): return "Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run).start()

# --- Bot Setup ---
class MyBot(commands.Bot):
    def __init__(self):
        # Intents නිවැරදිව සැකසීම
        intents = discord.Intents.default()
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)
        self.is_247 = {}

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Slash Commands Synced!")

bot = MyBot()

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# --- Commands ---

@bot.tree.command(name="join", description="Voice channel එකට සම්බන්ධ වේ")
async def join(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        await interaction.followup.send(f"✅ **{channel.name}** වෙත සම්බන්ධ වුණා")
    else:
        await interaction.followup.send("❌ මුලින්ම Voice channel එකකට සම්බන්ධ වෙන්න.")

@bot.tree.command(name="play", description="සින්දුවක් ප්ලේ කරන්න")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer(ephemeral=True)
    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            return await interaction.followup.send("❌ කලින් Voice channel එකකට සම්බන්ධ වෙන්න.")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}" if not search.startswith("http") else search, download=False)
            if 'entries' in info: info = info['entries'][0]
            url = info['url']
            title = info['title']
            
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=title))
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            interaction.guild.voice_client.stop()
            interaction.guild.voice_client.play(source)
            await interaction.followup.send(f"🎶 දැන් වාදනය වේ: **{title}**")
    except Exception as e:
        await interaction.followup.send(f"❌ දෝෂයක්: {str(e)}")

@bot.tree.command(name="stop", description="සින්දුව නතර කරන්න")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.followup.send("🛑 සින්දුව නතර කළා")
    else:
        await interaction.followup.send("❌ මම සින්දුවක් ප්ලේ කරමින් නොවේ ඉන්නේ.")

@bot.tree.command(name="leave", description="Channel එකෙන් ඉවත් වන්න")
async def leave(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if interaction.guild.voice_client:
        bot.is_247[interaction.guild.id] = False
        await interaction.guild.voice_client.disconnect()
        await interaction.followup.send("👋 ඉවත් වුණා")
    else:
        await interaction.followup.send("❌ මම Voice channel එකක නැත.")

@bot.tree.command(name="247", description="බොට්ව 24/7 චැනල් එකේ තබන්න")
async def mode_247(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild.id
    bot.is_247[guild_id] = not bot.is_247.get(guild_id, False)
    status = "සක්‍රියයි" if bot.is_247[guild_id] else "අක්‍රියයි"
    await interaction.followup.send(f"♾️ 24/7 Mode {status}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and after.channel is None:
        if bot.is_247.get(member.guild.id, False):
            await before.channel.connect()

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
