import os
import asyncio
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

ABMELDE_KANAL_ID = 1491834776557064315
LOG_CHANNEL_ID = 1491846127325155618

MEMBER_CHANNEL_ID = 1491850704669769728
BOT_CHANNEL_ID = 1491850735195918377
ROLE_CHANNEL_ID = 1491850780012187849

ANKUENDIGUNG_CHANNEL_ID = 1491834776343281727
AKTI_CHECK_CHANNEL_ID = 1491834776343281731

REACTION_CHECK_CHANNEL_IDS = [
    ANKUENDIGUNG_CHANNEL_ID,
    AKTI_CHECK_CHANNEL_ID
]
# =========================================

intents = discord.Intents.all()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= HILFSFUNKTIONEN =================
def log_channel(guild: discord.Guild):
    return guild.get_channel(LOG_CHANNEL_ID)

def format_duration(delta):
    total_seconds = int(delta.total_seconds())

    tage = total_seconds // 86400
    stunden = (total_seconds % 86400) // 3600
    minuten = (total_seconds % 3600) // 60

    teile = []
    if tage > 0:
        teile.append(f"{tage} Tag{'e' if tage != 1 else ''}")
    if stunden > 0:
        teile.append(f"{stunden} Stunde{'n' if stunden != 1 else ''}")
    if minuten > 0 or not teile:
        teile.append(f"{minuten} Minute{'n' if minuten != 1 else ''}")

    return ", ".join(teile)

async def get_audit_entry(guild: discord.Guild, action: discord.AuditLogAction, target_id: int = None):
    try:
        async for entry in guild.audit_logs(limit=10, action=action):
            if target_id is None:
                return entry

            target = entry.target
            if target and hasattr(target, "id") and target.id == target_id:
                delta = datetime.now(UTC) - entry.created_at
                if delta.total_seconds() <= 10:
                    return entry
    except Exception as e:
        print(f"❌ Audit-Log Fehler: {e}")
    return None

async def build_last_leader_reaction_map(
    guild: discord.Guild,
    limit_per_channel: int = 100
):
    leader_role = guild.get_role(LEADER_ROLE_ID)
    if leader_role is None:
        return {}

    leader_ids = {m.id for m in leader_role.members if not m.bot}
    latest_by_user = {}

    for channel_id in REACTION_CHECK_CHANNEL_IDS:
        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(channel_id)
            except Exception:
                continue

        if not isinstance(channel, discord.TextChannel):
            continue

        try:
            async for message in channel.history(limit=limit_per_channel):
                if message.author.bot:
                    continue

                if message.author.id not in leader_ids:
                    continue

                if not message.reactions:
                    continue

                reacted_user_ids = set()

                for reaction in message.reactions:
                    async for user in reaction.users():
                        if not user.bot:
                            reacted_user_ids.add(user.id)

                for user_id in reacted_user_ids:
                    old_msg = latest_by_user.get(user_id)
                    if old_msg is None or message.created_at > old_msg.created_at:
                        latest_by_user[user_id] = message

        except discord.Forbidden:
            print(f"❌ Keine Rechte für Kanal: {getattr(channel, 'name', channel_id)}")
            continue
        except discord.HTTPException as e:
            print(f"❌ HTTP-Fehler in Kanal {getattr(channel, 'name', channel_id)}: {e}")
            continue
        except Exception as e:
            print(f"❌ Fehler in {getattr(channel, 'name', channel_id)}: {e}")
            continue

    return latest_by_user

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
        except Exception:
            return

    elif isinstance(error, app_commands.errors.MissingPermissions):
        try:
            return await interaction.response.send_message(
                "❌ Du hast keine Rechte dafür.",
                ephemeral=True
            )
        except Exception:
            return

    print(f"❌ Fehler bei {interaction.command.name if interaction.command else 'Unbekannt'}: {error}")

    try:
        log = log_channel(interaction.guild)
        if log:
            embed = discord.Embed(title="⚠️ Command Fehler", color=0xE74C3C)
            embed.add_field(
                name="Command",
                value=interaction.command.name if interaction.command else "Unbekannt",
                inline=False
            )
            embed.add_field(name="User", value=interaction.user.mention, inline=False)
            embed.add_field(name="Fehler", value=str(error), inline=False)
            await log.send(embed=embed)
    except Exception:
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
    except Exception:
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
            description=liste[:4096],
            color=0xE74C3C
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Mitglieder gepingt.", ephemeral=True)

