import discord
from discord.ext import commands
import time
import os

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")

# ================= CONFIG =================
UPI_ID = "yourupi@okaxis"
QR_IMAGE_URL = "https://your-qr-image-link.png"
LOG_CHANNEL_ID = 123456789012345678  # change this

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

afk_users = {}
orders = {}

# ================= READY =================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ================= FIX MESSAGE HANDLER =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id

    if uid in afk_users:
        afk_users.pop(uid)
        await message.channel.send(f"🟢 Welcome back {message.author.mention}")

    for user in message.mentions:
        if user.id in afk_users:
            await message.channel.send(f"😴 {user.name} is AFK")

    await bot.process_commands(message)

# ================= TEST =================
@bot.command()
async def test(ctx):

    latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title="⚙️ SYSTEM STATUS",
        color=discord.Color.green()
    )

    embed.add_field(name="Status", value="ONLINE 🟢", inline=True)
    embed.add_field(name="Ping", value=f"{latency}ms", inline=True)
    embed.add_field(name="Shop", value="ACTIVE ✔", inline=True)
    embed.add_field(name="AFK", value="ACTIVE ✔", inline=True)

    await ctx.send(embed=embed)

# ================= AFK =================
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = {"reason": reason}
    await ctx.send(f"😴 AFK set: {reason}")

# ================= PURGE =================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):

    if amount < 1 or amount > 100:
        return await ctx.send("❌ 1–100 only")

    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {len(deleted)-1}", delete_after=5)

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

# ================= BUY COMMAND =================
@bot.command()
async def buy(ctx, item: str, price: int):

    order_id = str(len(orders) + 1)

    orders[order_id] = {
        "user": ctx.author.id,
        "item": item,
        "price": price,
        "status": "PENDING"
    }

    embed = discord.Embed(
        title="💳 CHECKOUT",
        description=f"""
🛍 Item: **{item}**
💰 Price: **₹{price}**

Choose payment method below:
""",
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed, view=PaymentView(order_id))

# ================= PAYMENT VIEW =================
class PaymentView(discord.ui.View):
    def __init__(self, order_id):
        super().__init__()
        self.order_id = order_id

    @discord.ui.button(label="📲 UPI", style=discord.ButtonStyle.success)
    async def upi(self, interaction, button):

        order = orders[self.order_id]

        embed = discord.Embed(
            title="📲 UPI PAYMENT",
            description=f"""
🛍 Item: **{order['item']}**
💰 Price: ₹{order['price']}

📌 UPI ID: `{UPI_ID}`
📷 Scan QR below
""",
            color=discord.Color.green()
        )

        embed.set_image(url=QR_IMAGE_URL)

        await interaction.response.send_message(
            embed=embed,
            view=PaidView(self.order_id),
            ephemeral=True
        )

    @discord.ui.button(label="🪙 Crypto", style=discord.ButtonStyle.primary)
    async def crypto(self, interaction, button):

        await interaction.response.send_message(
            "🪙 Send Crypto manually (address not set)",
            ephemeral=True
        )

    @discord.ui.button(label="💠 LTC", style=discord.ButtonStyle.secondary)
    async def ltc(self, interaction, button):

        await interaction.response.send_message(
            "💠 LTC address not set",
            ephemeral=True
        )

# ================= PAID BUTTON =================
class PaidView(discord.ui.View):
    def __init__(self, order_id):
        super().__init__()
        self.order_id = order_id

    @discord.ui.button(label="✅ I Paid", style=discord.ButtonStyle.primary)
    async def paid(self, interaction, button):

        orders[self.order_id]["status"] = "WAITING_CONFIRM"

        await interaction.response.send_message(
            "🧾 Payment submitted! Waiting for admin confirmation.",
            ephemeral=True
        )

# ================= CONFIRM ORDER =================
@bot.command()
@commands.has_permissions(administrator=True)
async def confirm(ctx, order_id: str):

    if order_id not in orders:
        return await ctx.send("❌ Invalid order ID")

    order = orders[order_id]
    user = await bot.fetch_user(order["user"])

    invoice = discord.Embed(
        title="🧾 INVOICE RECEIPT",
        description=f"""
🆔 Order: {order_id}
🛍 Item: {order['item']}
💰 Price: ₹{order['price']}
📌 Status: CONFIRMED ✅
""",
        color=discord.Color.gold()
    )

    # DM USER
    await user.send(embed=invoice)

    # LOG CHANNEL
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=invoice)

    order["status"] = "CONFIRMED"

    await ctx.send("✅ Order confirmed")

# ================= RUN =================
if TOKEN is None:
    raise RuntimeError("TOKEN not set")

bot.run(TOKEN)

