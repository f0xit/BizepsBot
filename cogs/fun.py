import json
import random

import aiohttp
import discord
import uwuify
from discord.ext import commands

from Main import _get_banned_users, _is_banned, logging


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.BannedUsers = _get_banned_users()

    async def cog_check(self, ctx):
        return await _is_banned(ctx)

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    async def get_waifu_img(self) -> dict[str, str | list] | None:
        waifurl = "https://api.waifu.im/search?is_nsfw=null"

        return_dict = {
            "url": "",
            "name": "",
            "urls": [],
        }
        async_timeout = aiohttp.ClientTimeout(total=2)

        async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}, timeout=async_timeout) as aiosession, aiosession.get(waifurl) as res:
            if res.status != 200:
                logging.error("Waifu API returned status code != 200!")
                return None

            try:
                img_json = (await res.json())["images"][0]
                return_dict["url"] = img_json["url"]
                if (artist := img_json["artist"]) is not None:
                    return_dict["name"] = artist["name"]
                    return_dict["urls"] = [page[1] for page in artist.items() if page[0] in ["patreon", "pixiv", "twitter", "deviant_art"] and page[1] is not None]
            except json.decoder.JSONDecodeError:
                logging.error("Waifu JSON Decode failed!")
                return None
            except KeyError:
                logging.error("Waifu key error: Something is wrong with the JSON file!")
                return None

            return return_dict

    # Commands
    @commands.slash_command(name="josch", description="Entwickler...", brief="Entwickler...")
    async def _blamedevs(self, ctx):
        await ctx.defer()
        await ctx.followup.send(file=discord.File("memes/josch700 (josch700)/josch.png"))
        logging.info(f"{ctx.author} blamed the devs.")

    @commands.slash_command(name="turnup", description="Was für Saft?", brief="Was für Saft?")
    async def _orangejuice(self, ctx):
        if str(ctx.author) != "Schnenko#9944":
            await ctx.respond("Frag nicht was für Saft, einfach Orangensaft! Tuuuuuuuurn up! Fassen Sie mich nicht an!")
        else:
            await ctx.respond("https://tenor.com/view/nerd-moneyboy-money-boy-hau-gif-16097814")
        logging.info(f"{ctx.author} turned up the orangensaft.")

    @commands.slash_command(name="ehrenmann", description="Der erwähnte User ist ein Ehrenmann!", brief="Der erwähnte User ist ein Ehrenmann!")
    async def _ehrenmann(self, ctx, user: discord.Option(discord.User, description="Wähle den ehrenhaften User", required=True)):
        await ctx.respond(f"{user.mention}, du bist ein gottverdammter Ehrenmann! <:djmaggus:1095706395355127808>")
        logging.info(f"{ctx.author} wanted to let {user.name} know he is an ehrenmann.")

    @commands.slash_command(name="lebonk", description="Don't mess with him...", brief="Don't mess with him...")
    async def _lebonk(self, ctx):
        LastMessages = await ctx.channel.history(limit=1).flatten()
        LastMessage = LastMessages[0]
        if LastMessage.author == self.bot.user:
            await ctx.respond("Das ist eine Nachricht von mir, die bonke ich nicht.", ephemeral=True)
        else:
            await ctx.defer(ephemeral=True)
            await ctx.followup.send("Die Nachricht wurde gebonkt!")
            await LastMessage.reply(f"Mess with Lechonk, you get the bonk! Du wurdest gebonkt von {ctx.author.name}!", file=discord.File("fun/LeBonk.png"))

    @commands.slash_command(name="pub", description="Typos...")
    async def _pubtypo(self, ctx):
        await ctx.respond(f"Das Discord Pub ist geschlossen, {ctx.author.name}! Du meintest wohl !pun?")

    @commands.slash_command(name="neinl", description="Sie sagte nein.")
    async def _noL(self, ctx):
        ElisabotList = [
            "frag doch einfach nochmal",
            "sie hat gerade einen kreativen Flow",
            "auch zu Lieferando",
            "denn es ist Käseabend, meine Kerl*innen",
            "denn das Arbeitszimmer ist besetzt",
            "weil die Aperolspur ist voll",
            "aber vielleicht morgen nicht mehr",
            "weil sie es kann",
            "auch wenn es keinen Grund gibt",
            "denn sie zahlt nicht umsonst Apple TV+",
            "Elisabot will wandern gehen",
            "die Bolo-Avocado ist gleich fertig",
            "denn die Bildschirmzeit ist aufgebraucht",
            "Fehler LC-208",
            "denn Elisabot hat Besuch",
            "denn er will es ja auch",
            "denn das 800€ Ticket muss genutzt werden",
            "denn Quinoa ist das neue Gyros",
            "es muss ein Innlandsflug gebucht werden",
        ]
        await ctx.respond(f"Elisabot sagt nein, {random.SystemRandom().choice(ElisabotList)}.")

    @commands.slash_command(name="nein", description="Nein.")
    async def _zuggisaysno(self, ctx: discord.ApplicationContext):
        LastMessages = await ctx.channel.history(limit=1).flatten()
        LastMessage = LastMessages[0]
        logging.info(f"{ctx.author.name} has invoked the nein command.")
        if LastMessage.author == self.bot.user:
            await ctx.respond("Das ist eine Nachricht von mir, die verneine ich nicht.", ephemeral=True)
        else:
            await LastMessage.reply("Zuggi sagt nein.")
            await ctx.respond("Nachricht wurde verneint!", ephemeral=True)

    @commands.slash_command(name="uwu", description="Weebt die Message UwU")
    async def _uwuthis(self, ctx):
        LastMessages = await ctx.channel.history(limit=1).flatten()
        if LastMessages[0].author == self.bot.user:
            await ctx.respond("Ich uwue meine Nachricht nicht!", ephemeral=True)
            return
        if LastMessages[0].content == "":
            await ctx.respond("Die Nachricht enthält keinen Text!", ephemeral=True)
            return
        flags = uwuify.SMILEY | uwuify.YU
        await ctx.respond(uwuify.uwu(LastMessages[0].content, flags=flags))
        logging.info(f"{ctx.author} hat die Nachricht [{LastMessages[0].content}] geUwUt.")

    @commands.slash_command(name="pr", description="Pullrequests einreichen zur Übername... oder so")
    async def _dont_ask(self, ctx):
        await ctx.respond("https://i.redd.it/before-t8-was-announced-harada-said-dont-ask-me-for-shit-v0-e4arzhnywrda1.jpg?width=451&format=pjpg&auto=webp&s=0ec112c803a3a927add3aad4eabafcb83a0bedec")

    @commands.slash_command(name="schnabi", description="Er malt gerne!", brief="Er malt gerne!")
    async def _schnabi(self, ctx: discord.context.ApplicationContext):
        if (waifu_data := await self.get_waifu_img()) is None:
            await ctx.respond("Heute keine Waifus für dich, fass mal Gras an :)")
            return

        embed = discord.Embed(title="Hat da jemand Waifu gesagt?", colour=discord.Colour(0xA53D8F)).set_image(url=waifu_data["url"])

        if waifu_data["name"]:
            embed.add_field(name="**Artist**", value=waifu_data["name"])
        if waifu_data["urls"]:
            embed.add_field(name="**Artist Links**", value="\n".join(waifu_data["urls"]), inline=False)

        await ctx.respond(embed=embed)

    @commands.Cog.listener("on_message")
    async def _uwumsg(self, message):
        if isinstance(message.channel, discord.channel.DMChannel):
            return
        if random.randint(0, 75) == 1 and len(message.content) > 50 and "http://" not in message.content and "https://" not in message.content:  # noqa: S311
            LastMessageContent = message.content
            flags = uwuify.SMILEY | uwuify.YU
            await message.channel.send(f"{uwuify.uwu(LastMessageContent, flags=flags)} <:UwU:870283726704242698>")
            logging.info(f"The message [{LastMessageContent}] was UwUed.")


def setup(bot):
    bot.add_cog(Fun(bot))
