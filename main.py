import discord
from discord.ext import commands
import yt_dlp
import asyncio
from flask import Flask
from threading import Thread
import os

# --- 24/7 Web Server (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online and Running 24/7!"

def run():
    # Koyeb සාමාන්‍යයෙන් පාවිච්චි කරන්නේ 8080 port එකයි
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Music Configuration
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

is_247 = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/play"))

# --- Commands ---

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()
        await ctx.send(f"✅ **{channel}** වෙත සම්බන්ධ වුණා.")
    else:
        await ctx.send("❌ මුලින්ම Voice Channel එකකට ජොයින් වෙන්න!")

@bot.command()
async def play(ctx, *, search):
    if not ctx.voice_client:
        await ctx.invoke(join)
    
    async with ctx.typing():
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                url = info['url']
                title = info['title']
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                ctx.voice_client.stop()
                ctx.voice_client.play(source)
                await ctx.send(f"🎵 දැන් වාදනය වේ: **{title}**")
        except Exception as e:
            await ctx.send(f"❌ දෝෂයක් සිදු වුණා: {str(e)}")

@bot.command(name="24/7")
async def mode_247(ctx):
    guild_id = ctx.guild.id
    if guild_id not in is_247 or not is_247[guild_id]:
        is_247[guild_id] = True
        await ctx.send("♾️ **24/7 Mode සක්‍රියයි!** මම මේ චැනල් එකේ දිගටම ඉන්නවා.")
    else:
        is_247[guild_id] = False
        await ctx.send("📴 **24/7 Mode අක්‍රියයි.**")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ සින්දුව Skip කළා.")
    else:
        await ctx.send("❌ දැනට කිසිම සින්දුවක් ප්ලේ වෙන්නේ නැහැ.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        is_247[ctx.guild.id] = False
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 නතර කළා සහ Voice Channel එකෙන් ඉවත් වුණා.")

# Disconnect වුණොත් ආයේ Join වෙන්න (24/7 Mode)
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and after.channel is None:
        guild_id = member.guild.id
        if guild_id in is_247 and is_247[guild_id]:
            await before.channel.connect()

# Koyeb Environment Variable එකෙන් Token එක ලබා ගැනීම
keep_alive()
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("Error: DISCORD_TOKEN හමු වුණේ නැහැ. කරුණාකර Koyeb Environment Variables පරීක්ෂා කරන්න.")
