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
DIENST_ROLLE_ID = 333333333333333333
NULLSECHSNEUN_ROLE_ID = 1481793788245704831
LEADER_ROLLE = 1481793788358819947

ABMELDE_KANAL_ID = 1478111622441598996
ABMELDE_KANAL_ID = 1481793789902192796
KONFLIKT_KANAL_ID = 1461730292569084074
VIERH_KANAL_ID = 1461730292569084075
STREETFIGHT_KANAL_ID = 1461730292569084076
# =========================================

# ================= WAFFEN PREISE =================
LANGWAFFEN_PREISE = {
    "SPEZI MK2": 15_000_000,
    "SPEZI": 10_000_000,
    "KARABINER MK2": 10_000_000,
    "KARABINER": 5_000_000,
    "BULLPUP GEWEHR": 2_100_000,
    "BULLPUP GEWEHR MK1": 1_000_000,
    "ADV": 1_500_000,
    "AK MK2": 2_000_000,
    "AK": 1_000_000
}

KURZWAFFEN_PREISE = {
    "Gusenberg": 5_000_000,
    "Billardkö": 2_300_000,
    "Baseballschläger": 750_000,
    "Brechstange": 1_300_000,
    "Golfschläger": 1_700_000,
    "Axt": 2_700_000,
    "Battle Axt": 15_000_000,
    "Machete": 2_300_000,
    "Zuckerstange": 3_700_000,
    "Hammer": 2_500_000,
    "Messer": 1_500_000,
    "Flasche": 10_000_000,
    "Sägepistole": 750_000,
    "Schwere Pistole": 900_000,
    "Keramik Pistole": 1_700_000,
    "Dolch": 2_300_000,
    "Schlagring": 1_300_000,
    "Klappmesser": 2_300_000,
    "Goldener Revolver": 4_800_000,
    "Navy Revolver": 6_000_000,
    "Revolver MK2": 5_800_000,
    "MP MK2": 5_000_000
}
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

# ================= KONFLIKT =================
@bot.tree.command(name="konflikt")
async def konflikt(interaction: discord.Interaction, gang1: str, gang2: str,
                   baseraid1: int, baseraid2: int, street1: int, street2: int, forderung: str):
    if interaction.channel_id != KONFLIKT_KANAL_ID:
        return await interaction.response.send_message("Falscher Channel.", ephemeral=True)

    embed = discord.Embed(title="⚔️ Konflikt", color=0x8E44AD)
    embed.description = (
        f"{gang1} vs {gang2}\n\n"
        f"Baseraid: {baseraid1} : {baseraid2}\n"
        f"Streetfight: {street1} : {street2}\n\n"
        f"Forderung: {forderung}"
    )
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Konflikt eingetragen.", ephemeral=True)

# ================= 4H REGEL =================
@bot.tree.command(name="vierhregel")
async def vierhregel(interaction: discord.Interaction, gang1: str, gang2: str,
                     wo: str, raus: str, forderung: str, stand: str):
    if interaction.channel_id != VIERH_KANAL_ID:
        return await interaction.response.send_message("Falscher Channel.", ephemeral=True)

    embed = discord.Embed(title="⏱️ 4H Regel", color=0x8E44AD)
    embed.description = (
        f"{gang1} vs {gang2}\n\n"
        f"Ort: {wo}\n"
        f"Raus: {raus}\n"
        f"Forderung: {forderung}\n"
        f"Stand: {stand}"
    )
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("4H Regel eingetragen.", ephemeral=True)

# ================= STREETFIGHT =================
@bot.tree.command(name="streetfight")
async def streetfight(interaction: discord.Interaction, gang1: str, gang2: str,
                      wo: str, forderung: str, werfen: str, stand: str):
    if interaction.channel_id != STREETFIGHT_KANAL_ID:
        return await interaction.response.send_message("Falscher Channel.", ephemeral=True)

    embed = discord.Embed(title="🥊 Streetfight", color=0x8E44AD)
    embed.description = (
        f"{gang1} vs {gang2}\n\n"
        f"Ort: {wo}\n"
        f"Forderung: {forderung}\n"
        f"Werfen: {werfen}\n"
        f"Stand: {stand}"
    )
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Streetfight eingetragen.", ephemeral=True)

# ================= CLEAR =================
@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, anzahl: int):
    if LEADER_ROLE_ID not in [r.id for r in interaction.user.roles]:
        return await interaction.response.send_message("Keine Leader-Rechte.", ephemeral=True)
    deleted = await interaction.channel.purge(limit=anzahl)
    await interaction.response.send_message(f"{len(deleted)} Nachrichten gelöscht.", ephemeral=True)

# ================= WAFFENSYSTEM =================
class WaffenSelect(Select):
    def __init__(self, preise):
        self.preise = preise
        super().__init__(
            placeholder="Waffen auswählen",
            min_values=1,
            max_values=len(preise),
            options=[discord.SelectOption(label=w) for w in preise]
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=None,
            view=MengenView(self.values, self.preise)
        )

class MengenView(View):
    def __init__(self, waffen, preise):
        super().__init__(timeout=120)
        self.waffen = list(waffen)
        self.preise = preise
        self.mengen = {w: 1 for w in self.waffen}
        self.index = 0
        self.add_item(Minus())
        self.add_item(Plus())
        self.add_item(Weiter())

class Minus(Button):
    def __init__(self): super().__init__(label="➖", style=discord.ButtonStyle.red)
    async def callback(self, interaction):
        v = self.view
        if v.mengen[v.waffen[v.index]] > 1:
            v.mengen[v.waffen[v.index]] -= 1
        await update(interaction, v)

class Plus(Button):
    def __init__(self): super().__init__(label="➕", style=discord.ButtonStyle.green)
    async def callback(self, interaction):
        v = self.view
        v.mengen[v.waffen[v.index]] += 1
        await update(interaction, v)

class Weiter(Button):
    def __init__(self): super().__init__(label="Weiter ➡️", style=discord.ButtonStyle.blurple)
    async def callback(self, interaction):
        v = self.view
        v.index += 1
        if v.index >= len(v.waffen):
            await summary(interaction, v)
        else:
            await update(interaction, v)

async def update(interaction, v):
    w = v.waffen[v.index]
    embed = discord.Embed(
        title="Menge festlegen",
        description=f"{w}\nMenge: {v.mengen[w]}",
        color=0xF1C40F
    )
    await interaction.response.edit_message(embed=embed, view=v)

async def summary(interaction, v):
    total = sum(v.preise[w]*m for w,m in v.mengen.items())
    text = "\n".join(f"{w} × {m}" for w,m in v.mengen.items())
    embed = discord.Embed(title="🧾 Bestellung", description=text)
    embed.add_field(name="Gesamt", value=f"{total/1_000_000:.1f} Mio")
    await interaction.response.edit_message(embed=embed, view=None)

@bot.tree.command(name="langwaffen")
async def langwaffen(interaction: discord.Interaction):
    v = View()
    v.add_item(WaffenSelect(LANGWAFFEN_PREISE))
    await interaction.response.send_message("Langwaffen auswählen:", view=v)

@bot.tree.command(name="kurzwaffen")
async def kurzwaffen(interaction: discord.Interaction):
    v = View()
    v.add_item(WaffenSelect(KURZWAFFEN_PREISE))
    await interaction.response.send_message("Kurzwaffen auswählen:", view=v)

# ================= START =================
bot.run(TOKEN)
















