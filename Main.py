import datetime
import json
import logging
import os

import discord
from discord.ext import commands

logging.getLogger(name="discord").setLevel(level=logging.WARNING)
logging.basicConfig(
    format="[%(asctime)s] %(message)s", level=logging.INFO, handlers=[logging.FileHandler(filename=f"./logs/{datetime.datetime.now().date()}_bot.log"), logging.StreamHandler()], encoding="UTF-8"
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(debug_guilds=[539546796473712650], command_prefix=("!"), intents=intents)


def _read_json(FileName):
    with open(f"{FileName}", "r", encoding="utf-8") as JsonRead:
        return json.load(JsonRead)


def _write_json(FileName, Content):
    with open(f"{FileName}", "w", encoding="utf-8") as JsonWrite:
        json.dump(Content, JsonWrite, indent=4)


def _load_settings_file():
    global bot
    bot.Settings = _read_json("Settings.json")
    logging.info("Settings have been loaded.")
    return bot.Settings


@bot.event
async def on_ready():
    """Startet den Bot und die Loops werden gestartet, sollten sie nicht schon laufen."""

    bot.reload_settings = _load_settings_file
    logging.info(f"Logged in as {bot.user}!")
    logging.info("Bot started up!")


@bot.event
async def on_message(message):
    """Was bei einer Nachricht passieren soll."""
    if message.author == bot.user:
        return


if __name__ == "__main__":
    _load_settings_file()

    with open("TOKEN.json", "r", encoding="UTF-8") as TOKENFILE:
        TOKENDATA = json.load(TOKENFILE)
        TOKEN = TOKENDATA["DISCORD_TOKEN"]

    for File in os.listdir("./cogs"):
        if File.endswith(".py") and f"cogs.{File[:-3]}" not in bot.extensions and not File.startswith("management") and not File.startswith("old"):
            bot.load_extension(f"cogs.{File[:-3]}")
            logging.info(f"Extension {File[:-3]} loaded.")
    if "cogs.management" not in bot.extensions:
        bot.load_extension("cogs.management")
        logging.info("Extension management loaded.")

    bot.run(TOKEN)
