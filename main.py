import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
from flask import Flask
from threading import Thread
import os

# --- 24/7 Web Server Setup ---
app = Flask('')
@app.route('/')
def home(): return "Premium Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Music Bot Logic with Queue ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.is_247 = {}
        self.queues = {} # සින්දු ලැයිස්තුව තබා ගැනීමට
        self.loop_status = {} # Loop එක සක්‍රියද බැලීමට

    async def setup_hook(self):
        await self.tree.sync()
        print("Premium Slash Commands Synced!")

bot = MyBot()

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'default_search': 'auto'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

# ඊළඟ සින්දුව ප්ලේ කරන Function එක
def play_next(interaction, guild_id):
    if guild_id in bot.queues and bot.queues[guild_id]:
        # Loop එක සක්‍රිය නම් සින්දුව අයින් නොකර නැවත අගට එකතු කරයි
        if bot.loop_status.get(guild_id, False):
            song = bot.queues[guild_id].pop(0)
            bot.queues[guild_id].append(song)
        else:
            song = bot.queues[guild_id].pop(0)

        url = song['url']
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        interaction.guild.voice_client.play(source, after=lambda e: play_next(interaction, guild_id))
    else:
        # සින්දු නැත්නම් සහ 24/7 නැත්නම් විනාඩි 5කින් අයින් වීමට සකස් කළ හැක

# --- Premium Slash Commands ---

@bot.tree.command(name="play", description="සින්දුවක් ප්ලේ කරන්න හෝ Queue එකට එකතු කරන්න")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()
    guild_id = interaction.guild.id

    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            return await interaction.followup.send("❌ කලින් Voice Channel එකකට ජොයින් වෙන්න!")

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(search, download=False)
        if 'entries' in info: info = info['entries'][0]
        song_data = {'url': info['url'], 'title': info['title']}

    if guild_id not in bot.queues: bot.queues[guild_id] = []
    
    if interaction.guild.voice_client.is_playing():
        bot.queues[guild_id].append(song_data)
        await interaction.followup.send(f"✅ Queue එකට එකතු කළා: **{info['title']}**")
    else:
        source = discord.FFmpegPCMAudio(song_data['url'], **FFMPEG_OPTIONS)
        interaction.guild.voice_client.play(source, after=lambda e: play_next(interaction, guild_id))
        await interaction.followup.send(f"🎶 දැන් වාදනය වේ: **{info['title']}**")

@bot.tree.command(name="skip", description="දැන් ප්ලේ වන සින්දුව Skip කරන්න")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("⏭️ සින්දුව Skip කළා.")
    else:
        await interaction.response.send_message("❌ ප්ලේ වන සින්දුවක් නැත.")

@bot.tree.command(name="queue", description="සින්දු ලැයිස්තුව (Queue) බලාගන්න")
async def queue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id in bot.queues and bot.queues[guild_id]:
        description = ""
        for i, song in enumerate(bot.queues[guild_id][:10], 1):
            description += f"{i}. {song['title']}\n"
        await interaction.response.send_message(f"📜 **සින්දු ලැයිස්තුව:**\n{description}")
    else:
        await interaction.response.send_message("Empty Queue!")

@bot.tree.command(name="loop", description="දැනට ප්ලේ වන සින්දුව/ලැයිස්තුව නැවත නැවත ප්ලේ කරන්න")
async def loop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    status = bot.loop_status.get(guild_id, False)
    bot.loop_status[guild_id] = not status
    msg = "🔁 **Loop සක්‍රියයි!**" if not status else "➡️ **Loop අක්‍රියයි.**"
    await interaction.response.send_message(msg)

@bot.tree.command(name="clear", description="සින්දු ලැයිස්තුව මකන්න")
async def clear(interaction: discord.Interaction):
    bot.queues[interaction.guild.id] = []
    await interaction.response.send_message("🗑️ Queue එක මැකුවා.")

@bot.tree.command(name="247", description="බොට්ව 24/7 චැනල් එකේ තබන්න")
async def mode_247(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    bot.is_247[guild_id] = not bot.is_247.get(guild_id, False)
    msg = "♾️ **24/7 Mode On!**" if bot.is_247[guild_id] else "📴 **24/7 Mode Off.**"
    await interaction.response.send_message(msg)

@bot.tree.command(name="stop", description="සින්දු නතර කර බොට්ව ඉවත් කරන්න")
async def stop(interaction: discord.Interaction):
    bot.is_247[interaction.guild.id] = False
    bot.queues[interaction.guild.id] = []
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("🛑 බොට් ඉවත් වුණා.")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and after.channel is None:
        if bot.is_247.get(member.guild.id, False):
            await before.channel.connect()

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
