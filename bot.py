import discord
from discord.ext import commands
from discord import app_commands
import time
import yt_dlp
import os

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")

# ================= INTENTS =================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

afk_users = {}

# ================= SHOP DATA =================
shop_items = {
    "1": {
        "name": "Premium Access",
        "price": "199",
        "desc": "Lifetime Premium Role"
    },
    "2": {
        "name": "VIP Badge",
        "price": "99",
        "desc": "VIP Discord Role"
    }
}

orders = {}

# ================= READY =================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"Sync error: {e}")


# ================= TEST =================
@bot.command(name="test")
async def test(ctx):
    await ctx.send("✅ Bot is running (prefix command)")


@bot.tree.command(name="test", description="Check bot status")
async def test_slash(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Bot is running (slash command)")


# ================= INTRO =================
@bot.command(name="intro")
async def intro(ctx):
    await ctx.send("🤖 Bot Online")


@bot.tree.command(name="intro", description="Bot intro")
async def intro_slash(interaction: discord.Interaction):
    await interaction.response.send_message("🤖 Bot Online")


# ================= PURGE =================
async def purge_logic(channel, amount):
    if amount <= 0 or amount > 100:
        return None
    deleted = await channel.purge(limit=amount + 1)
    return len(deleted) - 1


@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    result = await purge_logic(ctx.channel, amount)

    if result is None:
        return await ctx.send("❌ Enter 1–100 only")

    await ctx.send(f"🧹 Deleted {result} messages", delete_after=5)


@bot.tree.command(name="purge", description="Delete messages")
@app_commands.describe(amount="Number of messages")
async def purge_slash(interaction: discord.Interaction, amount: int):

    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ No permission", ephemeral=True)

    result = await purge_logic(interaction.channel, amount)

    if result is None:
        return await interaction.response.send_message("❌ Enter 1–100", ephemeral=True)

    await interaction.response.send_message(f"🧹 Deleted {result}", ephemeral=True)


# ================= AFK =================
@bot.command(name="afk")
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = {"reason": reason, "time": time.time()}
    await ctx.send(f"😴 AFK set: {reason}")


@bot.tree.command(name="afk", description="Set AFK")
async def afk_slash(interaction: discord.Interaction, reason: str = "AFK"):
    afk_users[interaction.user.id] = {"reason": reason, "time": time.time()}
    await interaction.response.send_message("😴 AFK set", ephemeral=True)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id

    # return from AFK
    if uid in afk_users:
        data = afk_users.pop(uid)
        await message.channel.send(f"🟢 Welcome back {message.author.mention}")

    # mention AFK
    for user in message.mentions:
        if user.id in afk_users:
            await message.channel.send(f"😴 {user.name} is AFK")

    await bot.process_commands(message)


# ================= DM ALL =================
@bot.command(name="dmall")
@commands.has_permissions(administrator=True)
async def dmall(ctx, *, message):
    sent = 0

    async for member in ctx.guild.fetch_members(limit=None):
        if member.bot:
            continue
        try:
            await member.send(message)
            sent += 1
        except:
            pass

    await ctx.send(f"📩 Sent to {sent} members")


# ================= SHOP SYSTEM =================
class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for key in shop_items:
            self.add_item(BuyButton(key))


class BuyButton(discord.ui.Button):
    def __init__(self, item_id):
        super().__init__(
            label=f"Buy {item_id}",
            style=discord.ButtonStyle.green,
            custom_id=f"buy_{item_id}"
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
            title="💳 Payment Required",
            description=f"{item['name']}\n₹{item['price']}",
            color=discord.Color.blue()
        )

        view = PaymentView(order_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


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
            title="💰 Send Payment",
            description=f"{method}\n{details}",
            color=discord.Color.orange()
        )

        view = PaidView(self.order_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class PaidView(discord.ui.View):
    def __init__(self, order_id):
        super().__init__()
        self.order_id = order_id

    @discord.ui.button(label="✅ I Paid", style=discord.ButtonStyle.success)
    async def paid(self, interaction, button):
        await interaction.response.send_modal(TxnModal(self.order_id))


class TxnModal(discord.ui.Modal):
    def __init__(self, order_id):
        super().__init__(title="Payment Proof")
        self.order_id = order_id

    txn = discord.ui.TextInput(label="Transaction ID", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction):

        orders[self.order_id]["txn"] = self.txn.value
        orders[self.order_id]["status"] = "WAITING"

        await interaction.response.send_message("✅ Submitted", ephemeral=True)


# ================= SHOP COMMAND =================
@bot.command(name="shop")
async def shop(ctx):
    embed = discord.Embed(title="🛒 SHOP", color=discord.Color.gold())

    for k, v in shop_items.items():
        embed.add_field(
            name=f"{v['name']}",
            value=f"₹{v['price']}\n{v['desc']}",
            inline=False
        )

    await ctx.send(embed=embed, view=ShopView())


# ================= VERIFY ORDER =================
@bot.command(name="verify")
@commands.has_permissions(administrator=True)
async def verify(ctx, order_id: str):

    if order_id not in orders:
        return await ctx.send("❌ Invalid order")

    order = orders[order_id]
    user = await bot.fetch_user(order["user"])

    await user.send(f"✅ Payment Verified!\nProduct: {order['item']['name']}")

    order["status"] = "DONE"

    await ctx.send("✅ Verified & Delivered")


# ================= MUSIC (UNCHANGED) =================
ytdl = yt_dlp.YoutubeDL({"format": "bestaudio"})

ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


@bot.command(name="join")
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ Join voice")
    channel = ctx.author.voice.channel
    await channel.connect()


@bot.command(name="play")
async def play(ctx, url):
    if not ctx.voice_client:
        await ctx.invoke(join)

    info = ytdl.extract_info(url, download=False)
    audio_url = info["url"]

    source = await discord.FFmpegOpusAudio.from_probe(audio_url, **ffmpeg_options)

    ctx.voice_client.stop()
    ctx.voice_client.play(source)

    await ctx.send(f"🎵 Playing {info['title']}")


@bot.command(name="stop")
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()


# ================= RUN =================
if TOKEN is None:
    raise RuntimeError("TOKEN not set")

bot.run(TOKEN)

