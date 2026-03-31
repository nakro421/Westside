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
ABMELDE_KANAL_ID = 1481793789902192796

# =========================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= EVENTS =================
@bot.event
async def setup_hook():
    await bot.tree.sync()

@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")

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

# ================= START =================
bot.run(TOKEN)
















