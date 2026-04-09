import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime, UTC
from dotenv import load_dotenv

# ================= SETUP =================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ===== SERVER / ROLLEN / CHANNEL IDS =====
GUILD_ID = 1491834774921150464

BALLAS_ROLE_ID = 1491834774921150469
LEADER_ROLE_ID = 1491834774950641842
ROLE_COUNTER_ID = 1491850662873661541

ABMELDE_KANAL_ID = 1491834776557064315
LOG_CHANNEL_ID = 1491846127325155618

MEMBER_CHANNEL_ID = 1491850704669769728
BOT_CHANNEL_ID = 1491850735195918377
ROLE_CHANNEL_ID = 1491850780012187849

# =========================================

intents = discord.Intents.all()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= HILFSFUNKTION =================
def log_channel(guild: discord.Guild):
    return guild.get_channel(LOG_CHANNEL_ID)

# ================= EVENTS =================
@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash-Commands synchronisiert")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren der Commands: {e}")

    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print(f"❌ Guild mit ID {GUILD_ID} nicht gefunden")
    else:
        print(f"✅ Server gefunden: {guild.name} ({guild.id})")
        print("=== Rollen auf dem Server ===")
        for role in guild.roles:
            print(f"{role.name} -> {role.id}")

    if not update_stats.is_running():
        update_stats.start()

# ================= ERROR HANDLING =================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        try:
            return await interaction.response.send_message(
                f"⏳ Bitte warte {round(error.retry_after, 1)} Sekunden.",
                ephemeral=True
            )
        except:
            return

    elif isinstance(error, app_commands.errors.MissingPermissions):
        try:
            return await interaction.response.send_message(
                "❌ Du hast keine Rechte dafür.",
                ephemeral=True
            )
        except:
            return

    print(f"❌ Fehler bei {interaction.command.name if interaction.command else 'Unbekannt'}: {error}")

    try:
        log = log_channel(interaction.guild)
        if log:
            embed = discord.Embed(title="⚠️ Command Fehler", color=0xE74C3C)
            embed.add_field(name="Command", value=interaction.command.name if interaction.command else "Unbekannt", inline=False)
            embed.add_field(name="User", value=interaction.user.mention, inline=False)
            embed.add_field(name="Fehler", value=str(error), inline=False)
            await log.send(embed=embed)
    except:
        pass

    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ Es ist ein Fehler aufgetreten (wurde geloggt).",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "❌ Es ist ein Fehler aufgetreten (wurde geloggt).",
                ephemeral=True
            )
    except:
        pass

