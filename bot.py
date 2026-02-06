import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime, UTC
from dotenv import load_dotenv

# ================= SETUP =================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

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

# ================= EVENTS =================
@bot.event
async def setup_hook():
    await bot.tree.sync()

@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")

# ================= PING VIEW =================
class PingView(View):
    def __init__(self, members_to_ping):
        super().__init__(timeout=None)
        self.members_to_ping = members_to_ping

    @discord.ui.button(
        label="Nicht reagierte Mitglieder pingen",
        style=discord.ButtonStyle.red
    )
    async def ping_button(self, interaction: discord.Interaction, button: Button):
        if not self.members_to_ping:
            await interaction.response.send_message(
                "Alle Mitglieder haben reagiert ✅",
                ephemeral=True
            )
            return

        liste = "\n".join(f"• {m.mention}" for m in self.members_to_ping)

        embed = discord.Embed(
            title="❌ Keine Reaktion erhalten",
            description=liste,
            color=0xE74C3C
        )
        embed.set_footer(
            text=f"Insgesamt: {len(self.members_to_ping)} Mitglieder"
        )

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(
            "Mitglieder wurden gepingt.",
            ephemeral=True
        )

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
        await interaction.response.send_message(
            "Keine Leader-Rechte.",
            ephemeral=True
        )
        return

    message = await channel.fetch_message(int(nachrichten_id))

    reacted_users = set()
    for reaction in message.reactions:
        async for user in reaction.users():
            reacted_users.add(user)

    ballas_role = interaction.guild.get_role(BALLAS_ROLE_ID)

    reagiert = []
    nicht_reagiert = []
    members_to_ping = []

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
        f"**Reagiert:**\n" + "\n".join(reagiert) +
        f"\n\n**Nicht reagiert:**\n" + "\n".join(nicht_reagiert),
        ephemeral=True,
        view=view
    )

# ================= ABMELDUNG =================
@bot.tree.command(name="abmelden", description="Ballas Dienstabmeldung")
@app_commands.describe(
    grund="Grund der Abmeldung",
    dauer="Wie lange du abgemeldet bist"
)
async def abmelden(
    interaction: discord.Interaction,
    grund: str,
    dauer: str
):
    if BALLAS_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message(
            "Keine Ballas-Rechte.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="Ballas Abmeldung",
        color=0x8E44AD,
        timestamp=datetime.now(UTC)
    )
    embed.add_field(
        name="Mitglied",
        value=interaction.user.mention,
        inline=False
    )
    embed.add_field(name="Grund", value=grund, inline=False)
    embed.add_field(name="Dauer", value=dauer, inline=False)

    channel = bot.get_channel(ABMELDE_KANAL_ID)
    await channel.send(embed=embed)

    rolle = interaction.guild.get_role(DIENST_ROLLE_ID)
    if rolle and rolle in interaction.user.roles:
        await interaction.user.remove_roles(rolle)

    await interaction.response.send_message(
        "Abmeldung eingetragen.",
        ephemeral=True
    )

# ================= CLEAR =================
@bot.tree.command(
    name="clear",
    description="Leader: Löscht bis zu 100 Nachrichten"
)
@app_commands.describe(
    anzahl="Anzahl der Nachrichten (max 100)"
)
async def clear(interaction: discord.Interaction, anzahl: int):
    if LEADER_ROLE_ID not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message(
            "Keine Leader-Rechte.",
            ephemeral=True
        )
        return

    if anzahl < 1 or anzahl > 100:
        await interaction.response.send_message(
            "Du kannst nur zwischen 1 und 100 Nachrichten löschen.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=anzahl)
    await interaction.followup.send(
        f"{len(deleted)} Nachrichten gelöscht.",
        ephemeral=True
    )

# ================= START =================
if __name__ == "__main__":
    bot.run(TOKEN)










