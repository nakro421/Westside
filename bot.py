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

# ================= LANGWAFFEN PREISE =================

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

# ================= IDS =================

BALLAS_ROLE_ID = 1461730290626990232
LEADER_ROLE_ID = 1461730291004473512
DIENST_ROLLE_ID = 333333333333333333
ABMELDE_KANAL_ID = 1461730292569084070
KONFLIKT_KANAL_ID = 1461730292569084074
VIERH_KANAL_ID = 1461730292569084075
STREETFIGHT_KANAL_ID = 1461730292569084076

# ================= BOT =================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def setup_hook():
    await bot.tree.sync()

@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user}")

# ================= LANGWAFFEN SYSTEM =================

class LangwaffenSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=name, value=name)
            for name in LANGWAFFEN_PREISE.keys()
        ]

        super().__init__(
            placeholder="🔫 Langwaffen auswählen",
            min_values=1,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view = MengenView(self.values)
        await interaction.response.edit_message(view=view, embed=None)

class MengenView(View):
    def __init__(self, waffen):
        super().__init__(timeout=120)
        self.waffen = list(waffen)
        self.mengen = {w: 1 for w in self.waffen}
        self.index = 0

        self.add_item(MinusButton())
        self.add_item(PlusButton())
        self.add_item(WeiterButton())

class MinusButton(Button):
    def __init__(self):
        super().__init__(label="➖", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        view: MengenView = self.view
        waffe = view.waffen[view.index]
        if view.mengen[waffe] > 1:
            view.mengen[waffe] -= 1
        await update_embed(interaction, view)

class PlusButton(Button):
    def __init__(self):
        super().__init__(label="➕", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        view: MengenView = self.view
        waffe = view.waffen[view.index]
        view.mengen[waffe] += 1
        await update_embed(interaction, view)

class WeiterButton(Button):
    def __init__(self):
        super().__init__(label="Weiter ➡️", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        view: MengenView = self.view
        view.index += 1

        if view.index >= len(view.waffen):
            await show_summary(interaction, view)
        else:
            await update_embed(interaction, view)

async def update_embed(interaction, view):
    waffe = view.waffen[view.index]
    menge = view.mengen[waffe]
    preis = LANGWAFFEN_PREISE[waffe]

    embed = discord.Embed(
        title="🔢 Menge festlegen",
        description=(
            f"🔫 **{waffe}**\n\n"
            f"Menge: **{menge}**\n"
            f"Einzelpreis: {preis/1_000_000:.1f} Mio"
        ),
        color=0xF1C40F
    )

    await interaction.response.edit_message(embed=embed, view=view)

async def show_summary(interaction, view):
    gesamt = 0
    text = ""

    for waffe, menge in view.mengen.items():
        preis = LANGWAFFEN_PREISE[waffe] * menge
        gesamt += preis
        text += f"🔫 {waffe} × {menge} → {preis/1_000_000:.1f} Mio\n"

    embed = discord.Embed(
        title="🧾 Bestellung",
        description=text,
        color=0x2ECC71,
        timestamp=datetime.now(UTC)
    )

    embed.add_field(
        name="💰 Gesamtpreis",
        value=f"**{gesamt/1_000_000:.1f} Mio**",
        inline=False
    )

    await interaction.response.edit_message(embed=embed, view=None)

@bot.tree.command(name="langwaffen", description="Langwaffen auswählen & Preise berechnen")
async def langwaffen(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔫 Langwaffen Auswahl",
        description="Wähle eine oder mehrere Waffen aus",
        color=0x3498DB
    )

    view = View()
    view.add_item(LangwaffenSelect())

    await interaction.response.send_message(embed=embed, view=view)

# ================= BOT START =================

if __name__ == "__main__":
    bot.run(TOKEN)








