import discord
from discord.ext import commands
from discord import Option
import random

class randoms(commands.Cog):
    """
    A cog containing miscellaneous fun commands.
    """

    # [CORRECTED] The __init__ method now only takes `bot`.
    def __init__(self, bot):
        """Initializes the randoms cog."""
        self.bot = bot
        # [CORRECTED] The config is now accessed through the bot instance.
        self.config = bot.config # Access config via bot.config

    @discord.slash_command(description="Rolls a random number between 1 and a user-specified number.")
    async def roll(self, ctx, max_number: int):
        """Rolls a random number between 1 and a user-specified number."""
        if max_number <= 0:
            await ctx.respond("Please enter a positive number.")
            return

        random_number = random.randrange(1, max_number + 1) # Use max_number + 1 to make it inclusive
        await ctx.respond(f"You rolled: {random_number} (1 to {max_number})")

# [CORRECTED] The setup function now only takes `bot` as an argument.
def setup(bot):
    """Called by Pycord to add the cog to the bot."""
    # Only pass bot to the cog's constructor
    bot.add_cog(randoms(bot))
