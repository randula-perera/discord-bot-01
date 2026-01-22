import discord
from discord.ext import commands
import yt_dlp
import asyncio
from flask import Flask
from threading import Thread

# --- 24/7 Server Setup ---
app = Flask('')
@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def stream(ctx, url):
    if not ctx.author.voice:
        return await ctx.send("Voice channel එකකට මුලින්ම ජොයින් වෙන්න!")
    
    vc = await ctx.author.voice.channel.connect()
    
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
        vc.play(source)
    
    await ctx.send(f"දැන් Live Stream එක වාදනය වෙනවා: {info['title']}")

keep_alive()
bot.run('MTQ2Mzg0NzEzMDc3ODMwNDU4MA.GU2d2Y.Bua7kC6qgmaOyV8L8JARn5DqT4u3Bzywa7X4EA')
