import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime, UTC
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ===== IDs EINTRAGEN =====
BALLAS_ROLE_ID = 1461730290626990232
LEADER_ROLE_ID = 1461730291004473512
DIENST_ROLLE_ID = 333333333333333333
ABMELDE_KANAL_ID = 1461730292569084070
KONFLIKT_KANAL_ID = 1461730292569084074
VIERH_KANAL_ID = 1461730292569084075
STREETFIGHT_KANAL_ID = 1461730292569084076
# =========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ---------- RICHTIGES SYNC (kein Rate Limit) ----------
@bot.event
async def setup_hook():
    await bot.tree.sync()

@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user}")


# ================= PING BUTTON =================

class PingView(View):
    def __init__(self, members_to_ping):
        super().__init__(timeout=None)
        self.members_to_ping = members_to_ping

    @discord.ui.button(label="Nicht reagierte Mitglieder pingen", style=discord.ButtonStyle.red)
    async def ping_button(self, interaction: discord.Interaction, button: Button):
        mentions = " ".join(member.mention for member in self.members_to_ping)
        await interaction.channel.send(f"Keine Reaktion von: {mentions}")
        await interaction.response.send_message("Mitglieder wurden gepingt.", ephemeral=True)


# ================= REAKTIONEN AUSWERTEN =================

@bot.tree.command(
    name="reaktionen_auswerten",
    description="Leader: Zeigt wer reagiert hat und wer nicht"
)
@app_commands.describe(
    channel="Channel der Nachricht",
    nachrichten_id="ID der Nachricht"
)
async def reaktionen_auswerten(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    nachrichten_id: str
):

    if LEADER_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("Keine Leader-Rechte.", ephemeral=True)
        return

    message = await channel.fetch_message(int(nachrichten_id))

    reacted_users = set()
    for reaction in message.reactions:
        async for user in reaction.users():
            reacted_users.add(user)

    ballas_role = interaction.guild.get_role(BALLAS_ROLE_ID)

    reagiert, nicht_reagiert, members_to_ping = [], [], []

    for member in ballas_role.members:
        if member.bot:
            continue
        if member in reacted_users:
            reagiert.append(member.display_name)
        else:
            nicht_reagiert.append(member.display_name)
            members_to_ping.append(member)

    view = PingView(members_to_ping) if members_to_ping else None

    await interaction.response.send_message(
        f"Reagiert:\n" + "\n".join(reagiert) +
        f"\n\nNicht reagiert:\n" + "\n".join(nicht_reagiert),
        ephemeral=True,
        view=view
    )

# ================= ABMELDUNG =================

@bot.tree.command(name="abmelden", description="Ballas Dienstabmeldung")
@app_commands.describe(
    grund="Grund der Abmeldung",
    dauer="Wie lange du abgemeldet bist"
)
async def abmelden(interaction: discord.Interaction, grund: str, dauer: str):

    if BALLAS_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message("Keine Ballas-Rechte.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Ballas Abmeldung",
        color=0x8E44AD,
        timestamp=datetime.now(UTC)
    )

    embed.add_field(name="Mitglied", value=interaction.user.mention, inline=False)
    embed.add_field(name="Grund", value=grund, inline=False)
    embed.add_field(name="Dauer", value=dauer, inline=False)

    channel = bot.get_channel(ABMELDE_KANAL_ID)
    await channel.send(embed=embed)

    rolle = interaction.guild.get_role(DIENST_ROLLE_ID)
    if rolle and rolle in interaction.user.roles:
        await interaction.user.remove_roles(rolle)

    await interaction.response.send_message("Abmeldung eingetragen.", ephemeral=True)
# ================= KONFLIKT AUSFÜLLEN =================

@bot.tree.command(name="konflikt", description="Konflikt eintragen")
@app_commands.describe(
    gang1="Gang 1",
    gang2="Gang 2",
    baseraid1="Baseraid Punkte Gang 1",
    baseraid2="Baseraid Punkte Gang 2",
    street1="Streetfight Punkte Gang 1",
    street2="Streetfight Punkte Gang 2",
    forderung="Aktuelle Forderung"
)
async def konflikt(
    interaction: discord.Interaction,
    gang1: str,
    gang2: str,
    baseraid1: int,
    baseraid2: int,
    street1: int,
    street2: int,
    forderung: str
):
    if interaction.channel_id != KONFLIKT_KANAL_ID:
        await interaction.response.send_message("Nur im Konflikt-Channel nutzbar.", ephemeral=True)
        return

    gesamt1 = baseraid1 + street1
    gesamt2 = baseraid2 + street2

    embed = discord.Embed(title="Konflikt", color=0x8E44AD)
    embed.description = (
        f"**{gang1} VS {gang2}**\n\n"
        f"**Baseraid :** {gang1} = {baseraid1} VS {baseraid2} = {gang2}\n\n"
        f"**Streetfight :** {gang1} = {street1} VS {street2} = {gang2}\n\n"
        f"**Insgesamt :** {gang1} = {gesamt1} VS {gesamt2} = {gang2}\n\n"
        f"**Aktuelle Forderung :** {forderung}"
    )

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Konflikt eingetragen.", ephemeral=True)


# ================= 4H REGEL AUSFÜLLEN =================

@bot.tree.command(name="4hregel", description="4H Regel eintragen")
@app_commands.describe(
    gang1="Gang 1",
    gang2="Gang 2",
    wo="Ort",
    raus="Raus Grund",
    forderung="Forderung",
    stand="Stand"
)
async def vierhregel(
    interaction: discord.Interaction,
    gang1: str,
    gang2: str,
    wo: str,
    raus: str,
    forderung: str,
    stand: str
):
    if interaction.channel_id != VIERH_KANAL_ID:
        await interaction.response.send_message("Nur im 4h-regel Channel nutzbar.", ephemeral=True)
        return

    embed = discord.Embed(title="4H Regel", color=0x8E44AD)
    embed.description = (
        f"**{gang1} VS {gang2}**\n\n"
        f"**Wo:** {wo}\n\n"
        f"**Raus:** {raus}\n\n"
        f"**Forderung:** {forderung}\n\n"
        f"**Stand:** {stand}"
    )

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("4H Regel eingetragen.", ephemeral=True)


# ================= STREETFIGHT AUSFÜLLEN =================

@bot.tree.command(name="streetfight", description="Streetfight eintragen")
@app_commands.describe(
    gang1="Gang 1",
    gang2="Gang 2",
    wo="Ort",
    forderung="Forderung",
    werfen="Mit oder ohne Werfen",
    stand="Stand"
)
async def streetfight(
    interaction: discord.Interaction,
    gang1: str,
    gang2: str,
    wo: str,
    forderung: str,
    werfen: str,
    stand: str
):
    if interaction.channel_id != STREETFIGHT_KANAL_ID:
        await interaction.response.send_message("Nur im Streetfight-Channel nutzbar.", ephemeral=True)
        return

    embed = discord.Embed(title="Streetfight", color=0x8E44AD)
    embed.description = (
        f"**{gang1} VS {gang2}**\n\n"
        f"**Wo:** {wo}\n\n"
        f"**Forderung:** {forderung}\n\n"
        f"**Mit oder ohne Werfen:** {werfen}\n\n"
        f"**Stand:** {stand}"
    )

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Streetfight eingetragen.", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)



