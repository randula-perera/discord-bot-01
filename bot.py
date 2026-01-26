import discord
from discord.ext import commands
from discord import app_commands # මේක අලුතින් ඕනේ
import os

TOKEN = os.getenv('DISCORD_TOKEN')

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        # මේකෙන් තමයි Discord එකට commands register කරන්නේ
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.tree.command(name="join", description="Join voice channel and play YouTube live")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("ඔයා voice channel එකකට join වෙලා ඉන්න ඕනේ!")
        return

    await interaction.response.defer() # ලොකු වැඩක් නිසා පොඩ්ඩක් ඉන්න කියනවා
    
    channel = interaction.user.voice.channel
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect()

    # Streaming logic එක මෙතනට (කලින් දුන්න එකමයි)
    await interaction.followup.send(f"Joined {channel}!")

bot.run(TOKEN)
