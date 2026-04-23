import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv

# loading in the values from env file
load_dotenv()

# cog files that should load in
COGS = ["cogs.courses", "cogs.grades", "cogs.professors", "cogs.career"]


class CourseCompassBot(commands.Bot):
    def __init__(self):
        # default bot intents
        intents = discord.Intents.default()

        # lets the bot actually read the messages 
        intents.message_content = True

        # slash command setup for the bot to be able to read 
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self):
        print("=== Setup hook called ===")

        # for loop to load in the cog files
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"Loaded cog: {cog}")
            except Exception as e:
                print(f"Failed to load cog {cog}: {e}")

        # syncs slash commands with Discord
        try:
            await self.tree.sync()
            print("Slash commands synced.")
        except Exception as e:
            print(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        # prints bot info 
        print(f"CourseCompass is online as {self.user} (ID: {self.user.id})")

        # shares bot status + activity in the Discord
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name="/recommend")
        )


def main():
    # check if the python version is the right one 
    if sys.version_info < (3, 10):
        raise RuntimeError(
            "CourseCompass requires Python 3.10 or newer. "
            "Run with /usr/local/bin/python3.11 or your project .venv interpreter."
        )

    # pull bot token from env file
    token = os.environ.get("DISCORD_TOKEN")

    # if theres no token, stop the program
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set in your .env file.")

    # make a bot obj
    bot = CourseCompassBot()

    # start running the bot with token
    bot.run(token)


if __name__ == "__main__":
    # only run the program if executed properly
    main()