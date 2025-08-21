import discord
from discord.ext import commands
from discord import app_commands
import json
import os

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== JSON 読み書き =====
def load_json(filename, default):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

global_data = load_json("global.json", {"channels": []})
shogo_data = load_json("shogo.json", {})

# ===== 起動 =====
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# ===== コマンド =====

# /setup
@bot.tree.command(name="setup", description="このチャンネルをグローバルチャットに設定します")
async def setup(interaction: discord.Interaction):
    channel_id = interaction.channel.id
    if channel_id not in global_data["channels"]:
        global_data["channels"].append(channel_id)
        save_json("global.json", global_data)
        await interaction.response.send_message("✅ このチャンネルをグローバルチャットに設定しました", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ すでに設定されています", ephemeral=True)

# /shogo-set
@bot.tree.command(name="shogo-set", description="ユーザーに二つ名を設定 (管理者専用)")
@app_commands.describe(userid="ユーザーID", content="二つ名")
async def shogo_set(interaction: discord.Interaction, userid: str, content: str):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ 権限がありません", ephemeral=True)
        return

    shogo_data[userid] = content
    save_json("shogo.json", shogo_data)
    await interaction.response.send_message(f"✅ <@{userid}> に二つ名「{content}」を設定しました", ephemeral=True)

# /serverlist
@bot.tree.command(name="serverlist", description="導入サーバー一覧を表示 (実行者のみ閲覧可)")
async def serverlist(interaction: discord.Interaction):
    embed_color = discord.Color.red() if interaction.user.id == ADMIN_ID else discord.Color.white()
    embed = discord.Embed(title="🌍 導入サーバー一覧", color=embed_color)

    setup_servers = []
    not_setup_servers = []

    for guild in bot.guilds:
        owner = await bot.fetch_user(guild.owner_id)
        try:
            invite = await list(guild.text_channels)[0].create_invite(max_age=0, max_uses=0)
            invite_link = invite.url
        except:
            invite_link = "招待リンクを作成できませんでした"

        # setup済みかどうか判定
        is_setup = any(cid in [c.id for c in guild.text_channels] for cid in global_data["channels"])

        entry = f"所有者: {owner}\n招待: {invite_link}"
        if is_setup:
            setup_servers.append((guild.name, entry))
        else:
            not_setup_servers.append((guild.name, entry))

    if setup_servers:
        embed.add_field(name="✅ グローバルチャット登録済み", value="\n\n".join([f"**{name}**\n{info}" for name, info in setup_servers]), inline=False)
    if not_setup_servers:
        embed.add_field(name="⚪ 未登録サーバー", value="\n\n".join([f"**{name}**\n{info}" for name, info in not_setup_servers]), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# /warn
@bot.tree.command(name="warn", description="ユーザーにDMで警告を送信 (管理者専用)")
@app_commands.describe(userid="ユーザーID", content="警告内容")
async def warn(interaction: discord.Interaction, userid: str, content: str):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ 権限がありません", ephemeral=True)
        return

    user = await bot.fetch_user(int(userid))
    try:
        await user.send(f"⚠️ 警告: {content}")
        await interaction.response.send_message(f"✅ <@{userid}> に警告を送信しました", ephemeral=True)
    except:
        await interaction.response.send_message("❌ DMを送信できませんでした", ephemeral=True)

# ====== グローバルチャット転送 ======
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id in global_data["channels"]:
        shogo = shogo_data.get(str(message.author.id), "")
        shogo_display = f"《{shogo}》" if shogo else ""

        content = message.content if message.content else "[添付のみ]"

        embed = discord.Embed(
            description=content,
            color=discord.Color.blue()
        )
        embed.set_author(
            name=f"{message.guild.name}: {shogo_display}{message.author.display_name}[{message.author.name}]",
            icon_url=message.author.display_avatar.url
        )

        files = []
        for attachment in message.attachments:
            try:
                file = await attachment.to_file()
                files.append(file)
            except:
                pass

        for channel_id in global_data["channels"]:
            if channel_id != message.channel.id:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed, files=files)

    await bot.process_commands(message)

bot.run(TOKEN)