# ================= REAKTIONEN =================
@bot.tree.command(name="reaktionen_auswerten", description="Wertet Reaktionen auf eine Nachricht aus")
async def reaktionen(interaction: discord.Interaction, channel: discord.TextChannel, nachrichten_id: str):
    if LEADER_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("❌ Keine Leader-Rechte.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    try:
        message = await channel.fetch_message(int(nachrichten_id))
    except Exception as e:
        return await interaction.followup.send(f"❌ Nachricht nicht gefunden: {e}", ephemeral=True)

    reacted_ids = set()
    for reaction in message.reactions:
        async for user in reaction.users():
            reacted_ids.add(user.id)

    role = interaction.guild.get_role(BALLAS_ROLE_ID)
    if role is None:
        return await interaction.followup.send("❌ BALLAS-Rolle nicht gefunden.", ephemeral=True)

    not_reacted = [m for m in role.members if not m.bot and m.id not in reacted_ids]
    now = datetime.now(UTC)

    if not not_reacted:
        embed = discord.Embed(
            title="✅ Reaktionsauswertung abgeschlossen",
            description="Alle Mitglieder haben auf diese Nachricht reagiert.",
            color=0x2ECC71
        )
        embed.add_field(name="Nachricht", value=f"[Zur Nachricht springen]({message.jump_url})", inline=False)

        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
            view=PingView(not_reacted)
        )
        return

    last_reaction_map = await build_last_leader_reaction_map(interaction.guild, limit_per_channel=100)

    lines = []
    for member in not_reacted:
        last_msg = last_reaction_map.get(member.id)

        if last_msg is None:
            status = "❌ noch nie auf Leader-Nachricht in #ankündigung oder #akti-check reagiert"
        else:
            delta = now - last_msg.created_at
            status = f"🕒 zuletzt reagiert vor {format_duration(delta)} in {last_msg.channel.mention}"

        line = f"• {member.mention} — {status}"

        if len("\n".join(lines + [line])) > 3800:
            lines.append("• ... weitere Mitglieder konnten wegen Discord-Limit nicht angezeigt werden")
            break

        lines.append(line)

    embed = discord.Embed(
        title="📊 Reaktionsauswertung",
        description="\n".join(lines),
        color=0xE67E22
    )
    embed.add_field(name="Nachricht", value=f"[Zur Nachricht springen]({message.jump_url})", inline=False)
    embed.add_field(name="Nicht reagiert", value=str(len(not_reacted)), inline=False)

    await interaction.followup.send(
        embed=embed,
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

    await interaction.response.defer(ephemeral=True)

    try:
        deleted = await interaction.channel.purge(limit=anzahl)
        await interaction.followup.send(f"✅ {len(deleted)} Nachrichten gelöscht.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Fehler beim Löschen: {e}", ephemeral=True)

# ================= LOGGING =================
@bot.event
async def on_message_delete(message):
    if message.guild is None:
        return

    log = log_channel(message.guild)
    if log is None:
        return

    deleter = "Unbekannt"
    try:
        await asyncio.sleep(1)
        entry = await get_audit_entry(
            message.guild,
            discord.AuditLogAction.message_delete,
            message.author.id if message.author else None
        )
        if entry:
            deleter = entry.user.mention
    except Exception:
        pass

    embed = discord.Embed(title="🗑️ Nachricht gelöscht", color=0xE74C3C)
    embed.add_field(name="Autor", value=message.author.mention if message.author else "Unbekannt", inline=False)
    embed.add_field(name="Gelöscht von", value=deleter, inline=False)
    embed.add_field(name="Kanal", value=message.channel.mention, inline=False)
    embed.add_field(name="Text", value=message.content if message.content else "-", inline=False)

    if message.attachments:
        dateien = "\n".join(a.url for a in message.attachments)
        embed.add_field(name="Anhänge", value=dateien[:1024], inline=False)

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
    embed.add_field(name="Kanal", value=before.channel.mention, inline=False)

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

    if before.nick != after.nick:
        embed = discord.Embed(title="✏️ Nickname geändert", color=0x3498DB)
        embed.add_field(name="User", value=after.mention, inline=False)
        embed.add_field(name="Alt", value=before.nick or before.name, inline=False)
        embed.add_field(name="Neu", value=after.nick or after.name, inline=False)
        await log.send(embed=embed)

    if before.timed_out_until != after.timed_out_until:
        await asyncio.sleep(1)
        entry = await get_audit_entry(after.guild, discord.AuditLogAction.member_update, after.id)
        moderator = entry.user.mention if entry else "Unbekannt"

        if after.timed_out_until and (after.timed_out_until > datetime.now(UTC)):
            embed = discord.Embed(title="🔇 Timeout gesetzt", color=0x9B59B6)
            embed.add_field(name="User", value=after.mention, inline=False)
            embed.add_field(name="Von", value=moderator, inline=False)
            embed.add_field(name="Bis", value=discord.utils.format_dt(after.timed_out_until, style="F"), inline=False)
        else:
            embed = discord.Embed(title="🔊 Timeout entfernt", color=0x2ECC71)
            embed.add_field(name="User", value=after.mention, inline=False)
            embed.add_field(name="Von", value=moderator, inline=False)

        await log.send(embed=embed)

@bot.event
async def on_member_join(member):
    now = datetime.now(UTC)

    global raid_tracker
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
            embed.add_field(name="Account erstellt", value=discord.utils.format_dt(member.created_at, style="F"), inline=False)
            await log.send(embed=embed)

@bot.event
async def on_member_remove(member):
    if member.guild is None:
        return

    log = log_channel(member.guild)
    if log is None:
        return

    await asyncio.sleep(1)

    kick_entry = await get_audit_entry(member.guild, discord.AuditLogAction.kick, member.id)

    if kick_entry:
        embed = discord.Embed(title="👢 Mitglied gekickt", color=0xE67E22)
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Gekickt von", value=kick_entry.user.mention, inline=False)
        embed.add_field(name="Grund", value=kick_entry.reason or "Kein Grund angegeben", inline=False)
    else:
        embed = discord.Embed(title="📤 User verlassen", color=0xE74C3C)
        embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)

    await log.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    log = log_channel(guild)
    if log is None:
        return

    await asyncio.sleep(1)
    entry = await get_audit_entry(guild, discord.AuditLogAction.ban, user.id)

    embed = discord.Embed(title="🔨 User gebannt", color=0xC0392B)
    embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)

    if entry:
        embed.add_field(name="Gebannt von", value=entry.user.mention, inline=False)
        embed.add_field(name="Grund", value=entry.reason or "Kein Grund angegeben", inline=False)

    await log.send(embed=embed)

