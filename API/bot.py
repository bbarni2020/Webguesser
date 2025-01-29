import discord
from discord.ui import Button, View
import requests
from flask import Flask, request, jsonify
import threading
from datetime import datetime, timedelta, timezone

API_KEY = ''
GUILD_ID = 0
CHANNEL_ID = 0

app = Flask(__name__)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

class MyView(View):
    def __init__(self, uid, user_name, email):
        super().__init__(timeout=None)
        self.uid = uid
        self.user_name = user_name
        self.email = email

    @discord.ui.button(label="Unlock 🔓", style=discord.ButtonStyle.green, custom_id="unlock_button")
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        response = requests.post(
            'http://localhost:5640/unlock',
            json={'uid': self.uid, 'active': 1},
            headers={'Authorization': f'Bearer {API_KEY}'}
        )
        current_time = datetime.now(timezone.utc) + timedelta(hours=1)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        if response.status_code == 200:
            await interaction.message.edit(
                embed=discord.Embed(
                    title="User Information",
                    description=(
                        f"Name: {self.user_name}\n"
                        f"Email: {self.email}\n"
                        f"Status: Unlocked 🔓\n"
                        f"Unlocked by: {interaction.user.mention}\n"
                        f"Date: {formatted_time}"
                    ),
                    color=discord.Color.dark_green()
                )
            )
        else:
            await interaction.message.edit(
                embed=discord.Embed(
                    title="User Information",
                    description=(
                        f"Name: {self.user_name}\n"
                        f"Email: {self.email}\n"
                        f"Status: Unlock failed\n"
                        f"Attempted by: {interaction.user.mention}\n"
                        f"Date: {formatted_time}"
                    ),
                    color=discord.Color.darker_grey()
                )
            )

    @discord.ui.button(label="Lock 🔒", style=discord.ButtonStyle.red, custom_id="lock_button")
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        response = requests.post(
            'http://localhost:5640/unlock',
            json={'uid': self.uid, 'active': 0},
            headers={'Authorization': f'Bearer {API_KEY}'}
        )
        current_time = datetime.now(timezone.utc) + timedelta(hours=1)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        if response.status_code == 200:
            await interaction.message.edit(
                embed=discord.Embed(
                    title="User Information",
                    description=(
                        f"Name: {self.user_name}\n"
                        f"Email: {self.email}\n"
                        f"Status: Locked 🔒\n"
                        f"Locked by: {interaction.user.mention}\n"
                        f"Date: {formatted_time}"
                    ),
                    color=discord.Color.dark_red()
                )
            )
        else:
            await interaction.message.edit(
                embed=discord.Embed(
                    title="User Information",
                    description=(
                        f"Name: {self.user_name}\n"
                        f"Email: {self.email}\n"
                        f"Status: Lock failed\n"
                        f"Attempted by: {interaction.user.mention}\n"
                        f"Date: {formatted_time}"
                    ),
                    color=discord.Color.darker_grey()
                )
            )


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.add_view(MyView(uid=None, user_name=None, email=None))

async def send_message(uid, user_name, email):
    guild = client.get_guild(GUILD_ID)
    channel = guild.get_channel(CHANNEL_ID)
    embed = discord.Embed(title="User Information", description=f"Name: {user_name}\nEmail: {email}", color=discord.Color.yellow())
    view = MyView(uid, user_name, email)
    await channel.send(embed=embed, view=view)

@app.route('/send_message', methods=['POST'])
def send_message_api():
    data = request.json
    uid = data.get('uid')
    user_name = data.get('user_name')
    email = data.get('email')
    if not uid or not user_name or not email:
        return jsonify({"error": "Missing data"}), 400

    client.loop.create_task(send_message(uid, user_name, email))
    return jsonify({"status": "Message sent"}), 200

def run_flask():
    app.run(port=2301)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    client.run('token')