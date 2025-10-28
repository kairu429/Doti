import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import aiohttp
import json

load_dotenv()

TOKEN = os.getenv('TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')  # ← GroqのAPIキーも.envに入れる

# サーバーごとに設定したチャンネルを保存
channel_settings = {}

# Discord Intents設定
intents = discord.Intents.default()
intents.message_content = True

# クライアント設定
class MyClient(discord.Client):
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()  # スラッシュコマンド同期

client = MyClient(intents=intents)


# ========== スラッシュコマンド ==========
@client.tree.command(name="setchannel", description="AI応答用チャンネルを設定します")
@app_commands.describe(channel="AIが返信するチャンネルを選択してください")
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    guild_id = interaction.guild.id
    channel_settings[guild_id] = channel.id
    await interaction.response.send_message(
        f"✅ AI応答チャンネルを {channel.mention} に設定しました！", ephemeral=True
    )


# ========== メッセージ監視 ==========
@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None
    if guild_id not in channel_settings:
        return  # 未設定なら無視

    # 設定済みチャンネルか確認
    if message.channel.id != channel_settings[guild_id]:
        return

    # AIにメッセージを送信して返信を生成
    response = await generate_ai_reply(message.content)
    await message.channel.send(response)


# ========== Groq API呼び出し ==========
async def generate_ai_reply(prompt: str):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "llama-3.1-8b-instant",  # Groqで安定して速いモデル
        "messages": [
            {"role": "system", "content": "あなたはフレンドリーで知的なAIアシスタントです。"},
            {"role": "user", "content": prompt},
        ],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(data)) as resp:
            if resp.status != 200:
                return f"⚠️ Groq APIエラー: {resp.status}"
            result = await resp.json()
            return result["choices"][0]["message"]["content"].strip()


# ========== 起動 ==========
@client.event
async def on_ready():
    print(f"✅ ログイン成功: {client.user}")

if not TOKEN:
    raise ValueError("TOKEN environment variable is not set.")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")

client.run(TOKEN)
