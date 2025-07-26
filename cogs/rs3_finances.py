import discord
from discord.ext import commands
from discord import Option
import json
import os
import datetime
import pytz

# Custom exception for channel checks to provide a specific error message.
class WrongChannelError(commands.CheckFailure):
    pass

# [ADDED] Custom exception for role checks to provide a specific error message.
class NotBankManagerError(commands.CheckFailure):
    pass

# Custom check function to see if the user has a bank manager role.
def is_bank_manager():
    async def predicate(ctx):
        # Get the list of allowed role IDs from the config file attached to the bot.
        allowed_role_ids = ctx.bot.config.BANK_MANAGER_ROLE_IDS
        # Check if any of the user's roles are in the allowed list.
        if any(role.id in allowed_role_ids for role in ctx.author.roles):
            return True
        # [MODIFIED] Raise a specific error if the user does not have the role.
        raise NotBankManagerError("User does not have a required bank manager role.")
    return commands.check(predicate)

# Custom check function to see if the command is used in the correct channel.
def in_admin_channel():
    async def predicate(ctx):
        allowed_channel_id = ctx.bot.config.ADMIN_BOT_COMMANDS_CHANNEL_ID
        if ctx.channel.id == allowed_channel_id:
            return True
        else:
            # Raise a custom exception to be caught by the error handler.
            raise WrongChannelError(f"This command can only be used in the designated admin channel.")
    return commands.check(predicate)


