import os
import json
import asyncio
import random
import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def load_config():
    if not os.path.exists("config.json"):
        return {"TOKEN": "", "HELPER_TOKENS": []}
    with open("config.json", "r") as f:
        return json.load(f)

def save_config(token, helper_tokens=None):
    if helper_tokens is None:
        helper_tokens = []
    with open("config.json", "w") as f:
        json.dump({"TOKEN": token, "HELPER_TOKENS": helper_tokens}, f)

def load_helper_bots():
    config = load_config()
    helper_tokens = config.get("HELPER_TOKENS", [])
    helper_bots = []
    
    for i, token in enumerate(helper_tokens):
        if token:
            intents = discord.Intents.default()
            intents.message_content = True
            helper_bot = discord.Client(intents=intents)
            
            @helper_bot.event
            async def on_ready():
                print(f"✅ Helper Bot {i+1} is online! Logged in as {helper_bot.user}")
            
            helper_bots.append({"client": helper_bot, "token": token})
    
    return helper_bots

# Token management
def token_management():
    print("=== Discord Bot Token Management ===")
    print("1. Set main bot token")
    print("2. Set helper bots tokens (3 helpers)")
    print("3. Use existing tokens")
    
    choice = input("Choose option (1/2/3): ")
    
    if choice == "1":
        token = input("Enter main bot token: ")
        config = load_config()
        save_config(token, config.get("HELPER_TOKENS", []))
        print("Main token saved!")
        return token
    
    elif choice == "2":
        helper_tokens = []
        for i in range(3):
            token = input(f"Enter helper bot {i+1} token: ")
            helper_tokens.append(token)
        config = load_config()
        save_config(config.get("TOKEN", ""), helper_tokens)
        print("Helper tokens saved!")
        return config.get("TOKEN", "")
    
    elif choice == "3":
        config = load_config()
        token = config.get("TOKEN")
        if token:
            print("Tokens loaded!")
            return token
        else:
            print("No tokens found!")
            return None
    else:
        print("Invalid choice!")
        return None

# /vex
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