@bot.event
async def on_member_unban(guild, user):
    log = log_channel(guild)
    if log is None:
        return

    await asyncio.sleep(1)
    entry = await get_audit_entry(guild, discord.AuditLogAction.unban, user.id)

    embed = discord.Embed(title="✅ User entbannt", color=0x2ECC71)
    embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)

    if entry:
        embed.add_field(name="Entbannt von", value=entry.user.mention, inline=False)
        embed.add_field(name="Grund", value=entry.reason or "Kein Grund angegeben", inline=False)

    await log.send(embed=embed)

@bot.event
async def on_guild_channel_create(channel):
    log = log_channel(channel.guild)
    if log is None:
        return

    embed = discord.Embed(title="📁 Kanal erstellt", color=0x2ECC71)
    embed.add_field(name="Name", value=channel.name, inline=False)
    embed.add_field(name="ID", value=str(channel.id), inline=False)
    await log.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel):
    log = log_channel(channel.guild)
    if log is None:
        return

    embed = discord.Embed(title="🗑️ Kanal gelöscht", color=0xE74C3C)
    embed.add_field(name="Name", value=channel.name, inline=False)
    embed.add_field(name="ID", value=str(channel.id), inline=False)
    await log.send(embed=embed)

@bot.event
async def on_guild_channel_update(before, after):
    log = log_channel(after.guild)
    if log is None:
        return

    if before.name != after.name:
        embed = discord.Embed(title="✏️ Kanal umbenannt", color=0xF1C40F)
        embed.add_field(name="Alt", value=before.name, inline=False)
        embed.add_field(name="Neu", value=after.name, inline=False)
        embed.add_field(name="ID", value=str(after.id), inline=False)
        await log.send(embed=embed)

@bot.event
async def on_guild_role_create(role):
    log = log_channel(role.guild)
    if log is None:
        return

    embed = discord.Embed(title="🆕 Rolle erstellt", color=0x2ECC71)
    embed.add_field(name="Rolle", value=role.name, inline=False)
    embed.add_field(name="ID", value=str(role.id), inline=False)
    await log.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
    log = log_channel(role.guild)
    if log is None:
        return

    embed = discord.Embed(title="🗑️ Rolle gelöscht", color=0xE74C3C)
    embed.add_field(name="Rolle", value=role.name, inline=False)
    embed.add_field(name="ID", value=str(role.id), inline=False)
    await log.send(embed=embed)

# ================= ANTI RAID =================
raid_tracker = {}
RAID_LIMIT = 5
RAID_TIME = 10

# ================= COUNTER =================
@tasks.loop(minutes=1)
async def update_stats():
    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        print(f"❌ Guild mit ID {GUILD_ID} nicht gefunden")
        return

    try:
        await guild.chunk()
    except Exception as e:
        print(f"❌ Fehler beim Laden der Mitglieder: {e}")

    members = guild.members

    total_members = len([m for m in members if not m.bot])
    bot_count = len([m for m in members if m.bot])

    role = guild.get_role(BALLAS_ROLE_ID)

    if role is None:
        print(f"❌ Rolle mit ID {BALLAS_ROLE_ID} nicht gefunden")
        role_count = 0
    else:
        role_count = len([
            m for m in members
            if not m.bot and any(r.id == BALLAS_ROLE_ID for r in m.roles)
        ])
        print(f"✅ STRYX BLOCK 069 Mitglieder: {role_count}")

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
