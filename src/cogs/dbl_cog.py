import dbl
import discord
from discord.ext import commands


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.cfg = bot.cfg
        self.bot = bot
        self.token = self.cfg.DBLToken  # set this to your DBL token
        if self.token == "":
            pass
        self.dblpy = dbl.DBLClient(
            self.bot, self.token, autopost=True
        )  # Autopost will post your guild count every 30 minutes


def setup(bot: commands.Bot) -> None:
    bot.add_cog(TopGG(bot))
