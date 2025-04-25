from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

import aiohttp
import discord
from bs4 import BeautifulSoup, Tag
from dateutil import parser
from discord.ext import commands, tasks
from requests.utils import quote

logging.getLogger(name="discord").setLevel(level=logging.WARNING)
logging.basicConfig(
    format="[%(asctime)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(filename=f"./logs/{datetime.datetime.now(tz=ZoneInfo("Europe/Berlin")).date()}_bot.log"),
        logging.StreamHandler(),
    ],
    encoding="UTF-8",
)

# To show the whole table, currently unused
# pd.set_option('display.max_rows', None)  # noqa: ERA001

GUILD_ID = 337227463564328970
MUCHZEPS_CHANNEL_ID = 986763851519385690

HTTP_OK = 200

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(debug_guilds=[GUILD_ID], command_prefix=("!"), intents=intents)

        self.Settings = {}

    def reload_settings(self) -> None:
        self.Settings = _read_json("Settings.json")
        logging.info("Settings have been loaded.")

    @property
    def BannedUsers(self) -> list:
        return self.Settings["Settings"]["BannedUsers"]


bot = Bot()

### Functions ###
def _read_json(FileName: str) -> dict:
    with open(f"{FileName}", encoding="utf-8") as JsonRead:
        return json.load(JsonRead)


def _write_json(FileName: str, Content: dict | list) -> None:
    with open(f"{FileName}", "w", encoding="utf-8") as JsonWrite:
        json.dump(Content, JsonWrite, indent=4)


async def _is_banned(ctx: commands.context.Context) -> bool:
    return str(ctx.author) not in bot.BannedUsers


