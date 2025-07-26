import discord
from discord.ext import commands
import config
import os
import asyncio
import signal
import sys
import datetime

BOT_TOKEN = config.TOKEN

cogs_list = [
    'admin',
    'randoms',
    'rs3_finances' # The new cog for clan finances
]

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='?', intents=intents, guild_ids=[config.GUILD_ID])
bot.config = config # Attach the config module to the bot instance for cogs to access

for cog_name in cogs_list:
    try:
        bot.load_extension(f'cogs.{cog_name}')
        print(f'[{datetime.datetime.now()}] Loaded cog: {cog_name}')
    except Exception as e:
        print(f'[{datetime.datetime.now()}] Failed to load cog {cog_name}. Error: {e}')

@bot.event
async def on_ready():
    print(f'[{datetime.datetime.now()}] Logged in as {bot.user.name}')
    print(f'[{datetime.datetime.now()}] Bot ID: {bot.user.id}')
    print(f'[{datetime.datetime.now()}] ------')

    print(f"[{datetime.datetime.now()}] Attempting explicit sync of slash commands for guild ID: {config.GUILD_ID}")
    try:
        await asyncio.sleep(0.5)
        synced_commands = await bot.sync_commands(guild_ids=[config.GUILD_ID])
        if synced_commands is not None:
            print(f"[{datetime.datetime.now()}] Successfully synced {len(synced_commands)} commands.")
            for command in synced_commands:
                print(f"[{datetime.datetime.now()}]   - /{command.name} (ID: {command.id})")
        else:
            print(f"[{datetime.datetime.now()}] bot.sync_commands returned None.")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Failed to explicitly sync slash commands. Error: {e}")

async def shutdown(loop, signal=None):
    if signal:
        print(f"[{datetime.datetime.now()}] Received exit signal {signal.name}...")
    print(f"[{datetime.datetime.now()}] Closing Discord connection...")
    await bot.close()
    print(f"[{datetime.datetime.now()}] Discord connection closed.")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    print(f"[{datetime.datetime.now()}] Shutting down event loop...")
    loop.stop()
    print(f"[{datetime.datetime.now()}] Event loop stopped.")
    sys.exit(0)

def handle_signal(signum, frame):
    loop = asyncio.get_event_loop()
    loop.create_task(shutdown(loop, signal.Signals(signum)))

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

bot.run(BOT_TOKEN)