# ================= PING VIEW =================
class PingView(View):
    def __init__(self, members):
        super().__init__(timeout=None)
        self.members = members

    @discord.ui.button(label="Nicht reagierte Mitglieder pingen", style=discord.ButtonStyle.red)
    async def ping_button(self, interaction: discord.Interaction, button: Button):
        if not self.members:
            return await interaction.response.send_message(
                "✅ Alle Mitglieder haben reagiert.",
                ephemeral=True
            )

        liste = "\n".join(f"• {m.mention}" for m in self.members)
        embed = discord.Embed(
            title="❌ Keine Reaktion",
            description=liste,
            color=0xE74C3C
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Mitglieder gepingt.", ephemeral=True)

# ================= REAKTIONEN =================
@bot.tree.command(name="reaktionen_auswerten", description="Wertet Reaktionen auf eine Nachricht aus")
async def reaktionen(interaction: discord.Interaction, channel: discord.TextChannel, nachrichten_id: str):
    if LEADER_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Keine Leader-Rechte.", ephemeral=True)

    try:
        message = await channel.fetch_message(int(nachrichten_id))
    except Exception as e:
        return await interaction.response.send_message(f"❌ Nachricht nicht gefunden: {e}", ephemeral=True)

    reacted = set()
    for r in message.reactions:
        async for u in r.users():
            reacted.add(u)

    role = interaction.guild.get_role(BALLAS_ROLE_ID)
    if role is None:
        return await interaction.response.send_message("❌ BALLAS-Rolle nicht gefunden.", ephemeral=True)

    not_reacted = [m for m in role.members if not m.bot and m not in reacted]

    await interaction.response.send_message(
        f"✅ Auswertung abgeschlossen. Nicht reagiert: {len(not_reacted)}",
        ephemeral=True,
        view=PingView(not_reacted)
    )

# ================= ABMELDUNG =================
@bot.tree.command(name="abmelden", description="Meldet dich ab")
async def abmelden(interaction: discord.Interaction, grund: str, dauer: str):
    embed = discord.Embed(
        title="General Lazkopat Abmeldung",
        color=0x8E44AD,
        timestamp=datetime.now(UTC)
    )
    embed.add_field(name="Mitglied", value=interaction.user.mention, inline=False)
    embed.add_field(name="Grund", value=grund, inline=False)
    embed.add_field(name="Dauer", value=dauer, inline=False)

    channel = bot.get_channel(ABMELDE_KANAL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(ABMELDE_KANAL_ID)
        except Exception as e:
            return await interaction.response.send_message(f"❌ Abmelde-Kanal nicht gefunden: {e}", ephemeral=True)

    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Abmeldung eingetragen.", ephemeral=True)

# ================= CLEAR =================
@bot.tree.command(name="clear", description="Löscht Nachrichten")
async def clear(interaction: discord.Interaction, anzahl: int):
    if LEADER_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Keine Leader-Rechte.", ephemeral=True)

    if anzahl <= 0:
        return await interaction.response.send_message("❌ Bitte gib eine Zahl größer als 0 an.", ephemeral=True)

    deleted = await interaction.channel.purge(limit=anzahl)
    await interaction.response.send_message(f"✅ {len(deleted)} Nachrichten gelöscht.", ephemeral=True)

# ================= LOGGING =================
@bot.event
async def on_message_delete(message):
    if message.author.bot or message.guild is None:
        return

    log = log_channel(message.guild)
    if log is None:
        return

    embed = discord.Embed(title="🗑️ Nachricht gelöscht", color=0xE74C3C)
    embed.add_field(name="User", value=message.author.mention, inline=False)
    embed.add_field(name="Text", value=message.content or "-", inline=False)

    await log.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.guild is None or before.content == after.content:
        return

    log = log_channel(before.guild)
    if log is None:
        return

    embed = discord.Embed(title="✏️ Nachricht bearbeitet", color=0xF1C40F)
    embed.add_field(name="User", value=before.author.mention, inline=False)
    embed.add_field(name="Alt", value=before.content or "-", inline=False)
    embed.add_field(name="Neu", value=after.content or "-", inline=False)

    await log.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    if after.guild is None:
        return

    log = log_channel(after.guild)
    if log is None:
        return

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added = after_roles - before_roles
    removed = before_roles - after_roles

    for role in added:
        embed = discord.Embed(title="➕ Rolle hinzugefügt", color=0x2ECC71)
        embed.add_field(name="User", value=after.mention, inline=False)
        embed.add_field(name="Rolle", value=role.mention, inline=False)
        await log.send(embed=embed)

    for role in removed:
        embed = discord.Embed(title="➖ Rolle entfernt", color=0xE67E22)
        embed.add_field(name="User", value=after.mention, inline=False)
        embed.add_field(name="Rolle", value=role.mention, inline=False)
        await log.send(embed=embed)

# ================= ANTI RAID =================
raid_tracker = {}
RAID_LIMIT = 5
RAID_TIME = 10

@bot.event
async def on_member_join(member):
    now = datetime.now(UTC)

    if member.guild.id not in raid_tracker:
        raid_tracker[member.guild.id] = []

    raid_tracker[member.guild.id].append(now)
    raid_tracker[member.guild.id] = [
        t for t in raid_tracker[member.guild.id]
        if (now - t).total_seconds() < RAID_TIME
    ]

    log = log_channel(member.guild)

    if len(raid_tracker[member.guild.id]) >= RAID_LIMIT:
        await member.guild.ban(member, reason="Raid erkannt")

        if log:
            embed = discord.Embed(title="🚨 RAID erkannt", color=0xC0392B)
            embed.description = f"{member.mention} wurde gebannt!"
            await log.send(embed=embed)
    else:
        if log:
            embed = discord.Embed(title="📥 Beigetreten", color=0x2ECC71)
            embed.add_field(name="User", value=member.mention, inline=False)
            await log.send(embed=embed)

@bot.event
async def on_member_remove(member):
    if member.guild is None:
        return

    log = log_channel(member.guild)
    if log is None:
        return

    embed = discord.Embed(title="📤 User verlassen", color=0xE74C3C)
    embed.add_field(name="User", value=member.mention, inline=False)
    await log.send(embed=embed)

# ================= COUNTER =================
@tasks.loop(minutes=1)
async def update_stats():
    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        print(f"❌ Guild mit ID {GUILD_ID} nicht gefunden")
        return

    await guild.chunk()

    members = guild.members
    total_members = len([m for m in members if not m.bot])
    bot_count = len([m for m in members if m.bot])

    role = guild.get_role(ROLE_COUNTER_ID)

    if role is None:
        print(f"❌ Rolle mit ID {ROLE_COUNTER_ID} nicht gefunden")
        role_count = 0
        role_name = "Rolle"
    else:
        role_count = len(role.members)
        role_name = role.name
        print(f"✅ Rolle gefunden: {role.name} | Mitglieder: {role_count}")

    try:
        member_channel = guild.get_channel(MEMBER_CHANNEL_ID)
        bot_channel = guild.get_channel(BOT_CHANNEL_ID)
        role_channel = guild.get_channel(ROLE_CHANNEL_ID)

        if member_channel:
            await member_channel.edit(name=f"👥 Mitglieder: {total_members}")
        else:
            print(f"❌ Mitglieder-Channel mit ID {MEMBER_CHANNEL_ID} nicht gefunden")

        if bot_channel:
            await bot_channel.edit(name=f"🤖 Bots: {bot_count}")
        else:
            print(f"❌ Bot-Channel mit ID {BOT_CHANNEL_ID} nicht gefunden")

        if role_channel:
            await role_channel.edit(name=f"🎭 STRYX BLOCK 069: {role_count}")
        else:
            print(f"❌ Rollen-Channel mit ID {ROLE_CHANNEL_ID} nicht gefunden")

    except Exception as e:
        print("❌ Counter Fehler:", e)

@update_stats.before_loop
async def before_update_stats():
    await bot.wait_until_ready()

# ================= START =================
bot.run(TOKEN)