class RS3Finances(commands.Cog):
    """
    A cog for managing the clan's RuneScape 3 finances.
    """

    def __init__(self, bot):
        self.bot = bot
        # Get the bank file path from the bot's config.
        self.bank_file_path = self.bot.config.BANK_FILE_PATH
        self.bank_total = self._load_bank()

    def _load_bank(self):
        """Loads the bank total from the JSON file specified in the config."""
        if os.path.exists(self.bank_file_path):
            try:
                with open(self.bank_file_path, 'r') as f:
                    data = json.load(f)
                    return data.get('total', 0)
            except (json.JSONDecodeError, IOError):
                return 0
        return 0

    def _save_bank(self):
        """Saves the current bank total to the JSON file specified in the config."""
        # Ensure the directory exists before trying to save the file.
        os.makedirs(os.path.dirname(self.bank_file_path), exist_ok=True)
        with open(self.bank_file_path, 'w') as f:
            json.dump({'total': self.bank_total}, f, indent=4)

    def _format_gp(self, amount):
        """Formats a number into a GP string (e.g., 1.1k, 1.05m, 1.15b)."""
        if amount >= 1_000_000_000:
            return f"{amount / 1_000_000_000:.2f}b"
        elif amount >= 1_000_000:
            return f"{amount / 1_000_000:.2f}m"
        elif amount >= 1_000:
            return f"{amount / 1_000:.2f}k"
        return str(amount)

    def _parse_gp_string(self, s: str) -> int | None:
        """Parses a GP string (e.g., "10k", "1.5m") into an integer. Returns None if invalid."""
        s = s.lower().strip()
        multiplier = 1
        if s.endswith('k'):
            multiplier = 1_000
            s = s[:-1]
        elif s.endswith('m'):
            multiplier = 1_000_000
            s = s[:-1]
        elif s.endswith('b'):
            multiplier = 1_000_000_000
            s = s[:-1]
        
        try:
            value = float(s)
            return int(value * multiplier)
        except ValueError:
            return None

    async def _log_transaction(self, ctx, transaction_type: str, amount: int, description: str | None, color: discord.Color):
        """Sends a log of the transaction to the log channel."""
        log_channel_id = self.bot.config.CLAN_BANK_LOG_CHANNEL_ID
        log_channel = self.bot.get_channel(log_channel_id)

        if not log_channel:
            print(f"[{datetime.datetime.now()}] ERROR: Clan bank log channel with ID {log_channel_id} not found.")
            return

        embed = discord.Embed(
            title=f"Bank Transaction Log: {transaction_type}",
            color=color,
            timestamp=datetime.datetime.now(pytz.utc)
        )
        embed.add_field(name="Executor", value=ctx.author.mention, inline=False)
        embed.add_field(name="Amount", value=f"{self._format_gp(amount)} GP", inline=False)
        if description:
            embed.add_field(name="Reason", value=description, inline=False)
        embed.add_field(name="New Balance", value=f"{self._format_gp(self.bank_total)} GP", inline=False)
        
        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            print(f"[{datetime.datetime.now()}] ERROR: Failed to send message to clan bank log channel. {e}")


    clanbank = discord.SlashCommandGroup("clanbank", "Commands for managing the clan bank.")

    @clanbank.command(description="Check the current value of the clan bank.")
    async def check(self, ctx):
        """Displays the current value of the clan bank."""
        formatted_total = self._format_gp(self.bank_total)
        embed = discord.Embed(
            title="💰 Clan Bank Balance 💰",
            description=f"The current clan bank total is **{formatted_total} GP**.",
            color=discord.Color.gold()
        )
        await ctx.respond(embed=embed)

    @clanbank.command(description="Add funds to the clan bank.")
    @is_bank_manager()
    @in_admin_channel() # Restrict command to a specific channel
    async def add(self, ctx,
                  amount: Option(str, "The amount of GP to add (e.g., 500000, 500k, 10m).", required=True),
                  description: Option(str, "Reason for adding the funds.", required=False) = None
                  ):
        """Adds funds to the clan bank."""
        parsed_amount = self._parse_gp_string(amount)

        if parsed_amount is None:
            await ctx.respond("Invalid amount format. Please use a number, or suffixes like 'k', 'm', 'b'.", ephemeral=True)
            return
            
        if parsed_amount <= 0:
            await ctx.respond("Please provide a positive amount to add.", ephemeral=True)
            return

        self.bank_total += parsed_amount
        self._save_bank()
        
        formatted_amount = self._format_gp(parsed_amount)
        formatted_total = self._format_gp(self.bank_total)

        embed = discord.Embed(
            title="✅ Funds Added",
            color=discord.Color.green()
        )
        embed.add_field(name="Amount Added", value=f"{formatted_amount} GP", inline=False)
        if description:
            embed.add_field(name="Reason", value=description, inline=False)
        embed.add_field(name="New Balance", value=f"{formatted_total} GP", inline=False)
        embed.set_footer(text=f"Transaction by {ctx.author.display_name}")

        await ctx.respond(embed=embed)
        await self._log_transaction(ctx, "Deposit", parsed_amount, description, discord.Color.green())

    @clanbank.command(description="Remove funds from the clan bank.")
    @is_bank_manager()
    @in_admin_channel() # Restrict command to a specific channel
    async def remove(self, ctx,
                     amount: Option(str, "The amount of GP to remove (e.g., 500000, 500k, 10m).", required=True),
                     description: Option(str, "Reason for removing the funds.", required=False) = None
                     ):
        """Removes funds from the clan bank."""
        parsed_amount = self._parse_gp_string(amount)

        if parsed_amount is None:
            await ctx.respond("Invalid amount format. Please use a number, or suffixes like 'k', 'm', 'b'.", ephemeral=True)
            return

        if parsed_amount <= 0:
            await ctx.respond("Please provide a positive amount to remove.", ephemeral=True)
            return
        
        if parsed_amount > self.bank_total:
            await ctx.respond("Cannot remove more funds than what is currently in the bank.", ephemeral=True)
            return

        self.bank_total -= parsed_amount
        self._save_bank()

        formatted_amount = self._format_gp(parsed_amount)
        formatted_total = self._format_gp(self.bank_total)

        embed = discord.Embed(
            title="❌ Funds Removed",
            color=discord.Color.red()
        )
        embed.add_field(name="Amount Removed", value=f"{formatted_amount} GP", inline=False)
        if description:
            embed.add_field(name="Reason", value=description, inline=False)
        embed.add_field(name="New Balance", value=f"{formatted_total} GP", inline=False)
        embed.set_footer(text=f"Transaction by {ctx.author.display_name}")

        await ctx.respond(embed=embed)
        await self._log_transaction(ctx, "Withdrawal", parsed_amount, description, discord.Color.red())

    # Updated error handler to distinguish between check failures.
    @add.error
    @remove.error
    async def on_clanbank_error(self, ctx, error):
        """Handles errors for the clanbank commands."""
        if isinstance(error, WrongChannelError):
            # Let the user know they are in the wrong channel.
            admin_channel = self.bot.get_channel(self.bot.config.ADMIN_BOT_COMMANDS_CHANNEL_ID)
            await ctx.respond(f"This command can only be used in {admin_channel.mention}.", ephemeral=True)
        # [MODIFIED] Catch the new, more specific role error.
        elif isinstance(error, NotBankManagerError):
            await ctx.respond("You do not have a required role to manage the clan bank.", ephemeral=True)
        elif isinstance(error, commands.CheckFailure):
            # Fallback for any other permission errors.
            await ctx.respond("You do not have permission to use this command.", ephemeral=True)
        else:
            # For any other errors, log them and send a generic message.
            print(f"An unhandled error occurred in a clanbank command: {error}")
            await ctx.respond("An unexpected error occurred. Please try again later.", ephemeral=True)


def setup(bot):
    """Called by Pycord to add the cog to the bot."""
    bot.add_cog(RS3Finances(bot))

