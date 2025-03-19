import json
import disnake
from disnake.ext import commands
from colorama import Fore, Style

class techCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Получить помощь по игре")
    async def help(self, inter: disnake.ApplicationCommandInteraction):
        """Send help embeds"""
        with open("game_rulles.json", "r", encoding="utf-8") as file:
            help_data = json.load(file)
        
        embeds = [
            disnake.Embed(
                title=embed["title"],
                description=embed["description"],
                color=embed["color"]
            )
            .set_image(url=embed["image"]["url"])
            .set_footer(text=embed["footer"]["text"])
            if "image" in embed and "footer" in embed
            else disnake.Embed(
                title=embed["title"],
                description=embed["description"],
                color=embed["color"]
            )
            for embed in help_data["embeds"]
        ]
        
        await inter.response.send_message(content=None, embeds=embeds)

def setup(bot: commands.Bot):
    bot.add_cog(techCog(bot))
    print(f'{Fore.LIGHTRED_EX}{__name__} {Fore.GREEN}+{Style.RESET_ALL}')
