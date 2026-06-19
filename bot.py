import discord
from discord.ext import commands
import time
import os

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")

# ================= INTENTS =================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

afk_users = {}

# ================= SHOP DATA =================
shop_items = {
    "1": {"name": "Premium Access", "price": "199", "desc": "Lifetime Premium Role"},
    "2": {"name": "VIP Badge", "price": "99", "desc": "VIP Role + Perks"}
}

orders = {}

# ================= READY =================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ================= FIX ON_MESSAGE =================
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

# ================= NEW TECH TEST COMMAND =================
@bot.command(name="test")
async def test(ctx):

    latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title="⚙️ SYSTEM STATUS DASHBOARD",
        description="Bot is running successfully",
        color=discord.Color.green()
    )

    embed.add_field(name="🟢 Status", value="ONLINE", inline=True)
    embed.add_field(name="📡 Latency", value=f"{latency}ms", inline=True)
    embed.add_field(name="🧠 Commands", value="Loaded ✔", inline=True)
    embed.add_field(name="🛒 Shop", value="Active ✔", inline=True)
    embed.add_field(name="⚙️ System", value="Stable ✔", inline=True)

    embed.set_footer(text="All systems operational 🚀")

    await ctx.send(embed=embed)

# ================= AFK =================
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = {"reason": reason, "time": time.time()}
    await ctx.send(f"😴 AFK set: {reason}")

# ================= SHOP =================
@bot.command()
async def shop(ctx):

    embed = discord.Embed(
        title="🛒 TECH SHOP SYSTEM",
        description="Click a button to buy a product",
        color=discord.Color.gold()
    )

    for k, v in shop_items.items():
        embed.add_field(
            name=f"{v['name']} (ID: {k})",
            value=f"💰 ₹{v['price']}\n{v['desc']}",
            inline=False
        )

    await ctx.send(embed=embed, view=ShopView())

# ================= SHOP BUTTON SYSTEM =================
class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for key in shop_items:
            self.add_item(BuyButton(key))


class BuyButton(discord.ui.Button):
    def __init__(self, item_id):
        super().__init__(
            label=f"Buy {item_id}",
            style=discord.ButtonStyle.green
        )
        self.item_id = item_id

    async def callback(self, interaction: discord.Interaction):

        item = shop_items[self.item_id]
        order_id = str(len(orders) + 1)

        orders[order_id] = {
            "user": interaction.user.id,
            "item": item,
            "status": "PENDING"
        }

        embed = discord.Embed(
            title="💳 PAYMENT GATEWAY",
            description=f"{item['name']}\n₹{item['price']}",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(
            embed=embed,
            view=PaymentView(order_id),
            ephemeral=True
        )

class PaymentView(discord.ui.View):
    def __init__(self, order_id):
        super().__init__()
        self.order_id = order_id

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
            title="💰 SEND PAYMENT",
            description=f"{method}\n`{details}`",
            color=discord.Color.orange()
        )

        await interaction.response.send_message(
            embed=embed,
            view=PaidView(self.order_id),
            ephemeral=True
        )

class PaidView(discord.ui.View):
    def __init__(self, order_id):
        super().__init__()
        self.order_id = order_id

    @discord.ui.button(label="✅ I Paid", style=discord.ButtonStyle.success)
    async def paid(self, interaction, button):
        await interaction.response.send_message(
            "🧾 Send your transaction ID to admin for verification.",
            ephemeral=True
        )

# ================= VERIFY =================
@bot.command()
@commands.has_permissions(administrator=True)
async def verify(ctx, order_id: str):

    if order_id not in orders:
        return await ctx.send("❌ Invalid order")

    order = orders[order_id]
    user = await bot.fetch_user(order["user"])

    await user.send(
        f"✅ PAYMENT VERIFIED\n\nProduct: {order['item']['name']}"
    )

    order["status"] = "DONE"

    await ctx.send("✅ Order completed")

# ================= RUN =================
if TOKEN is None:
    raise RuntimeError("TOKEN not set")

bot.run(TOKEN)

