import os

import discord
import requests
from discord import Option
from discord.ext import commands

from Main import logging


class Management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="reload_settings", description="Lädt alle Einstellungen des Bots neu", brief="Lädt alle Einstellungen des Bots neu")
    @discord.default_permissions(administrator=True)
    async def _reload_settings(self, ctx):
        self.bot.reload_settings()
        await ctx.respond("Die Boteinstellungen wurden neugeladen.")

    @commands.slash_command(name="ip", description="Gibt die aktuelle public IP aus")
    @discord.default_permissions(administrator=True)
    @commands.has_any_role("Admin", "Moderatoren")
    async def _returnpubip(self, ctx):
        MyIP = requests.get("https://api.ipify.org").content.decode("UTF-8")
        await ctx.respond(f"Die aktuelle IP lautet: {MyIP}", ephemeral=True)
        logging.info(f"{ctx.author} requested the public ip.")

    @commands.slash_command(name="log", description="Zeigt die neusten Logeinträge des Bots", brief="Zeigt die neusten Logeinträge des Bots")
    @discord.default_permissions(administrator=True)
    @commands.has_role("Admin")
    async def _showlog(self, ctx):
        """
        Zeigt die letzten 10 Einträge des Logs.
        """
        AllLogFiles = next(os.walk("logs/"))[2]
        SortedLogFiles = sorted(AllLogFiles)
        LatestLogFile = SortedLogFiles[-1]
        with open(f"logs/{LatestLogFile}", "r") as LogFileRead:
            LogContent = LogFileRead.readlines()
            LatestLogLines = LogContent[-10:]
            LogOutputInString = "".join(LatestLogLines)
            await ctx.defer()
            await ctx.followup.send(f"```{LogOutputInString}```")
        logging.info(f"{ctx.author} has called for the log.")

    @commands.slash_command(name="extension", description="Verwaltet die Extensions")
    @discord.default_permissions(administrator=True)
    async def _extensions(self, ctx, changearg: Option(str, "laden/entladen", choices=["load", "unload"], required=True), extension):
        """
        Verwaltet die externen Cogs.

        Load:   Lädt die Cog in den Bot.
        Unload: Entfernt die Cog aus dem Bot.
        """
        if changearg == "load":
            self.bot.load_extension(f"cogs.{extension}")
            await ctx.respond(f"Extension {extension} wurde geladen und ist jetzt einsatzbereit.")
            logging.info(f"Extension {extension} was loaded.")
        elif changearg == "unload":
            self.bot.unload_extension(f"cogs.{extension}")
            await ctx.respond(f"Extension {extension} wurde entfernt und ist nicht mehr einsatzfähig.")
            logging.info(f"Extension {extension} was unloaded.")

    @_showlog.error
    async def _showlog_error(self, ctx, error):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Na na, das darf nur der Admin.")
            logging.warning(f"{ctx.author} wanted to read the logs!")

def setup(bot):
    bot.add_cog(Management(bot))
