﻿from datetime import datetime, timedelta
from discord.ext import commands
import requests
import pandas as pd
from dateutil.parser import parse
from Main import _is_banned

class GDQ(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return _is_banned(ctx)

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    ### Get the GDQ Schedule and show which game is running or next up ###
    @commands.group(name="gdqgame", aliases=["GDQgame", "GDQGame", "gdq", "GDQ", "Gdq"], brief="Gibt das aktuelle GDQ Game, Runner und Kategorie aus")
    async def _gdqgame(self, ctx):
        pass

    @_gdqgame.command(name="now", aliases=["Now", "jetzt", "jetzala", "Jetzt"], brief="Gibt das aktuelle GDQ Game, Runner und Kategorie aus")
    async def _gdqgamenow(self, ctx):
        GDQ_URL = "https://gamesdonequick.com/schedule"
        GDQ_REQ = requests.get(GDQ_URL)
        GDQ_DATAFRAME = pd.read_html(GDQ_REQ.text)
        for Entry in GDQ_DATAFRAME:
            for index in range(0, len(Entry["Run"]), 2):
                runEntry = Entry["Run"]
                timeEntry = Entry["Time & Length"]
                GameTime = parse(timeEntry[index])
                GameDuration = datetime.strptime(
                    timeEntry[index+1], "%H:%M:%S")
                GameDelta = timedelta(
                    hours=GameDuration.hour, minutes=GameDuration.minute, seconds=GameDuration.second)
                GameTimeStamp = datetime.timestamp(GameTime + GameDelta)
                if datetime.timestamp(datetime.now()) < GameTimeStamp and datetime.now().date() == GameTime.date():
                    await ctx.send(f"Bei GDQ läuft gerade {runEntry[index]} {runEntry[index+1]}!")
                    break
            else:
                await ctx.send("GDQ ist vorbei oder noch nicht angefangen, beehre uns bald wieder.")

    @_gdqgame.command(name="next", aliases=["Next", "Spaeter", "spaeter"], brief="Gibt das nächste GDQ Game, Runner und Kategorie aus")
    async def _gdqgamenext(self, ctx):
        GDQ_URL = "https://gamesdonequick.com/schedule"
        GDQ_REQ = requests.get(GDQ_URL)
        GDQ_DATAFRAME = pd.read_html(GDQ_REQ.text)
        for Entry in GDQ_DATAFRAME:
            for index in range(0, len(Entry["Run"]), 2):
                runEntry = Entry["Run"]
                timeEntry = Entry["Time & Length"]
                GameTime = parse(timeEntry[index])
                GameDuration = datetime.strptime(
                    timeEntry[index+1], "%H:%M:%S")
                GameDelta = timedelta(
                    hours=GameDuration.hour, minutes=GameDuration.minute, seconds=GameDuration.second)
                GameTimeStamp = datetime.timestamp(GameTime + GameDelta)
                if datetime.timestamp(datetime.now()) < GameTimeStamp and datetime.now().date() == GameTime.date():
                    await ctx.send(f"Bei GDQ läuft als nächstes {runEntry[index+2]} {runEntry[index+3]}!")
                    break
            else:
                await ctx.send("GDQ ist vorbei oder noch nicht angefangen, beehre uns bald wieder.")


def setup(bot):
    bot.add_cog(GDQ(bot))
