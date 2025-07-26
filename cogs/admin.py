import discord
from discord.ext import commands, tasks
from discord import Option
import datetime
import pytz
import json
import os
import asyncio

REMINDERS_FILE = 'reminders.json'

class admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.reminders = self._load_reminders()
        self.reminder_task.start()

    def _load_reminders(self):
        if os.path.exists(REMINDERS_FILE):
            try:
                with open(REMINDERS_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"[{datetime.datetime.now()}] Warning: {REMINDERS_FILE} is corrupted. Starting with empty list.")
        return []

    def _save_reminders(self):
        with open(REMINDERS_FILE, 'w') as f:
            json.dump(self.reminders, f, indent=4)

    def _user_is_admin(self, ctx):
        # Ensure RUNESCAPE_STAFF_ROLE_ID is correctly defined in your bot's config
        # and that ctx.author.roles is populated.
        return any(role.id == self.config.RUNESCAPE_STAFF_ROLE_ID for role in ctx.author.roles)

    @tasks.loop(minutes=1)
    async def reminder_task(self):
        await self.bot.wait_until_ready()

        current_time = int(datetime.datetime.now(pytz.utc).timestamp())
        reminders_to_remove = []
        for reminder in self.reminders:
            if current_time >= reminder["reminder_time"]:
                try:
                    channel = self.bot.get_channel(reminder["channel_id"])
                    if channel:
                        embed = discord.Embed(
                            title=f":bell: Reminder: {reminder['original_title']}",
                            description=reminder["message_content"],
                            color=discord.Color.orange()
                        )
                        embed.add_field(name="Event Time", value=f"<t:{reminder['reminder_time']}:F>", inline=False)
                        mention = f"<@&{reminder['role_id']}>" if reminder.get("role_id") else ""
                        await channel.send(content=mention, embed=embed)
                    reminders_to_remove.append(reminder)
                except Exception as e:
                    print(f"[{datetime.datetime.now()}] Reminder error for event ID {reminder.get('event_id', 'N/A')}: {e}")
                    reminders_to_remove.append(reminder)

        if reminders_to_remove:
            self.reminders = [r for r in self.reminders if r not in reminders_to_remove]
            self._save_reminders()

    @reminder_task.before_loop
    async def before_reminder_task(self):
        await self.bot.wait_until_ready()

    def date_to_epoch(self, date_string, time_string, timezone_string, date_format="%Y-%m-%d %H:%M:%S"):
        try:
            datetime_str = f"{date_string} {time_string}"
            naive_dt_object = datetime.datetime.strptime(datetime_str, date_format)
            local_timezone = pytz.timezone(timezone_string)
            aware_dt_object = local_timezone.localize(naive_dt_object)
            utc_dt_object = aware_dt_object.astimezone(pytz.utc)
            return int(utc_dt_object.timestamp()), utc_dt_object
        except Exception as e:
            print(f"Error converting date to epoch: {e}")
            return None, None

    @discord.slash_command(description="Creates an event with a voice channel.")
    async def event(self, ctx,
                      title: str,
                      date: str,
                      time: str,
                      timezone: str,
                      host: discord.Member,
                      description: str,
                      voice_channel: discord.VoiceChannel,
                      reminder1_minutes: Option(int, required=False) = None,
                      reminder2_minutes: Option(int, required=False) = None,
                      reminder_channel: Option(discord.TextChannel, required=False) = None,
                      mention_role: Option(discord.Role, required=False) = None):
        if not self._user_is_admin(ctx):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return

        event_epoch_time, event_datetime_utc = self.date_to_epoch(date, time, timezone)
        if not event_epoch_time or event_datetime_utc < datetime.datetime.now(pytz.utc):
            await ctx.respond("Invalid or past date/time. Please provide a future date/time.", ephemeral=True)
            return

        await ctx.defer() 

        embed = discord.Embed(
            title=":alarm_clock: Odin's Valhalla Event :alarm_clock:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Event Title", value=title, inline=False)
        embed.add_field(name="Time & Date", value=f"<t:{event_epoch_time}:F>", inline=False)
        embed.add_field(name="Voice Channel", value=voice_channel.mention, inline=False)
        embed.add_field(name="Host", value=host.mention, inline=False)
        embed.add_field(name="Description", value=description, inline=False)

        try:
            end_time = event_datetime_utc + datetime.timedelta(hours=1)
            
            # --- MODIFIED PART FOR OLDER PYCORD/DISCORD.PY VERSIONS ---
            # Removed entity_type and using 'location' with channel mention as fallback
            created_event = await ctx.guild.create_scheduled_event(
                name=title,
                description=description,
                start_time=event_datetime_utc,
                end_time=end_time,
                location=voice_channel.mention, # Using mention string for location
                reason=f"Event created by {ctx.author.name}"
            )
            # --- END MODIFIED PART ---

            embed.set_footer(text=f"Event ID: {created_event.id}")
            await ctx.followup.send(embed=embed) 

            reminder_channel_id = reminder_channel.id if reminder_channel else getattr(self.config, 'REMINDER_CHANNEL_ID', ctx.channel.id)
            role_id = mention_role.id if mention_role else None
            current_epoch = int(datetime.datetime.now(pytz.utc).timestamp())
            scheduled_reminders_count = 0

            for minutes in [reminder1_minutes, reminder2_minutes]:
                if minutes is not None and minutes > 0:
                    reminder_epoch = int((event_datetime_utc - datetime.timedelta(minutes=minutes)).timestamp())
                    if reminder_epoch > current_epoch:
                        self.reminders.append({
                            "event_id": created_event.id,
                            "reminder_time": reminder_epoch,
                            "channel_id": reminder_channel_id,
                            "message_content": f"'{title}' starts in {minutes} min!",
                            "original_title": title,
                            "role_id": role_id
                        })
                        scheduled_reminders_count += 1

            if scheduled_reminders_count > 0:
                self._save_reminders()
                await ctx.followup.send(f"Event created and {scheduled_reminders_count} reminder(s) scheduled in <#{reminder_channel_id}>.", ephemeral=True)
            else:
                await ctx.followup.send("Event created. No valid reminders were scheduled.", ephemeral=True)


        except discord.Forbidden:
            print(f"[{datetime.datetime.now()}] Missing permissions to create scheduled event or send messages.")
            await ctx.followup.send("I don't have permission to create scheduled events or send messages in the specified channel. Please check my role permissions.", ephemeral=True)
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Error creating scheduled event: {e}")
            await ctx.followup.send("An unexpected error occurred while creating the server event. Please try again or contact support.", ephemeral=True)

    @discord.slash_command(description="Cancels a scheduled event by its ID.")
    async def cancelevent(self, ctx, event_id: str):
        if not self._user_is_admin(ctx):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return

        try:
            event_id = int(event_id)
        except ValueError:
            await ctx.respond("Invalid event ID format. Please provide a numerical ID.", ephemeral=True)
            return

        scheduled_event = discord.utils.get(await ctx.guild.fetch_scheduled_events(), id=event_id)
        if not scheduled_event:
            await ctx.respond("Event not found in Discord's scheduled events.", ephemeral=True)
            return

        try:
            await scheduled_event.delete()
        except discord.Forbidden:
            print(f"[{datetime.datetime.now()}] Missing permissions to delete scheduled event ID {event_id}.")
            await ctx.respond("I don't have permission to cancel this scheduled event. Please check my role permissions.", ephemeral=True)
            return
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Error deleting event ID {event_id}: {e}")
            await ctx.respond("An unexpected error occurred while cancelling the event.", ephemeral=True)
            return

        original_count = len(self.reminders)
        self.reminders = [r for r in self.reminders if r['event_id'] != event_id]
        deleted_count = original_count - len(self.reminders)

        if deleted_count > 0:
            self._save_reminders()

        await ctx.respond(f"Event '{scheduled_event.name}' successfully canceled. {deleted_count} associated reminder(s) removed.", ephemeral=True)

def setup(bot):
    bot.add_cog(admin(bot))
