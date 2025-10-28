import discord
import os
from dotenv import load_dotenv
load_dotenv()

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'ログインしました: {self.user}')

    async def on_message(self, message):
        print(f'送信: {message.author}: {message.content}')
        if message.author == self.user:
            return

        if message.content == '$Hello':
            await message.channel.send('Hello!')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv('TOKEN'))
