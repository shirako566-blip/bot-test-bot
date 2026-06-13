import discord
from discord.ext import commands
import time
import yt_dlp
import os

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= AFK SYSTEM =================
afk_users = {}

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


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ================= TEST COMMAND =================
@bot.command()
async def test(ctx):
    results = []

    results.append("✅ Bot is running")

    if isinstance(afk_users, dict):
        results.append("✅ AFK system OK")
    else:
        results.append("❌ AFK system error")

    if ctx.voice_client:
        results.append("🎧 Voice: Connected")
    else:
        results.append("🎧 Voice: Not connected")

    perms = ctx.guild.me.guild_permissions

    if perms.send_messages:
        results.append("✅ Send Messages OK")
    else:
        results.append("❌ Missing Send Messages permission")

    if perms.connect:
        results.append("✅ Voice Connect OK")
    else:
        results.append("❌ Missing Voice permission")

    if perms.speak:
        results.append("✅ Speak Permission OK")
    else:
        results.append("❌ Missing Speak permission")

    await ctx.send("\n".join(results))


# ================= INTRO =================
@bot.command()
async def intro(ctx):
    await ctx.send(
        "🤖 **Booting up systems...**\n"
        "🎧 Music Engine: Online\n"
        "😴 AFK System: Active\n"
        "📩 DM System: Ready\n\n"
        "👋 Hello! I am **Bot Test OFC**\n"
        "Your all-in-one Discord assistant ⚡"
    )


# ================= AFK =================
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_users[ctx.author.id] = {
        "reason": reason,
        "time": time.time(),
    }

    await ctx.send(f"🟢 You are now AFK\nReason: {reason}")


# ================= DM ALL =================
@bot.command()
@commands.has_permissions(administrator=True)
async def dmall(ctx, *, message):
    sent = 0

    async for member in ctx.guild.fetch_members(limit=None):
        if member.bot:
            continue

        try:
            await member.send(message)
            sent += 1
        except Exception:
            pass

    await ctx.send(f"📩 Sent DM to {sent} members.")


# ================= JOIN VOICE =================
@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ You are not in a voice channel!")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send("🎧 Joined voice channel")


# ================= PLAY MUSIC =================
@bot.command()
async def play(ctx, url):
    if not ctx.voice_client:
        await ctx.invoke(join)

    voice = ctx.voice_client

    info = ytdl.extract_info(url, download=False)
    audio_url = info["url"]

    source = await discord.FFmpegOpusAudio.from_probe(
        audio_url,
        **ffmpeg_options,
    )

    voice.stop()
    voice.play(source)

    await ctx.send(f"🎵 Now Playing: **{info['title']}**")
# ================= MUSIC CONTROLS =================
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused")


@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed")


@bot.command()
async def skip(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped")


@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⛔ Stopped & left voice")


# ================= AFK HANDLER =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id

    # Remove AFK when user sends a message
    if user_id in afk_users:
        data = afk_users.pop(user_id)
        afk_time = round(time.time() - data["time"])

        await message.channel.send(
            f"🟢 Welcome back {message.author.mention}\n"
            f"Reason: {data['reason']}\n"
            f"AFK Time: {afk_time} sec"
        )

    # Notify if mentioned user is AFK
    for user in message.mentions:
        if user.id in afk_users:
            data = afk_users[user.id]
            afk_time = round(time.time() - data["time"])

            await message.channel.send(
                f"🟡 {user.name} is AFK\n"
                f"Reason: {data['reason']}\n"
                f"AFK for: {afk_time} sec"
            )

    await bot.process_commands(message)


# ================= START BOT =================
if TOKEN is None:
    raise RuntimeError(
        "TOKEN environment variable is not set. "
        "Add TOKEN in Railway Variables."
    )

bot.run(TOKEN)