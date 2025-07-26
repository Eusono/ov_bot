# example.config.py

# Discord Bot Token
TOKEN = "YOUR_DISCORD_BOT_TOKEN"

# Guild (Server) ID the bot is scoped to
GUILD_ID = 123456789012345678  # Replace with your actual Discord server ID

# Channel IDs for functionality
THE_DOOR_CHANNEL_ID = 123456789012345678         # e.g., "The Door" welcome channel
RS3_GENERAL_CHAT_CHANNEL_ID = 123456789012345679 # RS3 general chat
CLAN_BANK_LOG_CHANNEL_ID = 123456789012345680    # Clan bank transaction log
ADMIN_BOT_COMMANDS_CHANNEL_ID = 123456789012345681  # Admin bot commands only

# Role IDs
RUNESCAPE_STAFF_ROLE_ID = 123456789012345682  # Used for role-based logic

# Roles allowed to use /clanbank add/remove
BANK_MANAGER_ROLE_IDS = [
    123456789012345682,  # 'Runescape Staff'
    123456789012345683,  # 'Discord Owners'
    123456789012345684,  # 'Discord Manager'
    123456789012345685,  # 'Clan Admin'
]

# Path to JSON file for clan bank data
# (Change this if running from a different path or locally)
BANK_FILE_PATH = '/opt/ovbot/clan_bank.json'
