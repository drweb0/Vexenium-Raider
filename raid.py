import os
import json
import asyncio
import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load token
def load_config():
    if not os.path.exists("config.json"):
        return {"TOKEN": ""}
    with open("config.json", "r") as f:
        return json.load(f)

def save_config(token):
    with open("config.json", "w") as f:
        json.dump({"TOKEN": token}, f)

# Token management
def token_management():
    print("=== Discord Bot Token Management ===")
    print("1. Set new token")
    print("2. Use existing token")
    
    choice = input("Choose option (1/2): ")
    
    if choice == "1":
        token = input("Enter bot token: ")
        save_config(token)
        print("Token saved!")
        return token
    elif choice == "2":
        config = load_config()
        token = config.get("TOKEN")
        if token:
            print("Token loaded!")
            return token
        else:
            print("No token found!")
            return None
    else:
        print("Invalid choice!")
        return None

# /vex raid
class SpamButton(View):
    def __init__(self, message, delay=0.5):
        super().__init__(timeout=300)
        self.message = message
        self.delay = delay

    @discord.ui.button(label="⚡ Start Spam", style=discord.ButtonStyle.danger)
    async def spam_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        
        for i in range(8):  # 8 сообщений за клик
            try:
                await interaction.followup.send(self.message, allowed_mentions=discord.AllowedMentions(everyone=True))
                await asyncio.sleep(self.delay)
            except Exception as e:
                print(f"Spam error: {e}")
                break

@bot.tree.command(name="vex", description="Start spam raid with button")
@app_commands.describe(
    text="Spam message text",
    delay="Delay between messages (0.1-2.0 seconds)"
)
async def vex_command(interaction: discord.Interaction, text: str, delay: float = 0.5):
    if delay < 0.1 or delay > 2.0:
        await interaction.response.send_message("❌ Delay must be between 0.1 and 2.0 seconds!", ephemeral=True)
        return
    
    view = SpamButton(text, delay)
    await interaction.response.send_message(
        f"**Vexelium Spam Tool**\n\nMessage: `{text}`\nDelay: `{delay}s`\n\nPress button to start spam:",
        view=view,
        ephemeral=True
    )

# /bl blame
@bot.tree.command(name="bl", description="Blame someone else for the raid")
@app_commands.describe(user="User to blame")
async def bl_command(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message("🕵️ Creating evidence...", ephemeral=True)
    await interaction.followup.send(f"✅ {user.mention} Your raid has been ended. Thanks for using our bot!")

@bot.event
async def on_ready():
    print(f"✅ Bot is online! Logged in as {bot.user}")
    print(f"✅ Commands loaded: /vex, /bl")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Command sync error: {e}")

# Start the bot
if __name__ == "__main__":
    token = token_management()
    if token:
        try:
            bot.run(token)
        except discord.LoginFailure:
            print("❌ Invalid token! Please check your bot token.")
        except Exception as e:
            print(f"❌ Bot error: {e}")
    else:
        print("❌ No token provided!")