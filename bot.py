import discord
from discord.ext import commands
import os

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= CONFIG (EDIT THIS) =================
UPI_ID = "yourupi@okaxis"
UPI_QR = "https://your-upi-qr.png"

USDT_ADDRESS = "your-usdt-wallet"
USDT_QR = "https://your-usdt-qr.png"

LTC_ADDRESS = "your-ltc-wallet"
LTC_QR = "https://your-ltc-qr.png"

LOG_CHANNEL_ID = 123456789012345678  # change this

# ================= DATA =================
orders = {}
afk_users = {}

# ================= READY =================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ================= MESSAGE HANDLER =================
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

# ================= HIGH-TECH TEST =================
@bot.command()
async def test(ctx):

    embed = discord.Embed(
        title="⚡ NEURAL SYSTEM STATUS",
        description="All systems operational",
        color=discord.Color.green()
    )

    embed.add_field(name="Status", value="ONLINE 🟢", inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency*1000)}ms", inline=True)
    embed.add_field(name="Shop Engine", value="ACTIVE ✔", inline=True)
    embed.add_field(name="Payment Core", value="ACTIVE ✔", inline=True)

    await ctx.send(embed=embed)

# ================= AFK =================
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = {"reason": reason}
    await ctx.send(f"😴 AFK set: {reason}")

# ================= SHOP ENTRY =================
@bot.command()
async def shop(ctx):
    await ctx.send(
        "🛒 **NEURAL SHOP SYSTEM**\n\n"
        "Use command:\n"
        "`!buy <item> <price>`\n\n"
        "Example:\n"
        "`!buy Nitro 299`"
    )

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
        title="💳 SECURE CHECKOUT",
        description=f"""
🛍 Item: **{item}**
💰 Price: **₹{price}**
🆔 Order ID: `{order_id}`

Select payment method:
""",
        color=discord.Color.purple()
    )

    await ctx.send(embed=embed, view=PaymentView(order_id))

# ================= PAYMENT VIEW =================
class PaymentView(discord.ui.View):
    def __init__(self, order_id):
        super().__init__()
        self.order_id = order_id

    @discord.ui.button(label="📲 UPI", style=discord.ButtonStyle.success)
    async def upi(self, interaction, button):
        await self.show(interaction, "UPI", UPI_ID, UPI_QR)

    @discord.ui.button(label="🪙 USDT", style=discord.ButtonStyle.primary)
    async def usdt(self, interaction, button):
        await self.show(interaction, "USDT (TRC20)", USDT_ADDRESS, USDT_QR)

    @discord.ui.button(label="💠 LTC", style=discord.ButtonStyle.secondary)
    async def ltc(self, interaction, button):
        await self.show(interaction, "LTC", LTC_ADDRESS, LTC_QR)

    async def show(self, interaction, method, address, qr):

        order = orders[self.order_id]

        embed = discord.Embed(
            title="⚡ PAYMENT GATEWAY",
            description=f"""
🛍 Item: **{order['item']}**
💰 Price: **₹{order['price']}**
📌 Method: **{method}**

📍 Address:
`{address}`

Scan QR below 👇
""",
            color=discord.Color.green()
        )

        embed.set_image(url=qr)

        await interaction.response.send_message(
            embed=embed,
            view=PaidView(self.order_id),
            ephemeral=True
        )

# ================= I PAID =================
class PaidView(discord.ui.View):
    def __init__(self, order_id):
        super().__init__()
        self.order_id = order_id

    @discord.ui.button(label="✅ I PAID", style=discord.ButtonStyle.primary)
    async def paid(self, interaction, button):

        orders[self.order_id]["status"] = "WAITING_CONFIRM"

        await interaction.response.send_message(
            "🧾 Payment submitted. Waiting for admin confirmation.",
            ephemeral=True
        )

# ================= CONFIRM ORDER =================
@bot.command()
@commands.has_permissions(administrator=True)
async def confirm(ctx, order_id: str):

    if order_id not in orders:
        return await ctx.send("❌ Invalid Order ID")

    order = orders[order_id]

    if order["status"] != "WAITING_CONFIRM":
        return await ctx.send("❌ Order not in payment waiting state")

    user = await bot.fetch_user(order["user"])

    invoice = discord.Embed(
        title="🧾 INVOICE RECEIPT",
        description=f"""
🆔 Order ID: {order_id}
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

    await ctx.send("✅ Order confirmed successfully")

# ================= RUN =================
if TOKEN is None:
    raise RuntimeError("TOKEN not set")

bot.run(TOKEN)

