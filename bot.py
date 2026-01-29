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


if __name__ == "__main__":
    bot.run(TOKEN)
