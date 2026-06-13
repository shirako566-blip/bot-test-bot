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

# ================= SYNC SLASH COMMANDS =================
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
    await ctx.send("🤖 Bot Test OFC Online (prefix)")


@bot.tree.command(name="intro", description="Bot intro")
async def intro_slash(interaction: discord.Interaction):
    await interaction.response.send_message("🤖 Bot Test OFC Online (slash)")


# ================= PURGE (HYBRID CORE FUNCTION) =================
async def purge_logic(channel, amount):
    if amount <= 0:
        return None
    if amount > 100:
        return None

    deleted = await channel.purge(limit=amount + 1)
    return len(deleted) - 1


# PREFIX PURGE
@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    result = await purge_logic(ctx.channel, amount)

    if result is None:
        return await ctx.send("❌ Enter 1–100 only")

    await ctx.send(f"🧹 Deleted {result} messages", delete_after=5)


# SLASH PURGE
@bot.tree.command(name="purge", description="Delete messages (1–100)")
@app_commands.describe(amount="Number of messages")
async def purge_slash(interaction: discord.Interaction, amount: int):

    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message(
            "❌ No permission",
            ephemeral=True
        )

    result = await purge_logic(interaction.channel, amount)

    if result is None:
        return await interaction.response.send_message(
            "❌ Enter 1–100 messages",
            ephemeral=True
        )

    await interaction.response.send_message(
        f"🧹 Deleted {result} messages",
        ephemeral=True
    )


# ================= AFK SYSTEM =================
@bot.command(name="afk")
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = {
        "reason": reason,
        "time": time.time()
    }

    await ctx.send(f"😴 You are now AFK: {reason}")


@bot.tree.command(name="afk", description="Set AFK status")
@app_commands.describe(reason="AFK reason")
async def afk_slash(interaction: discord.Interaction, reason: str = "AFK"):

    afk_users[interaction.user.id] = {
        "reason": reason,
        "time": time.time()
    }

    await interaction.response.send_message(
        f"😴 AFK set: {reason}",
        ephemeral=True
    )
    # ================= AFK HANDLER =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id

    # remove AFK
    if user_id in afk_users:
        data = afk_users.pop(user_id)
        afk_time = round(time.time() - data["time"])

        await message.channel.send(
            f"🟢 Welcome back {message.author.mention}\n"
            f"Reason: {data['reason']}\n"
            f"AFK Time: {afk_time}s"
        )

    # mention check
    for user in message.mentions:
        if user.id in afk_users:
            data = afk_users[user.id]
            afk_time = round(time.time() - data["time"])

            await message.channel.send(
                f"😴 {user.name} is AFK\n"
                f"Reason: {data['reason']}\n"
                f"Time: {afk_time}s"
            )

    await bot.process_commands(message)


# ================= DM ALL (PREFIX ONLY - SAFE ADMIN TOOL) =================
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


# ================= MUSIC SETUP =================
ytdl_format_options = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
}

ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


# ================= JOIN =================
@bot.command(name="join")
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ Join voice first")

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send("🎧 Joined voice")


# ================= PLAY =================
@bot.command(name="play")
async def play(ctx, url):

    if not ctx.voice_client:
        await ctx.invoke(join)

    voice = ctx.voice_client

    info = ytdl.extract_info(url, download=False)
    audio_url = info["url"]

    source = await discord.FFmpegOpusAudio.from_probe(
        audio_url,
        **ffmpeg_options
    )

    voice.stop()
    voice.play(source)

    await ctx.send(f"🎵 Playing: {info['title']}")


# ================= CONTROLS =================
@bot.command(name="pause")
async def pause(ctx):
    if ctx.voice_client:
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused")


@bot.command(name="resume")
async def resume(ctx):
    if ctx.voice_client:
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed")


@bot.command(name="skip")
async def skip(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped")


@bot.command(name="stop")
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⛔ Disconnected")


# ================= START BOT =================
if TOKEN is None:
    raise RuntimeError("TOKEN not set in environment variables")

bot.run(TOKEN)
