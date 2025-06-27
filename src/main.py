import discord
import os
from dotenv import load_dotenv

load_dotenv()

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user}はオンラインです。")

# このファイル(main.py)からの相対パスでcogsディレクトリを指定
cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')

for filename in os.listdir(cogs_dir):
    if filename.endswith('.py') and not filename.startswith('__'):
        # srcディレクトリが起点となるため、'cogs.ファイル名'で指定
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(os.getenv("TOKEN"))



