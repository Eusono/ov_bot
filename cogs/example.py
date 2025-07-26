import discord
from discord.ext import commands

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ ExampleCog initialized!")  # Debugging print

    @commands.slash_command(name="ping", description="Shows the bot's latency.")
    async def ping(self, ctx):
        """Shows the bot's latency."""
        print("✅ /ping command executed!")  # Debugging output
        await ctx.respond(f'Pong! Latency: {round(self.bot.latency * 1000)}ms')

# FIX: Correctly define `setup` function as `async`
async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
    print("✅ ExampleCog registered!")