### Tasks Section ###
@tasks.loop(time=datetime.time(hour=17, minute=5, second=0, tzinfo=ZoneInfo("Europe/Berlin")))
async def GetFreeEpicGames() -> None:
    AllEpicFiles = next(os.walk("epic/"))[2]
    NumberOfEpicFiles = len(AllEpicFiles)
    CurrentTime = datetime.datetime.now(timezone.utc)
    EndedOffers = []

    for FreeGameEntry in bot.Settings["Settings"]["FreeEpicGames"]:
        GameEndDate = (
            parser.parse(bot.Settings["Settings"]["FreeEpicGames"][f"{FreeGameEntry}"]["endDate"])
            if bot.Settings["Settings"]["FreeEpicGames"][f"{FreeGameEntry}"]["endDate"]
            else (datetime.datetime.now(tz=ZoneInfo("Europe/Berlin")) + timedelta(days=7)).replace(hour=12)  # to make the game expire in a week
        )
        if CurrentTime > GameEndDate:
            EndedOffers.append(FreeGameEntry)

    if EndedOffers:
        for EndedOffer in EndedOffers:
            bot.Settings["Settings"]["FreeEpicGames"].pop(EndedOffer)
            logging.info(f"{EndedOffer} removed from free Epic Games, since it expired!")
            _write_json("Settings.json", bot.Settings)

    EpicStoreURL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=de&country=DE&allowCountries=DE"

    async with aiohttp.ClientSession() as EpicSession, EpicSession.get(EpicStoreURL) as RequestFromEpic:
        if RequestFromEpic.status != HTTP_OK:
            logging.error("Epic Store is not available!")
            return

        JSONFromEpicStore = await RequestFromEpic.json()

        if not JSONFromEpicStore["data"]["Catalog"]["searchStore"]["elements"]:
            return

        for FreeGame in JSONFromEpicStore["data"]["Catalog"]["searchStore"]["elements"]:
            if FreeGame["promotions"] is None or not FreeGame["promotions"]["promotionalOffers"]:
                return

            PromotionalStartDate = (
                parser.parse(FreeGame["promotions"]["promotionalOffers"][0]["promotionalOffers"][0]["startDate"])
                if FreeGame["promotions"]["promotionalOffers"][0]["promotionalOffers"][0]["startDate"]
                else parser.parse(FreeGame["promotions"]["promotionalOffers"][0]["promotionalOffers"][1]["startDate"])
            )
            LaunchingToday = parser.parse(FreeGame["effectiveDate"])

            if FreeGame["price"]["totalPrice"]["discountPrice"] == 0 and (
                LaunchingToday.date() <= datetime.datetime.now(tz=ZoneInfo("Europe/Berlin")).date() or PromotionalStartDate.date() <= datetime.datetime.now(tz=ZoneInfo("Europe/Berlin")).date()
            ):
                offers = FreeGame["promotions"]["promotionalOffers"]
                for offer in offers:
                    FreeGameObject = {
                        f"{FreeGame['title']}": {
                            "startDate": offer["promotionalOffers"][0]["startDate"],
                            "endDate": offer["promotionalOffers"][0]["endDate"],
                        }
                    }

                    try:
                        if FreeGame["title"] in bot.Settings["Settings"]["FreeEpicGames"]:
                            pass
                        else:
                            bot.Settings["Settings"]["FreeEpicGames"].update(FreeGameObject)
                            _write_json("Settings.json", bot.Settings)
                            EndOfOffer = (
                                offer["promotionalOffers"][0]["endDate"]
                                if offer["promotionalOffers"][0]["endDate"]
                                else offer["promotionalOffers"][1]["endDate"]  # Look into the second property for the EndDate
                            )
                            EndDateOfOffer = parser.parse(EndOfOffer).date()

                            for index in range(len(FreeGame["keyImages"])):
                                if FreeGame["keyImages"][index]["type"] in ["Thumbnail", "DieselStoreFrontWide", "OfferImageWide"]:
                                    EpicImageURL = FreeGame["keyImages"][index]["url"]
                                    async with EpicSession.get(EpicImageURL) as EpicImageReq:
                                        EpicImage = await EpicImageReq.read()
                                        break
                            else:
                                EpicImageURL = ""
                                EpicImage = ""

                            ### Build Embed with chosen vars ###
                            EpicEmbed = discord.Embed(
                                title=f"Neues Gratis Epic Game: {FreeGame['title']}!\r\n\nNoch einlösbar bis zum {EndDateOfOffer.day}.{EndDateOfOffer.month}.{EndDateOfOffer.year}!\r\n\n",
                                colour=discord.Colour(0x1),
                                timestamp=datetime.datetime.now(tz=ZoneInfo("Europe/Berlin")),
                            )
                            EpicEmbed.set_thumbnail(
                                url=r"https://cdn2.unrealengine.com/Epic+Games+Node%2Fxlarge_whitetext_blackback_epiclogo_504x512_1529964470588-503x512-ac795e81c54b27aaa2e196456dd307bfe4ca3ca4.jpg"
                            )
                            EpicEmbed.set_author(name="Bizeps_Bot", icon_url="https://cdn.discordapp.com/avatars/794273832508588062/9267c06d60098704f652d980caa5a43c.png")
                            if FreeGame["productSlug"]:
                                if "collection" in FreeGame["productSlug"] or "bundle" in FreeGame["productSlug"] or "trilogy" in FreeGame["productSlug"]:
                                    EpicEmbed.add_field(name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/bundles/{FreeGame['productSlug']})", inline=True)
                                    EpicEmbed.add_field(name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/bundles/{FreeGame['productSlug']}>", inline=True)
                                else:
                                    EpicEmbed.add_field(name="Besuch mich im EGS", value=f"[Epic Games Store](https://store.epicgames.com/de/p/{FreeGame['productSlug']})", inline=True)
                                    EpicEmbed.add_field(name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/p/{FreeGame['productSlug']}>", inline=True)
                            elif FreeGame["catalogNs"]["mappings"][0]["pageSlug"]:
                                if (
                                    "collection" in FreeGame["catalogNs"]["mappings"][0]["pageSlug"]
                                    or "bundle" in FreeGame["catalogNs"]["mappings"][0]["pageSlug"]
                                    or "trilogy" in FreeGame["catalogNs"]["mappings"][0]["pageSlug"]
                                ):
                                    EpicEmbed.add_field(
                                        name="Besuch mich im EGS",
                                        value=f"[Epic Games Store](https://store.epicgames.com/de/bundles/{FreeGame['catalogNs']['mappings'][0]['pageSlug']})",
                                        inline=True,
                                    )
                                    EpicEmbed.add_field(
                                        name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/bundles/{FreeGame['catalogNs']['mappings'][0]['pageSlug']}>", inline=True
                                    )
                                else:
                                    EpicEmbed.add_field(
                                        name="Besuch mich im EGS",
                                        value=f"[Epic Games Store](https://store.epicgames.com/de/p/{FreeGame['catalogNs']['mappings'][0]['pageSlug']})",
                                        inline=True,
                                    )
                                    EpicEmbed.add_field(
                                        name="Hol mich im Launcher", value=f"<com.epicgames.launcher://store/p/{FreeGame['catalogNs']['mappings'][0]['pageSlug']}>", inline=True
                                    )
                            if EpicImageURL != "":
                                EpicImageURL = quote(EpicImageURL, safe=":/")
                                EpicEmbed.set_image(url=f"{EpicImageURL}")
                            EpicEmbed.set_footer(text="Bizeps_Bot")

                            if EpicImage != "" and EpicImage:
                                NumberOfEpicFiles = NumberOfEpicFiles + 1
                                EpicImagePath = f"{NumberOfEpicFiles}_epic.jpg"
                                with open(f"epic/{EpicImagePath}", "wb") as write_file:
                                    write_file.write(EpicImage)

                            if not isinstance(
                                joschweichlp_channel := bot.get_channel(MUCHZEPS_CHANNEL_ID),
                                discord.TextChannel
                            ):
                                return

                            await joschweichlp_channel.send(embed=EpicEmbed)
                            logging.info(f"{FreeGame['title']} was added to free Epic Games!")

                    except json.decoder.JSONDecodeError:
                        logging.exception("ERROR: Something bad happend with the json decoding! The Free EpicGames list was created again!")
                        bot.Settings["Settings"]["FreeEpicGames"] = {}
                        bot.Settings["Settings"]["FreeEpicGames"].update(FreeGameObject)
                        _write_json("Settings.json", bot.Settings)


@tasks.loop(minutes=15)
async def _get_free_steamgames() -> None:
    FreeGameTitleList = []
    SteamURL = "https://store.steampowered.com/search/?maxprice=free&specials=1"

    async with aiohttp.ClientSession() as SteamSession, SteamSession.get(SteamURL) as SteamReq:
        if SteamReq.status != HTTP_OK or not (SteamPage := await SteamReq.read()):
            return

        if not (
            Results := BeautifulSoup(SteamPage, "html.parser").find_all("a", class_="search_result_row ds_collapse_flag")
        ):
            return

        for Result in Results:
            if (
                not isinstance(Result, Tag)
                or (SteamGame := Result.find(class_="title")) is None
                or not (SteamGameTitle := SteamGame.text)
            ):
                continue

            FreeGameTitleList.append(SteamGameTitle)

            if SteamGameTitle in bot.Settings["Settings"]["FreeSteamGames"]:
                continue

            SteamGameURL = Result["href"]
            ProdID = Result["data-ds-appid"]
            ImageSrc = f"https://cdn.akamai.steamstatic.com/steam/apps/{ProdID}/header.jpg"
            SteamImageURL = quote(ImageSrc, safe=":/")

            SteamEmbed = discord.Embed(
                title=f"Neues Gratis Steam Game: {SteamGameTitle}!\r\n\n",
                colour=discord.Colour(0x6C6C6C),
                timestamp=datetime.datetime.now(tz=ZoneInfo("Europe/Berlin")),
            ).set_thumbnail(
                url="https://store.cloudflare.steamstatic.com/public/images/v6/logo_steam_footer.png",
            ).set_author(
                name="Bizeps_Bot",
                icon_url="https://cdn.discordapp.com/avatars/794273832508588062/9267c06d60098704f652d980caa5a43c.png",
            ).add_field(
                name="Besuch mich auf Steam",
                value=f"{SteamGameURL}",
                inline=True,
            ).add_field(
                name="Hol mich im Launcher",
                value=f"<Steam://openurl/{SteamGameURL}>",
                inline=True,
            ).set_image(
                url=f"{SteamImageURL}",
            ).set_footer(
                text="Bizeps_Bot",
            )

            if not isinstance(
                joschweichlp_channel := bot.get_channel(MUCHZEPS_CHANNEL_ID),
                discord.TextChannel
            ):
                return

            await joschweichlp_channel.send(embed=SteamEmbed)

        bot.Settings["Settings"]["FreeSteamGames"].extend(FreeGameTitleList)
        _write_json("Settings.json", bot.Settings)

        ExpiredGames = set(bot.Settings["Settings"]["FreeSteamGames"]).difference(FreeGameTitleList)

        for ExpiredGame in ExpiredGames:
            bot.Settings["Settings"]["FreeSteamGames"].remove(ExpiredGame)

        _write_json("Settings.json", bot.Settings)


@tasks.loop(time=datetime.time(hour=19, minute=5, second=0, tzinfo=ZoneInfo("Europe/Berlin")))
async def _get_free_goggames() -> None:
    GOGURL = "https://www.gog.com/"

    async with aiohttp.ClientSession() as GOGSession:
        for _ in range(10):  # ten tries to find the giveaway HTML, this is absolutely godless but otherwise the bot is too spammy
            async with GOGSession.get(GOGURL) as GOGReq:
                if GOGReq.status != HTTP_OK:
                    break

                if (
                    not (GOGHTML := await GOGReq.read())
                    or not (GOGPage := BeautifulSoup(GOGHTML, "html.parser").find(class_="giveaway"))
                    or not isinstance(GOGPage, Tag)
                ):
                    await asyncio.sleep(360)
                    continue

                GOGGameLink = GOGPage.find("a", class_="giveaway__overlay-link")

                if not isinstance(GOGGameLink, Tag) or not GOGGameLink.has_attr("href"):
                    continue

                GOGGameURL = GOGGameLink.get("href")

                GOGGameTitle = GOGPage.find_all(
                    class_="giveaway__image",
                )[0].find_all(
                    "img", alt=True,
                )[0]["alt"].replace(" giveaway", "")

                if GOGGameTitle in bot.Settings["Settings"]["FreeGOGGames"]:
                    continue

                GOGImageURL = GOGPage.find_all(
                    class_="giveaway__image",
                )[0].find_all(
                    "source", srcset=True, type="image/jpeg",
                )[0]["srcset"].split(",")[0]

                GOGEmbed = discord.Embed(
                    title=f"Neues Gratis GOG Game: {GOGGameTitle}!\r\n\n",
                    colour=discord.Colour(0xFFFFFF),
                    timestamp=datetime.datetime.now(tz=ZoneInfo("Europe/Berlin")),
                ).set_thumbnail(
                    url=r"https://www.gog.com/blog/wp-content/uploads/2022/01/gogcomlogo-1.jpeg",
                ).set_author(
                    name="Bizeps_Bot",
                    icon_url="https://cdn.discordapp.com/avatars/794273832508588062/9267c06d60098704f652d980caa5a43c.png",
                ).add_field(
                    name="Besuch mich auf GOG", value=f"{GOGGameURL}", inline=True
                ).set_image(
                    url=f"{GOGImageURL}"
                ).set_footer(
                    text="Bizeps_Bot"
                )

                if not isinstance(
                    joschweichlp_channel := bot.get_channel(MUCHZEPS_CHANNEL_ID),
                    discord.TextChannel
                ):
                    return

                await joschweichlp_channel.send(embed=GOGEmbed)

                bot.Settings["Settings"]["FreeGOGGames"].append(GOGGameTitle)
                _write_json("Settings.json", bot.Settings)

                break

        else:
            if bot.Settings["Settings"]["FreeGOGGames"]:
                for FreeGameEntry in bot.Settings["Settings"]["FreeGOGGames"]:
                    bot.Settings["Settings"]["FreeGOGGames"].remove(FreeGameEntry)
                    logging.info(f"{FreeGameEntry} removed from free GOG Games, since it expired!")
                    _write_json("Settings.json", bot.Settings)

@bot.event
async def on_ready() -> None:
    """Startet den Bot und die Loops werden gestartet, sollten sie nicht schon laufen."""

    logging.info(f"Logged in as {bot.user}!")

    if not GetFreeEpicGames.is_running():
        GetFreeEpicGames.start()
    if not _get_free_steamgames.is_running():
        _get_free_steamgames.start()
    if not _get_free_goggames.is_running():
        _get_free_goggames.start()

    for File in os.listdir("./cogs"):
        if File.endswith(".py") and f"cogs.{File[:-3]}" not in bot.extensions and not File.startswith("management") and not File.endswith("__.py"):
            bot.load_extension(f"cogs.{File[:-3]}")
            logging.info(f"Extension {File[:-3]} loaded.")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError)  -> None:
    """ Fehlerbehandlung falls Fehler bei einem Befehl auftreten.
    Aktuell werden dort nur fehlende Befehle behandelt."""

    if isinstance(error, commands.CommandNotFound):
        logging.warning(f"{error}, {ctx.author} wants a new command.")


if __name__ == "__main__":
    bot.reload_settings()

    with open("TOKEN.json", encoding="UTF-8") as TOKENFILE:
        TOKENDATA = json.load(TOKENFILE)
        TOKEN = TOKENDATA["DISCORD_TOKEN"]
        logging.info("Token successfully loaded.")

    if "cogs.management" not in bot.extensions:
        bot.load_extension("cogs.management")
        logging.info("Extension management loaded.")

    bot.run(TOKEN)
