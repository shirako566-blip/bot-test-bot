import discord
from discord.ext import commands
import time
import os

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

afk_users = {}

# ================= READY =================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ================= FIXED MESSAGE HANDLER =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id

    # AFK return
    if uid in afk_users:
        afk_users.pop(uid)
        await message.channel.send(f"🟢 Welcome back {message.author.mention}")

    # AFK mention check
    for user in message.mentions:
        if user.id in afk_users:
            await message.channel.send(f"😴 {user.name} is AFK")

    await bot.process_commands(message)

# ================= CLEAN TEST COMMAND (NO EXTRA LINES) =================
@bot.command()
async def test(ctx):

    latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title="⚙️ Bot Status",
        color=discord.Color.green()
    )

    embed.add_field(name="Status", value="ONLINE 🟢", inline=True)
    embed.add_field(name="Ping", value=f"{latency}ms", inline=True)
    embed.add_field(name="AFK System", value="Active ✔", inline=True)
    embed.add_field(name="Shop System", value="Active ✔", inline=True)

    await ctx.send(embed=embed)

# ================= AFK =================
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = {"reason": reason, "time": time.time()}
    await ctx.send(f"😴 AFK set: {reason}")

# ================= PURGE =================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):

    if amount <= 0 or amount > 100:
        return await ctx.send("❌ 1–100 only")

    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {len(deleted)-1} messages", delete_after=5)

# ================= DM ALL =================
@bot.command()
@commands.has_permissions(administrator=True)
async def dmall(ctx, *, msg):

    sent = 0

    async for member in ctx.guild.fetch_members(limit=None):
        if not member.bot:
            try:
                await member.send(msg)
                sent += 1
            except:
                pass

    await ctx.send(f"📩 Sent to {sent} users")

# ================= SHOP =================
@bot.command()
async def shop(ctx):
    await ctx.send(
        "🛒 **SHOP SYSTEM**\n\n"
        "Use:\n"
        "`!buy <item> <price>`\n\n"
        "Example:\n"
        "`!buy Nitro 299`"
    )

# ================= BUY =================
@bot.command()
async def buy(ctx, item: str, price: int):

    embed = discord.Embed(
        title="💳 PAYMENT GATEWAY",
        description=f"🛍 {item}\n💰 ₹{price}",
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed, view=PaymentView(item, price))

# ================= PAYMENT SYSTEM =================
class PaymentView(discord.ui.View):
    def __init__(self, item, price):
        super().__init__()
        self.item = item
        self.price = price

    @discord.ui.button(label="📲 UPI", style=discord.ButtonStyle.success)
    async def upi(self, interaction, button):
        await self.pay(interaction, "UPI", "yourupi@okaxis")

    @discord.ui.button(label="🪙 Crypto", style=discord.ButtonStyle.primary)
    async def crypto(self, interaction, button):
        await self.pay(interaction, "CRYPTO", "wallet_address")

    @discord.ui.button(label="💠 LTC", style=discord.ButtonStyle.secondary)
    async def ltc(self, interaction, button):
        await self.pay(interaction, "LTC", "ltc_address")

    async def pay(self, interaction, method, details):

        embed = discord.Embed(
            title="💰 PAYMENT INFO",
            description=f"""
🛍 {self.item}
💰 ₹{self.price}

📌 Method: {method}
📍 {details}
""",
            color=discord.Color.orange()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

# ================= RUN =================
if TOKEN is None:
    raise RuntimeError("TOKEN not set")

bot.run(TOKEN)

