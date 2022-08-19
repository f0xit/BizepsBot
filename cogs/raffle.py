import discord
from discord import Option
from discord.ext import commands
from Main import _is_banned
from Main import _read_json
from Main import _write_json
from Main import _get_banned_users
from Main import logging
from Main import random

### Checks ###


def _raffle_active(self):
    RaffleJSON = _read_json('Settings.json')
    return RaffleJSON['Settings']['Raffle']['Active']


class Raffle(commands.Cog, name="Raffle"):

    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()

    async def cog_check(self, ctx):
        return _is_banned(ctx, self.BannedUsers)

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    # Commands
    giveaway = discord.SlashCommandGroup("giveaway", "Befehle für Giveaways")

    @giveaway.command(name="join", brief="Tritt dem Giveaway bei")
    @commands.check(_raffle_active)
    async def _joinraffle(self, ctx):
        RaffleJSON = _read_json('Settings.json')
        NewEntry = {
            f"{ctx.author.name}": ctx.author.mention
        }
        if ctx.author.name not in RaffleJSON['Settings']['Raffle']['Entries'].keys():
            RaffleJSON['Settings']['Raffle']['Entries'].update(NewEntry)
            await ctx.respond("Du wurdest zum Raffle hinzugefügt.")
        else:
            await ctx.respond("Du bist bereits im Raffle, jeder nur ein Los!")
        _write_json('Settings.json', RaffleJSON)

    @giveaway.command(name="show", brief="Zeigt das aktuelle Giveaway")
    @commands.check(_raffle_active)
    async def _showraffle(self, ctx):
        RaffleJSON = _read_json('Settings.json')
        ctx.respond(
            f"Aktuell wird {RaffleJSON['Settings']['Raffle']['Title']} verlost!")

    @commands.slash_command(name="set_giveaway", description="Startet ein Giveaway", brief="Startet ein Giveaway")
    @discord.default_permissions(administrator=True)
    @commands.has_role("Admin")
    async def _set_giveaway(self, ctx, prize: Option(str, description="Der Preis", required=True)):
        """
        Setzt den Preis für ein Giveaway.
        """
        RaffleJSON = _read_json('Settings.json')
        CurrentPrize = RaffleJSON['Settings']['Raffle']['Title']
        if CurrentPrize != "":
            await ctx.respond(f"Aktuell ist {CurrentPrize} noch im Giveaway eingetragen!")
        else:
            RaffleJSON['Settings']['Raffle']['Title'] = prize
            RaffleJSON['Settings']['Raffle']['Active'] = True
            _write_json('Settings.json', RaffleJSON)
            await ctx.respond(f"{prize} wurde zum Giveaway hinzugefügt!")

    @commands.slash_command(name="start_giveaway", description="Startet ein Giveaway", brief="Startet ein Giveaway")
    @discord.default_permissions(administrator=True)
    @commands.has_role("Admin")
    async def _start_giveaway(self, ctx):
        """
        Startet ein Giveaway.
        """
        RaffleJSON = _read_json('Settings.json')
        CurrentPrize = RaffleJSON['Settings']['Raffle']['Title']
        CurrentState = RaffleJSON['Settings']['Raffle']['Active']
        if CurrentPrize != "" and CurrentState:
            await ctx.respond(f"Das neue Raffle wurde aktiviert! Teilnehmen könnt ihr über /giveaway join, verlost wird {RaffleJSON['Settings']['Raffle']['Title']}!")
        else:
            await ctx.respond(f"Es fehlt der Preis oder der Status wurde nicht auf aktiv gesetzt! Preis: {CurrentPrize} State: {CurrentState}!")

    @commands.slash_command(name="stop_giveaway", description="Startet ein Giveaway", brief="Startet ein Giveaway")
    @discord.default_permissions(administrator=True)
    @commands.has_role("Admin")
    async def _stop_giveaway(self, ctx):
        """
        Beendet ein Giveaway.
        """
        RaffleJSON = _read_json('Settings.json')
        EntryList = list(RaffleJSON['Settings']
                         ['Raffle']['Entries'].items())
        if EntryList == []:
            await ctx.respond("Leider hat niemand teilgenommen. Viel Glück beim nächsten Mal!")
        else:
            Entry = random.SystemRandom().choice(EntryList)
            await ctx.respond(f"Das Raffle wurde beendet! {RaffleJSON['Settings']['Raffle']['Title']} wurde von {Entry[0]}! {Entry[1]} gewonnen!")
        RaffleJSON['Settings']['Raffle']['Entries'] = {}
        RaffleJSON['Settings']['Raffle']['Title'] = ""
        RaffleJSON['Settings']['Raffle']['Active'] = False
        _write_json('Settings.json', RaffleJSON)

    @_start_giveaway.error
    async def _showlog_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.respond("Na na, das darf nur der Admin.")
            logging.warning(f"{ctx.author} wanted to start a giveaway!")

    @_stop_giveaway.error
    async def _showlog_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.respond("Na na, das darf nur der Admin.")
            logging.warning(f"{ctx.author} wanted to stop a giveaway!")

    @_set_giveaway.error
    async def _showlog_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.respond("Na na, das darf nur der Admin.")
            logging.warning(f"{ctx.author} wanted to set a giveaway!")

    @_joinraffle.error
    async def _giveaway_join_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Es ist kein Giveaway aktiv!")
            logging.info(
                f"{ctx.author} wanted to join a giveaway, but none are running.")
        else:
            logging.error(f"{error}")  # Raise other errors

    @_showraffle.error
    async def _giveaway_show_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, discord.errors.CheckFailure):
            await ctx.respond("Es ist kein Giveaway aktiv!")
            logging.info(
                f"{ctx.author} wanted to join a giveaway, but none are running.")
        else:
            logging.error(f"{error}")  # Raise other errors


def setup(bot):
    bot.add_cog(Raffle(bot))