# Mass ping
class MassPingButton(View):
    def __init__(self, user_ids: list, pings_per_message: int = 1):
        super().__init__(timeout=None)
        self.user_ids = user_ids
        self.pings_per_message = pings_per_message
        self.delay = 1

    @discord.ui.button(label="🔁 Ping!", style=discord.ButtonStyle.red)
    async def ping_button(self, interaction: discord.Interaction, button: Button):
        if not self.user_ids:
            await interaction.response.send_message("⚠️ No IDs available to ping.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        max_retries = 2

        for _ in range(5):
            selected_ids = random.sample(self.user_ids, min(self.pings_per_message, len(self.user_ids)))
            mentions = " ".join(f"<@{uid}>" for uid in selected_ids)
            pingmsg = '''
text for mass ping )**
            '''
            message_content = f"{mentions}\n{pingmsg}"
            retries = 0
            while retries <= max_retries:
                try:
                    await interaction.followup.send(message_content, ephemeral=False)
                    break
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        retry_after = getattr(e, "retry_after", 1.5)
                        retry_after = min(retry_after, 5)
                        print(f"Rate limit hit, retrying after {retry_after:.2f}s (retry {retries + 1}/{max_retries})")
                        await asyncio.sleep(retry_after)
                        retries += 1
                    else:
                        raise e
            else:
                print("Failed to send message after max retries, skipping.")

# dm spam
class DMSpamButton(View):
    def __init__(self, user: discord.User, message: str):
        super().__init__(timeout=300)
        self.user = user
        self.message = message

    @discord.ui.button(label="💣 Start DM Spam", style=discord.ButtonStyle.danger)
    async def dm_spam_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        
        config = load_config()
        helper_tokens = config.get("HELPER_TOKENS", [])
        
        if len(helper_tokens) < 3:
            await interaction.followup.send("❌ Not enough helper bots configured! Need 3 helper tokens.", ephemeral=True)
            return
        
        try:
           
            success_count = 0
            
            
            try:
                await self.user.send(f" {self.message}")
                success_count += 1
            except:
                pass
            
            # Start spam
            await interaction.followup.send(f"🚀 Starting DM spam with {len(helper_tokens) + 1} bots...", ephemeral=True)
            
            
            async def send_helper_messages(token, bot_number):
                try:
                    helper_client = discord.Client(intents=discord.Intents.default())
                    
                    @helper_client.event
                    async def on_ready():
                        try:
                            target_user = await helper_client.fetch_user(self.user.id)
                            for i in range(5):  
                                await target_user.send(f"#{bot_number} {self.message}")
                                await asyncio.sleep(0.5)
                            await helper_client.close()
                        except Exception as e:
                            print(f"Helper bot {bot_number} error: {e}")
                            await helper_client.close()
                    
                    await helper_client.start(token)
                except Exception as e:
                    print(f"Failed to start helper bot {bot_number}: {e}")
            
            
            tasks = []
            for i, token in enumerate(helper_tokens[:3]):  
                task = asyncio.create_task(send_helper_messages(token, i+1))
                tasks.append(task)
            
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            await interaction.followup.send(f"✅ DM spam completed! Used {len(helper_tokens) + 1} bots", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ DM spam error: {e}", ephemeral=True)

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

# /massping
@bot.tree.command(name="massping", description="Ping random user IDs from a .txt file using a button")
@app_commands.describe(
    file="A .txt file containing user IDs (one per line)",
    pings_per_message="Amount of users to ping per message (1-5 recommended)"
)
@app_commands.rename(pings_per_message="amount")
async def massping_command(
    interaction: discord.Interaction,
    file: discord.Attachment,
    pings_per_message: int = 1
):
    try:
        if not file.filename.endswith(".txt"):
            await interaction.response.send_message("❌ Please upload a valid `.txt` file with user IDs.", ephemeral=True)
            return

        file_content = await file.read()
        text = file_content.decode("utf-8")
        user_ids = [line.strip() for line in text.splitlines() if line.strip().isdigit()]

        if not user_ids:
            await interaction.response.send_message("⚠️ No valid user IDs found in the file.", ephemeral=True)
            return

        view = MassPingButton(user_ids, pings_per_message)
        await interaction.response.send_message("🔴 Click to ping random users!", view=view, ephemeral=True)

    except Exception as e:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ Error: `{e}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Error: `{e}`", ephemeral=True)

# /dmspam
@bot.tree.command(name="dmspam", description="DM spam user with multiple bots")
@app_commands.describe(
    user="User to DM spam",
    message="Message to send"
)
async def dmspam_command(interaction: discord.Interaction, user: discord.User, message: str):
    config = load_config()
    helper_tokens = config.get("HELPER_TOKENS", [])
    
    if len(helper_tokens) < 3:
        await interaction.response.send_message(
            "❌ Not enough helper bots configured! Need 3 helper tokens. Use token management to set them.",
            ephemeral=True
        )
        return
    
    view = DMSpamButton(user, message)
    await interaction.response.send_message(
        f"**DM Spam Tool**\n\nTarget: {user.mention}\nMessage: `{message}`\nBots: {len(helper_tokens) + 1}\n\nPress button to start DM spam:",
        view=view,
        ephemeral=True
    )

# /bl
@bot.tree.command(name="bl", description="Blame someone else for the raid")
@app_commands.describe(user="User to blame")
async def bl_command(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message("🕵️ Creating evidence...", ephemeral=True)
    await interaction.followup.send(f"✅ {user.mention} Your raid has been ended. Thanks for using our bot!")

@bot.event
async def on_ready():
    print(f"✅ Main Bot is online! Logged in as {bot.user}")
    print(f"✅ Commands loaded: /vex, /massping, /dmspam, /bl")
    
    config = load_config()
    helper_tokens = config.get("HELPER_TOKENS", [])
    if helper_tokens:
        print(f"✅ {len(helper_tokens)} helper tokens loaded")
    else:
        print("⚠️ No helper tokens configured. Use token management to set them.")
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Command sync error: {e}")

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