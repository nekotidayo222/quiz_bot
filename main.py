import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

QUIZ_FILE = "quiz.json"
QUIZ3_FILE = "3quiz.json"


def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")


# -------------------- /quiz --------------------
@bot.tree.command(name="quiz", description="quiz.jsonからクイズを出題 (記述式)")
async def quiz(interaction: discord.Interaction):
    quiz_data = load_json(QUIZ_FILE)
    if not quiz_data:
        await interaction.response.send_message("❌ クイズがまだありません。")
        return

    q = random.choice(quiz_data)
    await interaction.response.send_message(f"📝 問題: {q['question']}")

    def check(msg: discord.Message):
        return msg.author.id == interaction.user.id and msg.channel == interaction.channel

    try:
        msg = await bot.wait_for("message", timeout=30.0, check=check)
    except:
        await interaction.followup.send("⌛ 時間切れ！")
        return

    if msg.content.strip().lower() == q["answer"].lower():
        await interaction.followup.send("⭕ 正解！")
    else:
        await interaction.followup.send(f"❌ 不正解！正解は `{q['answer']}` です。")


# -------------------- /quiz-set --------------------
@bot.tree.command(name="quiz-set", description="quiz.jsonにクイズを追加 (管理者のみ)")
async def quiz_set(interaction: discord.Interaction, question: str, answer: str):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    quiz_data = load_json(QUIZ_FILE)
    quiz_data.append({"question": question, "answer": answer})
    save_json(QUIZ_FILE, quiz_data)
    await interaction.response.send_message(f"✅ クイズを追加しました！\nQ: {question}\nA: {answer}")


# -------------------- /3quiz --------------------
@bot.tree.command(name="3quiz", description="3quiz.jsonから3択クイズを出題")
async def quiz3(interaction: discord.Interaction):
    quiz_data = load_json(QUIZ3_FILE)
    if not quiz_data:
        await interaction.response.send_message("❌ 3択クイズがまだありません。")
        return

    q = random.choice(quiz_data)
    question = q["question"]
    answer = q["answer"]
    choices = [answer, q["dummy1"], q["dummy2"]]
    random.shuffle(choices)

    view = discord.ui.View()
    for choice in choices:
        async def button_callback(interact: discord.Interaction, choice=choice):
            if choice == answer:
                await interact.response.send_message("⭕ 正解！", ephemeral=True)
            else:
                await interact.response.send_message(f"❌ 不正解！正解は `{answer}` です。", ephemeral=True)

        button = discord.ui.Button(label=choice, style=discord.ButtonStyle.primary)
        button.callback = button_callback
        view.add_item(button)

    await interaction.response.send_message(f"📝 問題: {question}", view=view)


# -------------------- /3quiz-set --------------------
@bot.tree.command(name="3quiz-set", description="3quiz.jsonに3択クイズを追加 (管理者のみ)")
async def quiz3_set(interaction: discord.Interaction, question: str, answer: str, dummy1: str, dummy2: str):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ このコマンドは管理者のみ使用できます。", ephemeral=True)
        return

    quiz_data = load_json(QUIZ3_FILE)
    quiz_data.append({"question": question, "answer": answer, "dummy1": dummy1, "dummy2": dummy2})
    save_json(QUIZ3_FILE, quiz_data)
    await interaction.response.send_message(
        f"✅ 3択クイズを追加しました！\nQ: {question}\nA: {answer}\n選択肢: {answer}, {dummy1}, {dummy2}"
    )


bot.run(TOKEN)
