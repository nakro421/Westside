import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
from datetime import datetime, UTC
from dotenv import load_dotenv

# ================= SETUP =================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

BALLAS_ROLE_ID = 1481793788245704831
LEADER_ROLE_ID = 1481793788358819947

ABMELDE_KANAL_ID = 1478111622441598996

# ================= COUNTER =================
GUILD_ID = 1481793788245704826  
ROLE_COUNTER_ID = 1489217135530999938  

MEMBER_CHANNEL_ID = 1489217183572820108
BOT_CHANNEL_ID = 1489217212332904578
ROLE_CHANNEL_ID = 1489217322978639892


# =========================================

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= EVENTS =================
@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")

    # 👉 Counter starten
    if not update_stats.is_running():
        update_stats.start()

# ================= PING VIEW =================
class PingView(View):
    def __init__(self, members):
        super().__init__(timeout=None)
        self.members = members

    @discord.ui.button(label="Nicht reagierte Mitglieder pingen", style=discord.ButtonStyle.red)
    async def ping_button(self, interaction: discord.Interaction, button: Button):
        liste = "\n".join(f"• {m.mention}" for m in self.members)
        embed = discord.Embed(title="❌ Keine Reaktion", description=liste, color=0xE74C3C)
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Mitglieder gepingt.", ephemeral=True)

# ================= REAKTIONEN =================
@bot.tree.command(name="reaktionen_auswerten")
async def reaktionen(interaction: discord.Interaction, channel: discord.TextChannel, nachrichten_id: str):
    if LEADER_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("Keine Leader-Rechte.", ephemeral=True)

    message = await channel.fetch_message(int(nachrichten_id))
    reacted = set()
    for r in message.reactions:
        async for u in r.users():
            reacted.add(u)

    role = interaction.guild.get_role(BALLAS_ROLE_ID)
    not_reacted = [m for m in role.members if not m.bot and m not in reacted]

    await interaction.response.send_message(
        "Auswertung abgeschlossen.",
        ephemeral=True,
        view=PingView(not_reacted)
    )

# ================= ABMELDUNG =================
@bot.tree.command(name="abmelden")
async def abmelden(interaction: discord.Interaction, grund: str, dauer: str):
    embed = discord.Embed(title="General Lazkopat Abmeldung", color=0x8E44AD, timestamp=datetime.now(UTC))
    embed.add_field(name="Mitglied", value=interaction.user.mention)
    embed.add_field(name="Grund", value=grund)
    embed.add_field(name="Dauer", value=dauer)
    await bot.get_channel(ABMELDE_KANAL_ID).send(embed=embed)
    await interaction.response.send_message("Abmeldung eingetragen.", ephemeral=True)

# ================= CLEAR =================
@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, anzahl: int):
    if LEADER_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("Keine Leader-Rechte.", ephemeral=True)
    deleted = await interaction.channel.purge(limit=anzahl)
    await interaction.response.send_message(f"{len(deleted)} Nachrichten gelöscht.", ephemeral=True)
# ================= LOGGING =================

LOG_CHANNEL_ID = 1488558224553672875

def log_channel(guild):
    return guild.get_channel(LOG_CHANNEL_ID)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    embed = discord.Embed(title="🗑️ Nachricht gelöscht", color=0xE74C3C)
    embed.add_field(name="User", value=message.author.mention)
    embed.add_field(name="Text", value=message.content or "-")

    await log_channel(message.guild).send(embed=embed)


@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:
        return

    embed = discord.Embed(title="✏️ Nachricht bearbeitet", color=0xF1C40F)
    embed.add_field(name="Alt", value=before.content or "-")
    embed.add_field(name="Neu", value=after.content or "-")

    await log_channel(before.guild).send(embed=embed)


@bot.event
async def on_member_update(before, after):
    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added = after_roles - before_roles
    removed = before_roles - after_roles

    for role in added:
        embed = discord.Embed(title="➕ Rolle hinzugefügt", color=0x2ECC71)
        embed.add_field(name="User", value=after.mention)
        embed.add_field(name="Rolle", value=role.mention)
        await log_channel(after.guild).send(embed=embed)

    for role in removed:
        embed = discord.Embed(title="➖ Rolle entfernt", color=0xE67E22)
        embed.add_field(name="User", value=after.mention)
        embed.add_field(name="Rolle", value=role.mention)
        await log_channel(after.guild).send(embed=embed)


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

    if len(raid_tracker[member.guild.id]) >= RAID_LIMIT:
        await member.guild.ban(member, reason="Raid erkannt")

        embed = discord.Embed(title="🚨 RAID erkannt", color=0xC0392B)
        embed.description = f"{member.mention} wurde gebannt!"
        await log_channel(member.guild).send(embed=embed)
    else:
        embed = discord.Embed(title="📥 Beigetreten", color=0x2ECC71)
        embed.add_field(name="User", value=member.mention)
        await log_channel(member.guild).send(embed=embed)


@bot.event
async def on_member_remove(member):
    embed = discord.Embed(title="📤 User verlassen", color=0xE74C3C)
    embed.add_field(name="User", value=member.mention)
    await log_channel(member.guild).send(embed=embed)

from discord.ext import tasks

@tasks.loop(seconds=30)
async def update_stats():
    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        print("❌ Guild nicht gefunden")
        return

    await guild.chunk()

    members = guild.members

    total_members = len([m for m in members if not m.bot])
    bot_count = len([m for m in members if m.bot])
    role_count = len([m for m in members if any(r.id == ROLE_COUNTER_ID for r in m.roles)])

    try:
        member_channel = guild.get_channel(MEMBER_CHANNEL_ID)
        bot_channel = guild.get_channel(BOT_CHANNEL_ID)
        role_channel = guild.get_channel(ROLE_CHANNEL_ID)

        if member_channel:
            await member_channel.edit(name=f"👥 Mitglieder: {total_members}")

        if bot_channel:
            await bot_channel.edit(name=f"🤖 Bots: {bot_count}")

        if role_channel:
            await role_channel.edit(name=f"🎭 Ballas: {role_count}")

    except Exception as e:
        print("❌ Counter Fehler:", e)


@update_stats.before_loop
async def before_stats():
    await bot.wait_until_ready()
# ================= START =================
bot.run(TOKEN)
















